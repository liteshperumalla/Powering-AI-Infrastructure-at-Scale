"""
Tests for Prompt Manager - Version control and A/B testing.
"""

import pytest
from datetime import datetime, timedelta
from src.infra_mind.llm.prompt_manager import (
    PromptManager,
    PromptVersion,
    PromptStatus,
    ABTest,
    ABTestResult,
    InMemoryPromptStorage,
    FilePromptStorage
)


class TestPromptVersion:
    """Test PromptVersion dataclass."""

    def test_create_prompt_version(self):
        """Test creating a prompt version."""
        prompt = PromptVersion(
            template_id="test_template",
            version="v1.abc123",
            content="Analyze {data}",
            variables=["data"],
            metadata={"agent": "test"},
            created_at=datetime.now(),
            created_by="test_user"
        )

        assert prompt.template_id == "test_template"
        assert prompt.version == "v1.abc123"
        assert "data" in prompt.variables
        assert prompt.status == PromptStatus.DRAFT
        assert prompt.total_uses == 0

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = PromptVersion(
            template_id="test",
            version="v1.0",
            content="Test {var}",
            variables=["var"],
            metadata={},
            created_at=datetime.now(),
            created_by="test"
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = PromptVersion.from_dict(data)

        assert restored.template_id == original.template_id
        assert restored.version == original.version
        assert restored.content == original.content


class TestInMemoryPromptStorage:
    """Test in-memory storage backend."""

    def test_save_and_retrieve(self):
        """Test saving and retrieving prompts."""
        storage = InMemoryPromptStorage()

        prompt = PromptVersion(
            template_id="test",
            version="v1.0",
            content="Test content",
            variables=[],
            metadata={},
            created_at=datetime.now(),
            created_by="test"
        )

        # Save
        storage.save_prompt(prompt)

        # Retrieve
        retrieved = storage.get_prompt_version("test", "v1.0")
        assert retrieved is not None
        assert retrieved.content == "Test content"

    def test_get_latest_prompt(self):
        """Test getting latest active prompt."""
        storage = InMemoryPromptStorage()

        # Create multiple versions
        for i in range(3):
            prompt = PromptVersion(
                template_id="test",
                version=f"v{i+1}.0",
                content=f"Content {i+1}",
                variables=[],
                metadata={},
                created_at=datetime.now() + timedelta(seconds=i),
                created_by="test",
                status=PromptStatus.ACTIVE if i == 2 else PromptStatus.DEPRECATED
            )
            storage.save_prompt(prompt)

        # Get latest should return v3
        latest = storage.get_latest_prompt("test")
        assert latest is not None
        assert latest.version == "v3.0"

    def test_list_versions(self):
        """Test listing all versions."""
        storage = InMemoryPromptStorage()

        # Create 3 versions
        for i in range(3):
            prompt = PromptVersion(
                template_id="test",
                version=f"v{i+1}.0",
                content=f"Content {i+1}",
                variables=[],
                metadata={},
                created_at=datetime.now(),
                created_by="test"
            )
            storage.save_prompt(prompt)

        versions = storage.list_versions("test")
        assert len(versions) == 3


class TestPromptManager:
    """Test PromptManager functionality."""

    def test_create_prompt(self):
        """Test creating a new prompt."""
        manager = PromptManager()

        prompt = manager.create_prompt(
            template_id="test_template",
            content="Analyze {data} and provide {output}",
            created_by="test_user"
        )

        assert prompt.template_id == "test_template"
        assert "data" in prompt.variables
        assert "output" in prompt.variables
        assert prompt.status == PromptStatus.DRAFT

    def test_auto_variable_detection(self):
        """Test automatic variable detection."""
        manager = PromptManager()

        prompt = manager.create_prompt(
            template_id="test",
            content="Hello {name}, you have {count} messages"
        )

        assert set(prompt.variables) == {"name", "count"}

    def test_activate_prompt(self):
        """Test activating a prompt version."""
        manager = PromptManager()

        # Create and activate
        prompt = manager.create_prompt(
            template_id="test",
            content="Test content"
        )

        activated = manager.activate_prompt("test", prompt.version)
        assert activated.status == PromptStatus.ACTIVE

    def test_get_prompt_latest(self):
        """Test getting latest active prompt."""
        manager = PromptManager()

        # Create and activate first version
        v1 = manager.create_prompt("test", "Content v1")
        manager.activate_prompt("test", v1.version)

        # Create and activate second version
        v2 = manager.create_prompt("test", "Content v2")
        manager.activate_prompt("test", v2.version)

        # Get latest should return v2
        latest = manager.get_prompt("test")
        assert latest is not None
        assert latest.version == v2.version

    def test_render_prompt(self):
        """Test rendering a prompt with variables."""
        manager = PromptManager()

        prompt = manager.create_prompt(
            template_id="greeting",
            content="Hello {name}, welcome to {place}!"
        )
        manager.activate_prompt("greeting", prompt.version)

        rendered, version = manager.render_prompt(
            "greeting",
            {"name": "Alice", "place": "Wonderland"}
        )

        assert rendered == "Hello Alice, welcome to Wonderland!"
        assert version == prompt.version

    def test_render_prompt_missing_variable(self):
        """Test rendering with missing variable raises error."""
        manager = PromptManager()

        prompt = manager.create_prompt(
            template_id="test",
            content="Hello {name}"
        )
        manager.activate_prompt("test", prompt.version)

        with pytest.raises(ValueError, match="Missing required variable"):
            manager.render_prompt("test", {})

    def test_record_prompt_result(self):
        """Test recording prompt performance metrics."""
        manager = PromptManager()

        prompt = manager.create_prompt("test", "Content")

        # Record multiple results
        for i in range(5):
            manager.record_prompt_result(
                template_id="test",
                version=prompt.version,
                quality_score=0.8 + (i * 0.01),
                response_time=1.0,
                cost=0.01,
                tokens_used=100,
                success=True
            )

        # Check metrics updated
        updated = manager.storage.get_prompt_version("test", prompt.version)
        assert updated.total_uses == 5
        assert updated.avg_quality_score > 0.8
        assert updated.success_rate == 1.0

    def test_performance_report(self):
        """Test getting performance report."""
        manager = PromptManager()

        # Create multiple versions
        v1 = manager.create_prompt("test", "Content v1")
        v2 = manager.create_prompt("test", "Content v2")

        # Record some usage
        manager.record_prompt_result(
            "test", v1.version, 0.9, 1.0, 0.01, 100, True
        )

        report = manager.get_performance_report("test")

        assert report["total_versions"] == 2
        assert len(report["versions"]) == 2


class TestABTesting:
    """Test A/B testing functionality."""

    def test_create_ab_test(self):
        """Test creating an A/B test."""
        manager = PromptManager()

        # Create two versions
        v1 = manager.create_prompt("test", "Content A")
        v2 = manager.create_prompt("test", "Content B")

        # Start A/B test
        experiment_id = manager.start_ab_test(
            template_id="test",
            variant_a_version=v1.version,
            variant_b_version=v2.version,
            traffic_split=0.5
        )

        assert experiment_id is not None
        assert "test" in manager.active_experiments

    def test_ab_test_variant_assignment(self):
        """Test deterministic variant assignment."""
        manager = PromptManager()

        v1 = manager.create_prompt("test", "Content A")
        v2 = manager.create_prompt("test", "Content B")

        manager.start_ab_test("test", v1.version, v2.version, traffic_split=0.5)

        # Same key should always get same variant
        variant1 = manager.get_prompt("test", ab_test_key="user_123")
        variant2 = manager.get_prompt("test", ab_test_key="user_123")

        assert variant1.version == variant2.version

    def test_ab_test_traffic_split(self):
        """Test traffic split distribution."""
        manager = PromptManager()

        v1 = manager.create_prompt("test", "Content A")
        v2 = manager.create_prompt("test", "Content B")

        # 30% to variant B
        manager.start_ab_test("test", v1.version, v2.version, traffic_split=0.3)

        # Test with many keys
        variant_b_count = 0
        total_count = 1000

        for i in range(total_count):
            variant = manager.get_prompt("test", ab_test_key=f"user_{i}")
            if variant.version == v2.version:
                variant_b_count += 1

        # Should be approximately 30% (allow 5% margin)
        ratio = variant_b_count / total_count
        assert 0.25 < ratio < 0.35

    def test_ab_test_record_results(self):
        """Test recording results for A/B test."""
        manager = PromptManager()

        v1 = manager.create_prompt("test", "Content A")
        v2 = manager.create_prompt("test", "Content B")

        manager.start_ab_test("test", v1.version, v2.version)
        experiment = manager.active_experiments["test"]

        # Record results for both variants
        for i in range(50):
            # Variant A: quality 0.8
            manager.record_prompt_result(
                "test", v1.version, 0.8, 1.0, 0.01, 100, True
            )

            # Variant B: quality 0.9 (better)
            manager.record_prompt_result(
                "test", v2.version, 0.9, 1.0, 0.01, 100, True
            )

        # Check results
        assert len(experiment.variant_a_results) == 50
        assert len(experiment.variant_b_results) == 50

    def test_ab_test_statistical_analysis(self):
        """Test statistical significance testing."""
        manager = PromptManager()

        v1 = manager.create_prompt("test", "Content A")
        v2 = manager.create_prompt("test", "Content B")

        manager.start_ab_test("test", v1.version, v2.version)

        # Record significantly different results
        for i in range(50):
            manager.record_prompt_result(
                "test", v1.version, 0.7, 1.0, 0.01, 100, True
            )
            manager.record_prompt_result(
                "test", v2.version, 0.95, 1.0, 0.01, 100, True
            )

        # Get results
        result = manager.get_ab_test_results("test", min_samples=30)

        assert result is not None
        assert result.is_significant
        assert result.winner == v2.version
        assert result.improvement_percentage > 0

    def test_end_ab_test_activate_winner(self):
        """Test ending A/B test and activating winner."""
        manager = PromptManager()

        v1 = manager.create_prompt("test", "Content A")
        v2 = manager.create_prompt("test", "Content B")

        manager.start_ab_test("test", v1.version, v2.version)

        # Record results with clear winner (v2)
        for i in range(50):
            manager.record_prompt_result(
                "test", v1.version, 0.6, 1.0, 0.01, 100, True
            )
            manager.record_prompt_result(
                "test", v2.version, 0.95, 1.0, 0.01, 100, True
            )

        # End test and activate winner
        winner = manager.end_ab_test("test", activate_winner=True)

        assert winner == v2.version

        # Verify v2 is now active
        active = manager.get_prompt("test")
        assert active.version == v2.version
        assert active.status == PromptStatus.ACTIVE

    def test_ab_test_insufficient_samples(self):
        """Test A/B test with insufficient samples."""
        manager = PromptManager()

        v1 = manager.create_prompt("test", "Content A")
        v2 = manager.create_prompt("test", "Content B")

        manager.start_ab_test("test", v1.version, v2.version)

        # Record only 10 results (need 30)
        for i in range(10):
            manager.record_prompt_result(
                "test", v1.version, 0.8, 1.0, 0.01, 100, True
            )

        result = manager.get_ab_test_results("test", min_samples=30)
        assert result is None


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_prompt_evolution_workflow(self):
        """Test complete prompt evolution workflow."""
        manager = PromptManager()

        # 1. Create initial prompt
        v1 = manager.create_prompt(
            template_id="cto_analysis",
            content="Analyze {requirements} for business impact",
            metadata={"agent": "cto", "purpose": "strategic_analysis"}
        )
        manager.activate_prompt("cto_analysis", v1.version)

        # 2. Use it and collect metrics
        for i in range(20):
            rendered, version = manager.render_prompt(
                "cto_analysis",
                {"requirements": "test data"}
            )
            manager.record_prompt_result(
                "cto_analysis", version, 0.75, 1.5, 0.02, 150, True
            )

        # 3. Create improved version
        v2 = manager.create_prompt(
            template_id="cto_analysis",
            content="As a CTO, provide detailed analysis of {requirements} focusing on ROI and strategic alignment",
            metadata={"agent": "cto", "purpose": "strategic_analysis", "improvement": "more specific"}
        )

        # 4. A/B test new version
        manager.start_ab_test(
            "cto_analysis",
            v1.version,
            v2.version,
            traffic_split=0.5,
            test_name="Specificity improvement test"
        )

        # 5. Collect results for A/B test
        for i in range(50):
            # Simulate variant assignment and results
            key = f"user_{i}"
            variant = manager.get_prompt("cto_analysis", ab_test_key=key)

            # v2 performs better
            quality = 0.8 if variant.version == v1.version else 0.92

            manager.record_prompt_result(
                "cto_analysis", variant.version, quality, 1.5, 0.02, 150, True
            )

        # Ensure we have enough samples for statistical analysis
        experiment = manager.active_experiments["cto_analysis"]
        while len(experiment.variant_a_results) < 30 or len(experiment.variant_b_results) < 30:
            experiment.record_result(v1.version, 0.8, 1.5, 0.02, True)
            experiment.record_result(v2.version, 0.92, 1.5, 0.02, True)

        # 6. Check results and decide
        results = manager.get_ab_test_results("cto_analysis")
        assert results is not None
        assert results.is_significant
        assert results.winner == v2.version

        # 7. Activate winner
        winner = manager.end_ab_test("cto_analysis", activate_winner=True)
        assert winner == v2.version

        # 8. Verify new version is active
        active = manager.get_prompt("cto_analysis")
        assert active.version == v2.version

        # 9. Get performance report
        report = manager.get_performance_report("cto_analysis")
        assert report["total_versions"] == 2
        assert report["active_version"]["version"] == v2.version


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
