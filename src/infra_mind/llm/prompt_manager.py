"""
Prompt Manager - Centralized prompt template management with versioning and A/B testing.

Provides comprehensive prompt lifecycle management including:
- Version control for prompt templates
- A/B testing framework with statistical analysis
- Performance tracking and comparison
- Rollback capabilities
- Audit trail for all prompt changes
"""

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import re

logger = logging.getLogger(__name__)


class PromptStatus(str, Enum):
    """Status of a prompt version."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class PromptVersion:
    """Represents a versioned prompt template."""
    template_id: str
    version: str
    content: str
    variables: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    created_by: str
    status: PromptStatus = PromptStatus.DRAFT

    # Performance metrics (updated over time)
    total_uses: int = 0
    avg_quality_score: float = 0.0
    avg_response_time: float = 0.0
    avg_cost: float = 0.0
    success_rate: float = 0.0
    total_tokens_used: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptVersion':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['status'] = PromptStatus(data['status'])
        return cls(**data)


@dataclass
class ABTestResult:
    """Result of A/B test comparison."""
    variant_a_version: str
    variant_b_version: str
    variant_a_samples: int
    variant_b_samples: int
    variant_a_avg_quality: float
    variant_b_avg_quality: float
    improvement_percentage: float
    is_significant: bool
    p_value: float
    winner: Optional[str]
    confidence_level: float


@dataclass
class ABTest:
    """A/B test between two prompt variants."""
    experiment_id: str
    template_id: str
    variant_a: PromptVersion
    variant_b: PromptVersion
    traffic_split: float  # Percentage to variant B (0.0-1.0)
    test_name: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime] = None
    is_active: bool = True

    # Results tracking
    variant_a_results: List[float] = field(default_factory=list)
    variant_b_results: List[float] = field(default_factory=list)
    variant_a_costs: List[float] = field(default_factory=list)
    variant_b_costs: List[float] = field(default_factory=list)
    variant_a_response_times: List[float] = field(default_factory=list)
    variant_b_response_times: List[float] = field(default_factory=list)

    def get_variant(self, key: str) -> PromptVersion:
        """
        Deterministically assign variant based on key.

        Args:
            key: Unique key for consistent assignment (user_id, request_id, etc.)

        Returns:
            PromptVersion to use
        """
        # Use hash for deterministic assignment
        hash_val = int(hashlib.md5(key.encode()).hexdigest(), 16)
        normalized = (hash_val % 10000) / 10000.0

        return self.variant_b if normalized < self.traffic_split else self.variant_a

    def record_result(
        self,
        version: str,
        quality_score: float,
        cost: float,
        response_time: float,
        success: bool
    ):
        """
        Record result for A/B test.

        Args:
            version: Version that was used
            quality_score: Quality score (0.0-1.0)
            cost: Cost in USD
            response_time: Response time in seconds
            success: Whether request was successful
        """
        # Only record successful results for quality comparison
        quality = quality_score if success else 0.0

        if version == self.variant_a.version:
            self.variant_a_results.append(quality)
            self.variant_a_costs.append(cost)
            self.variant_a_response_times.append(response_time)
        elif version == self.variant_b.version:
            self.variant_b_results.append(quality)
            self.variant_b_costs.append(cost)
            self.variant_b_response_times.append(response_time)
        else:
            logger.warning(f"Unknown version {version} in A/B test {self.experiment_id}")

    def get_results(self, min_samples: int = 30) -> Optional[ABTestResult]:
        """
        Get A/B test results with statistical analysis.

        Args:
            min_samples: Minimum samples required for statistical significance

        Returns:
            ABTestResult if enough samples, None otherwise
        """
        if (len(self.variant_a_results) < min_samples or
            len(self.variant_b_results) < min_samples):
            return None

        # Calculate averages
        avg_a = sum(self.variant_a_results) / len(self.variant_a_results)
        avg_b = sum(self.variant_b_results) / len(self.variant_b_results)

        # Calculate improvement
        improvement = ((avg_b - avg_a) / avg_a * 100) if avg_a > 0 else 0

        # Perform statistical test (t-test)
        is_significant, p_value = self._perform_statistical_test(
            self.variant_a_results,
            self.variant_b_results
        )

        # Determine winner
        winner = None
        if is_significant:
            winner = self.variant_b.version if avg_b > avg_a else self.variant_a.version

        # Calculate confidence level
        confidence_level = (1 - p_value) * 100 if p_value < 1.0 else 0

        return ABTestResult(
            variant_a_version=self.variant_a.version,
            variant_b_version=self.variant_b.version,
            variant_a_samples=len(self.variant_a_results),
            variant_b_samples=len(self.variant_b_results),
            variant_a_avg_quality=avg_a,
            variant_b_avg_quality=avg_b,
            improvement_percentage=improvement,
            is_significant=is_significant,
            p_value=p_value,
            winner=winner,
            confidence_level=confidence_level
        )

    def _perform_statistical_test(
        self,
        sample_a: List[float],
        sample_b: List[float],
        alpha: float = 0.05
    ) -> tuple[bool, float]:
        """
        Perform statistical significance test.

        Args:
            sample_a: Sample data for variant A
            sample_b: Sample data for variant B
            alpha: Significance level (default 0.05 = 95% confidence)

        Returns:
            Tuple of (is_significant, p_value)
        """
        try:
            from scipy import stats

            # Perform Welch's t-test (doesn't assume equal variance)
            t_stat, p_value = stats.ttest_ind(sample_a, sample_b, equal_var=False)

            is_significant = p_value < alpha

            return is_significant, p_value

        except ImportError:
            logger.warning("scipy not available, using simple comparison")
            # Fallback: simple comparison if scipy not available
            avg_a = sum(sample_a) / len(sample_a)
            avg_b = sum(sample_b) / len(sample_b)

            # Simple threshold: >10% improvement = significant
            improvement = abs((avg_b - avg_a) / avg_a) if avg_a > 0 else 0
            is_significant = improvement > 0.10

            return is_significant, 0.5  # Conservative p-value


class PromptStorage:
    """Abstract base class for prompt storage backends."""

    def save_prompt(self, prompt: PromptVersion) -> None:
        """Save prompt version."""
        raise NotImplementedError

    def get_prompt_version(self, template_id: str, version: str) -> Optional[PromptVersion]:
        """Get specific prompt version."""
        raise NotImplementedError

    def get_latest_prompt(self, template_id: str) -> Optional[PromptVersion]:
        """Get latest active prompt version."""
        raise NotImplementedError

    def list_versions(self, template_id: str) -> List[PromptVersion]:
        """List all versions of a template."""
        raise NotImplementedError

    def update_prompt(self, prompt: PromptVersion) -> None:
        """Update prompt version (for metrics)."""
        raise NotImplementedError


class InMemoryPromptStorage(PromptStorage):
    """In-memory storage for prompt templates (for development/testing)."""

    def __init__(self):
        self.prompts: Dict[str, Dict[str, PromptVersion]] = {}

    def save_prompt(self, prompt: PromptVersion) -> None:
        """Save prompt version to memory."""
        if prompt.template_id not in self.prompts:
            self.prompts[prompt.template_id] = {}

        self.prompts[prompt.template_id][prompt.version] = prompt
        logger.debug(f"Saved prompt {prompt.template_id} v{prompt.version} to memory")

    def get_prompt_version(self, template_id: str, version: str) -> Optional[PromptVersion]:
        """Get specific prompt version from memory."""
        return self.prompts.get(template_id, {}).get(version)

    def get_latest_prompt(self, template_id: str) -> Optional[PromptVersion]:
        """Get latest active prompt version."""
        versions = self.prompts.get(template_id, {})
        if not versions:
            return None

        # Get all active versions
        active_versions = [v for v in versions.values() if v.status == PromptStatus.ACTIVE]

        if not active_versions:
            return None

        # Return most recently created
        return max(active_versions, key=lambda v: v.created_at)

    def list_versions(self, template_id: str) -> List[PromptVersion]:
        """List all versions of a template."""
        return list(self.prompts.get(template_id, {}).values())

    def update_prompt(self, prompt: PromptVersion) -> None:
        """Update prompt version in memory."""
        if prompt.template_id in self.prompts:
            self.prompts[prompt.template_id][prompt.version] = prompt


class FilePromptStorage(PromptStorage):
    """File-based storage for prompt templates (for production)."""

    def __init__(self, base_path: str = "./data/prompts"):
        import os
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _get_file_path(self, template_id: str, version: str) -> str:
        """Get file path for prompt version."""
        import os
        return os.path.join(self.base_path, f"{template_id}_{version}.json")

    def save_prompt(self, prompt: PromptVersion) -> None:
        """Save prompt version to file."""
        file_path = self._get_file_path(prompt.template_id, prompt.version)

        with open(file_path, 'w') as f:
            json.dump(prompt.to_dict(), f, indent=2)

        logger.debug(f"Saved prompt {prompt.template_id} v{prompt.version} to {file_path}")

    def get_prompt_version(self, template_id: str, version: str) -> Optional[PromptVersion]:
        """Get specific prompt version from file."""
        import os
        file_path = self._get_file_path(template_id, version)

        if not os.path.exists(file_path):
            return None

        with open(file_path, 'r') as f:
            data = json.load(f)

        return PromptVersion.from_dict(data)

    def get_latest_prompt(self, template_id: str) -> Optional[PromptVersion]:
        """Get latest active prompt version."""
        versions = self.list_versions(template_id)
        active_versions = [v for v in versions if v.status == PromptStatus.ACTIVE]

        if not active_versions:
            return None

        return max(active_versions, key=lambda v: v.created_at)

    def list_versions(self, template_id: str) -> List[PromptVersion]:
        """List all versions of a template."""
        import os
        versions = []

        for filename in os.listdir(self.base_path):
            if filename.startswith(f"{template_id}_") and filename.endswith(".json"):
                with open(os.path.join(self.base_path, filename), 'r') as f:
                    data = json.load(f)
                    versions.append(PromptVersion.from_dict(data))

        return versions

    def update_prompt(self, prompt: PromptVersion) -> None:
        """Update prompt version in file."""
        self.save_prompt(prompt)


class PromptManager:
    """
    Centralized prompt template management with versioning and A/B testing.

    Features:
    - Version control for all prompt templates
    - A/B testing with statistical analysis
    - Performance tracking per version
    - Automatic rollback on quality degradation
    - Audit trail for all changes
    """

    def __init__(self, storage_backend: Optional[PromptStorage] = None):
        """
        Initialize prompt manager.

        Args:
            storage_backend: Storage backend for prompts (defaults to in-memory)
        """
        self.storage = storage_backend or InMemoryPromptStorage()
        self.active_experiments: Dict[str, ABTest] = {}
        self.version_cache: Dict[str, PromptVersion] = {}  # Cache for performance

        logger.info(f"PromptManager initialized with {type(self.storage).__name__}")

    def create_prompt(
        self,
        template_id: str,
        content: str,
        variables: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: str = "system"
    ) -> PromptVersion:
        """
        Create a new prompt template version.

        Args:
            template_id: Unique identifier (e.g., "cto_strategic_analysis")
            content: Prompt template with {variable} placeholders
            variables: List of variable names (auto-detected if None)
            metadata: Additional metadata (agent, category, model, etc.)
            created_by: Creator identifier

        Returns:
            PromptVersion object
        """
        # Auto-detect variables if not provided
        if variables is None:
            variables = self._extract_variables(content)

        # Generate version hash from content
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]

        # Check if this exact content already exists
        existing_versions = self.storage.list_versions(template_id)
        for existing in existing_versions:
            if hashlib.sha256(existing.content.encode()).hexdigest()[:8] == content_hash:
                logger.info(f"Prompt content unchanged, returning existing version {existing.version}")
                return existing

        # Generate version number
        version_num = len(existing_versions) + 1
        version = f"v{version_num}.{content_hash}"

        prompt = PromptVersion(
            template_id=template_id,
            version=version,
            content=content,
            variables=variables,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            status=PromptStatus.DRAFT
        )

        self.storage.save_prompt(prompt)
        logger.info(f"Created prompt {template_id} {version}")

        return prompt

    def activate_prompt(self, template_id: str, version: str) -> PromptVersion:
        """
        Activate a prompt version (make it the live version).

        Args:
            template_id: Template identifier
            version: Version to activate

        Returns:
            Activated prompt version

        Raises:
            ValueError: If version not found
        """
        prompt = self.storage.get_prompt_version(template_id, version)
        if not prompt:
            raise ValueError(f"Prompt {template_id} {version} not found")

        # Deactivate all other versions
        for other_version in self.storage.list_versions(template_id):
            if other_version.version != version and other_version.status == PromptStatus.ACTIVE:
                other_version.status = PromptStatus.DEPRECATED
                self.storage.update_prompt(other_version)

        # Activate this version
        prompt.status = PromptStatus.ACTIVE
        self.storage.update_prompt(prompt)

        # Clear cache
        self.version_cache.pop(template_id, None)

        logger.info(f"Activated prompt {template_id} {version}")
        return prompt

    def get_prompt(
        self,
        template_id: str,
        version: Optional[str] = None,
        ab_test_key: Optional[str] = None
    ) -> Optional[PromptVersion]:
        """
        Retrieve prompt template with optional A/B testing.

        Args:
            template_id: Prompt template identifier
            version: Specific version (None = latest active)
            ab_test_key: A/B test key for variant selection

        Returns:
            PromptVersion to use, or None if not found
        """
        # Check if there's an active A/B test
        if ab_test_key and template_id in self.active_experiments:
            experiment = self.active_experiments[template_id]
            if experiment.is_active:
                return experiment.get_variant(ab_test_key)

        # Get specific version or latest
        if version:
            return self.storage.get_prompt_version(template_id, version)

        # Check cache first
        if template_id in self.version_cache:
            return self.version_cache[template_id]

        # Get latest from storage
        latest = self.storage.get_latest_prompt(template_id)
        if latest:
            self.version_cache[template_id] = latest

        return latest

    def render_prompt(
        self,
        template_id: str,
        variables: Dict[str, Any],
        version: Optional[str] = None,
        ab_test_key: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Render prompt template with variables.

        Args:
            template_id: Prompt template identifier
            variables: Variables to substitute
            version: Specific version to use
            ab_test_key: A/B test key for variant selection

        Returns:
            Tuple of (rendered_prompt, version_used)

        Raises:
            ValueError: If template not found or missing variables
        """
        prompt = self.get_prompt(template_id, version, ab_test_key)
        if not prompt:
            raise ValueError(f"Prompt template '{template_id}' not found")

        try:
            rendered = prompt.content.format(**variables)
            return rendered, prompt.version

        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(
                f"Missing required variable '{missing_var}' for prompt '{template_id}'. "
                f"Required: {prompt.variables}"
            )

    def start_ab_test(
        self,
        template_id: str,
        variant_a_version: str,
        variant_b_version: str,
        traffic_split: float = 0.5,
        test_name: Optional[str] = None
    ) -> str:
        """
        Start A/B test between two prompt versions.

        Args:
            template_id: Prompt template to test
            variant_a_version: Control version
            variant_b_version: Test version
            traffic_split: Percentage of traffic to variant B (0.0-1.0)
            test_name: Optional name for the test

        Returns:
            Experiment ID

        Raises:
            ValueError: If versions not found or test already active
        """
        if template_id in self.active_experiments:
            raise ValueError(f"A/B test already active for {template_id}")

        variant_a = self.storage.get_prompt_version(template_id, variant_a_version)
        variant_b = self.storage.get_prompt_version(template_id, variant_b_version)

        if not variant_a or not variant_b:
            raise ValueError("One or both variants not found")

        experiment = ABTest(
            experiment_id=str(uuid.uuid4()),
            template_id=template_id,
            variant_a=variant_a,
            variant_b=variant_b,
            traffic_split=traffic_split,
            test_name=test_name,
            started_at=datetime.now(timezone.utc)
        )

        self.active_experiments[template_id] = experiment

        logger.info(
            f"Started A/B test for {template_id}: "
            f"{variant_a_version} vs {variant_b_version} "
            f"(split: {traffic_split*100}%)"
        )

        return experiment.experiment_id

    def record_prompt_result(
        self,
        template_id: str,
        version: str,
        quality_score: float,
        response_time: float,
        cost: float,
        tokens_used: int,
        success: bool
    ):
        """
        Record performance metrics for a prompt usage.

        Args:
            template_id: Template identifier
            version: Version used
            quality_score: Quality score (0.0-1.0)
            response_time: Response time in seconds
            cost: Cost in USD
            tokens_used: Number of tokens used
            success: Whether request was successful
        """
        # Update prompt version metrics
        prompt = self.storage.get_prompt_version(template_id, version)
        if not prompt:
            logger.warning(f"Prompt {template_id} {version} not found for metrics update")
            return

        # Update running averages
        n = prompt.total_uses
        prompt.avg_quality_score = (prompt.avg_quality_score * n + quality_score) / (n + 1)
        prompt.avg_response_time = (prompt.avg_response_time * n + response_time) / (n + 1)
        prompt.avg_cost = (prompt.avg_cost * n + cost) / (n + 1)
        prompt.success_rate = (prompt.success_rate * n + (1 if success else 0)) / (n + 1)
        prompt.total_uses += 1
        prompt.total_tokens_used += tokens_used

        self.storage.update_prompt(prompt)

        # Update A/B test if active
        if template_id in self.active_experiments:
            experiment = self.active_experiments[template_id]
            experiment.record_result(version, quality_score, cost, response_time, success)

        logger.debug(f"Recorded metrics for {template_id} {version}")

    def get_ab_test_results(self, template_id: str, min_samples: int = 30) -> Optional[ABTestResult]:
        """
        Get A/B test results with statistical analysis.

        Args:
            template_id: Template being tested
            min_samples: Minimum samples for statistical significance

        Returns:
            ABTestResult if test active and has enough samples, None otherwise
        """
        if template_id not in self.active_experiments:
            return None

        experiment = self.active_experiments[template_id]
        return experiment.get_results(min_samples)

    def end_ab_test(self, template_id: str, activate_winner: bool = True) -> Optional[str]:
        """
        End A/B test and optionally activate winner.

        Args:
            template_id: Template being tested
            activate_winner: Whether to activate the winning version

        Returns:
            Winner version if found, None otherwise
        """
        if template_id not in self.active_experiments:
            return None

        experiment = self.active_experiments[template_id]
        result = experiment.get_results()

        if result and result.winner and activate_winner:
            self.activate_prompt(template_id, result.winner)
            logger.info(f"A/B test ended, activated winner: {result.winner}")

        experiment.is_active = False
        experiment.ended_at = datetime.now(timezone.utc)

        logger.info(f"Ended A/B test for {template_id}")

        return result.winner if result else None

    def get_performance_report(self, template_id: str) -> Dict[str, Any]:
        """
        Get performance report for all versions of a template.

        Args:
            template_id: Template identifier

        Returns:
            Performance report dictionary
        """
        versions = self.storage.list_versions(template_id)

        if not versions:
            return {"error": "Template not found"}

        # Sort by creation date (newest first)
        versions.sort(key=lambda v: v.created_at, reverse=True)

        report = {
            "template_id": template_id,
            "total_versions": len(versions),
            "active_version": None,
            "versions": []
        }

        for v in versions:
            version_data = {
                "version": v.version,
                "status": v.status.value,
                "created_at": v.created_at.isoformat(),
                "total_uses": v.total_uses,
                "avg_quality_score": round(v.avg_quality_score, 3),
                "avg_response_time": round(v.avg_response_time, 3),
                "avg_cost": round(v.avg_cost, 6),
                "success_rate": round(v.success_rate, 3),
                "total_tokens_used": v.total_tokens_used
            }

            report["versions"].append(version_data)

            if v.status == PromptStatus.ACTIVE:
                report["active_version"] = version_data

        return report

    def _extract_variables(self, content: str) -> List[str]:
        """
        Extract variable names from prompt template.

        Args:
            content: Prompt template content

        Returns:
            List of variable names
        """
        # Find all {variable} patterns
        pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        variables = re.findall(pattern, content)

        return list(set(variables))  # Remove duplicates
