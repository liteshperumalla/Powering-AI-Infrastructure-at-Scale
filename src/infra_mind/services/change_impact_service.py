"""
Resource inventory and change impact analysis derived from a user's assessments.

There is no live cloud inventory to query, so the "resources" are the services
recommended for the user's assessments (their planned architecture). Dependencies
between them are inferred from resource types, and impact analysis is rule-based
over that graph. Values the data can't support (e.g. downtime cost, which needs
revenue data) are reported as 0 rather than invented.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set

# Recommendation category -> resource type
CATEGORY_TYPES = {
    "compute": "compute",
    "infrastructure": "compute",
    "storage": "storage",
    "database": "database",
    "data": "database",
    "networking": "networking",
    "network": "networking",
    "ai_ml": "ai_ml",
    "ml": "ai_ml",
    "mlops": "ai_ml",
    "security": "security",
    "monitoring": "monitoring",
}

# What each resource type depends on (within the same assessment's architecture)
DEPENDS_ON = {
    "compute": {"database", "storage"},
    "ai_ml": {"compute", "storage", "database"},
    "networking": {"compute"},
    "monitoring": {"compute", "database"},
    "security": {"compute", "networking"},
}

# Types on the request path: a change here can affect end users
RUNTIME_TYPES = {"compute", "database", "networking", "ai_ml"}
DATA_TYPES = {"database", "storage"}

ACTION_BASE_RISK = {"create": 20, "update": 40, "replace": 60, "delete": 75}
ENVIRONMENT_FACTOR = {"dev": 0.6, "staging": 1.0, "prod": 1.3}
TYPE_FACTOR = {"database": 1.3, "networking": 1.2, "compute": 1.1, "storage": 1.0}
ACTION_DURATION = {
    "create": "1-2 hours",
    "update": "30-60 minutes",
    "replace": "2-4 hours",
    "delete": "about 1 hour",
}
PROVIDERS = {"aws", "azure", "gcp", "kubernetes"}


@dataclass
class InventoryResource:
    id: str
    name: str
    type: str
    provider: str
    region: Optional[str]
    monthly_cost: float
    assessment_id: str
    assessment_title: str
    recommendation_id: str
    from_llm_services: bool
    depends_on: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)

    def to_api(self, environment: str) -> Dict[str, Any]:
        """Shape expected by the frontend's `Resource` type."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "provider": self.provider,
            "region": self.region,
            "environment": environment,
            "tags": {"assessment": self.assessment_title},
            "properties": {
                "source": "assessment_recommendation",
                "assessment_id": self.assessment_id,
                "recommendation_id": self.recommendation_id,
            },
            "dependencies": {"depends_on": list(self.depends_on), "dependents": list(self.dependents)},
            "cost_info": {"monthly_cost": self.monthly_cost, "currency": "USD"},
            "created_at": "",
            "last_modified": "",
        }


def _resource_id(recommendation_id: str, index: int) -> str:
    digest = hashlib.sha1(f"{recommendation_id}:{index}".encode()).hexdigest()[:12]
    return f"res_{digest}"


def _to_float(value: Any) -> float:
    try:
        return round(float(str(value).replace(",", "").replace("$", "")), 2)
    except (TypeError, ValueError):
        return 0.0


def _clean_title(title: str) -> str:
    return re.sub(r"\s*\[[^\]]*\]\s*$", "", title or "").strip() or "Unnamed resource"


def _assessment_provider(assessment: Dict[str, Any]) -> str:
    technical = assessment.get("technical_requirements") or {}
    for key in ("preferred_cloud_providers", "current_cloud_providers"):
        for provider in technical.get(key) or []:
            p = str(provider).strip().lower()
            if p in PROVIDERS:
                return p
    return "aws"


def _assessment_region(assessment: Dict[str, Any]) -> Optional[str]:
    regions = (assessment.get("business_requirements") or {}).get("geographic_regions") or []
    return str(regions[0]) if regions else None


def build_inventory(
    assessments: Iterable[Dict[str, Any]],
    recommendations: Iterable[Dict[str, Any]],
    provider_filter: Optional[str] = None,
) -> List[InventoryResource]:
    """Turn recommendations into de-duplicated resources with an inferred dependency graph."""
    by_assessment = {str(a["_id"]): a for a in assessments}
    resources: List[InventoryResource] = []
    seen: Set[tuple] = set()

    for rec in recommendations:
        assessment = by_assessment.get(str(rec.get("assessment_id")))
        if assessment is None:
            continue
        rec_id = str(rec.get("_id"))
        default_provider = _assessment_provider(assessment)
        region = _assessment_region(assessment)
        services = rec.get("recommended_services") or []
        # Use concrete services when the LLM produced them; otherwise one resource per recommendation
        entries = [
            {
                "name": s.get("service_name") or _clean_title(rec.get("title", "")),
                "category": s.get("service_category") or rec.get("category"),
                "provider": str(s.get("provider") or default_provider).lower(),
                "cost": s.get("estimated_monthly_cost"),
            }
            for s in services
        ] or [{
            "name": _clean_title(rec.get("title", "")),
            "category": rec.get("category"),
            "provider": default_provider,
            "cost": rec.get("total_estimated_monthly_cost"),
        }]

        for index, entry in enumerate(entries):
            rtype = CATEGORY_TYPES.get(str(entry["category"] or "").lower())
            if rtype is None:
                continue  # strategy/general recommendations aren't infrastructure resources
            provider = entry["provider"] if entry["provider"] in PROVIDERS else default_provider
            key = (str(assessment["_id"]), rtype, provider, entry["name"].lower())
            if key in seen:
                continue
            seen.add(key)
            resources.append(InventoryResource(
                id=_resource_id(rec_id, index),
                name=entry["name"],
                type=rtype,
                provider=provider,
                region=region,
                monthly_cost=_to_float(entry["cost"]),
                assessment_id=str(assessment["_id"]),
                assessment_title=assessment.get("title") or "Assessment",
                recommendation_id=rec_id,
                from_llm_services=bool(services),
            ))

    # Infer edges within each assessment's architecture
    for resource in resources:
        wanted = DEPENDS_ON.get(resource.type, set())
        for other in resources:
            if other is not resource and other.assessment_id == resource.assessment_id and other.type in wanted:
                resource.depends_on.append(other.id)
                other.dependents.append(resource.id)

    if provider_filter:
        resources = [r for r in resources if r.provider == provider_filter.lower()]
    return resources


def _walk(start: Iterable[str], index: Dict[str, InventoryResource], attr: str, depth: int) -> List[str]:
    """Breadth-first walk along `depends_on` or `dependents`, excluding the start set."""
    start = list(start)
    visited, frontier = set(start), list(start)
    found: List[str] = []
    for _ in range(max(depth, 0)):
        nxt = []
        for rid in frontier:
            for neighbour in getattr(index[rid], attr):
                if neighbour not in visited and neighbour in index:
                    visited.add(neighbour)
                    found.append(neighbour)
                    nxt.append(neighbour)
        frontier = nxt
    return found


def dependency_view(resource_id: str, inventory: List[InventoryResource], depth: int, environment: str) -> Dict[str, Any]:
    index = {r.id: r for r in inventory}
    upstream = _walk([resource_id], index, "depends_on", depth)
    downstream = _walk([resource_id], index, "dependents", depth)
    nodes = [resource_id, *upstream, *downstream]
    return {
        "upstream": [index[r].to_api(environment) for r in upstream],
        "downstream": [index[r].to_api(environment) for r in downstream],
        "dependency_graph": {
            "nodes": [{"id": n, "name": index[n].name, "type": index[n].type} for n in nodes],
            "edges": [
                {"from": n, "to": d}
                for n in nodes for d in index[n].depends_on if d in nodes
            ],
        },
    }


def _risk_level(score: int) -> str:
    if score < 30:
        return "low"
    if score < 55:
        return "medium"
    if score < 80:
        return "high"
    return "critical"


def analyze_change(
    change_request: Dict[str, Any],
    inventory: List[InventoryResource],
    assessments: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Rule-based impact analysis for a change to one or more inventory resources."""
    index = {r.id: r for r in inventory}
    action = str(change_request.get("change_type") or "update").lower()
    if action not in ACTION_BASE_RISK:
        action = "update"
    environment = str(change_request.get("target_environment") or "dev").lower()
    env_factor = ENVIRONMENT_FACTOR.get(environment, 1.0)
    is_prod = environment == "prod"

    target_ids = [c.get("resource_id") for c in change_request.get("resources") or []]
    targets = [index[t] for t in target_ids if t in index]
    indirect_ids = _walk([t.id for t in targets], index, "dependents", depth=2)
    indirect = [index[i] for i in indirect_ids]
    upstream_ids = _walk([t.id for t in targets], index, "depends_on", depth=1)

    type_factor = max((TYPE_FACTOR.get(t.type, 0.9) for t in targets), default=1.0)
    score = ACTION_BASE_RISK[action] * env_factor * type_factor + min(5 * len(indirect), 15)
    score = int(max(0, min(100, round(score))))
    level = _risk_level(score)

    severity_for_target = {"create": "low", "update": "medium", "replace": "high", "delete": "high"}[action]
    if is_prod and severity_for_target == "high":
        severity_for_target = "critical"
    downtime = {"create": "none", "update": "under 5 minutes", "replace": "15-30 minutes", "delete": "until replaced"}[action]

    def impact(r: InventoryResource, direct: bool) -> Dict[str, Any]:
        sev = severity_for_target if direct else ("high" if action == "delete" else "medium")
        return {
            "resource_id": r.id,
            "resource_name": r.name,
            "resource_type": r.type,
            "impact_type": "cost" if action == "create" else ("availability" if r.type in RUNTIME_TYPES else "configuration"),
            "impact_severity": sev,
            "impact_description": (
                f"{action.capitalize()} of this {r.type} resource" if direct
                else f"Depends on a changed resource ({r.type})"
            ),
            "estimated_downtime": downtime if direct else ("possible" if action in ("delete", "replace") else "none expected"),
            "recovery_time": ACTION_DURATION[action],
            "mitigation_actions": (
                ["Take a backup/snapshot before the change"] if r.type in DATA_TYPES else []
            ) + ([] if direct else ["Verify this service after the change"]),
        }

    # Business context from the owning assessments
    owning = [assessments[a] for a in {t.assessment_id for t in targets} if a in assessments]
    users = 0
    sla_targets: Set[str] = set()
    compliance: Set[str] = set()
    for a in owning:
        growth = (a.get("business_requirements") or {}).get("growth_projection") or {}
        users = max(users, int(growth.get("current_users") or 0))
        uptime = ((a.get("technical_requirements") or {}).get("performance_requirements") or {}).get("uptime_percentage")
        if uptime:
            sla_targets.add(f"{uptime}% uptime")
        compliance.update(
            c for c in (a.get("business_requirements") or {}).get("compliance_requirements") or []
            if c and str(c).lower() != "none"
        )
    touches_runtime = any(r.type in RUNTIME_TYPES for r in [*targets, *indirect])
    user_facing = is_prod and touches_runtime and action != "create"
    affected_users = users if user_facing else 0

    target_cost = sum(t.monthly_cost for t in targets)
    cost_change = {"create": target_cost, "delete": -target_cost}.get(action, 0.0)
    disruption = round(score / 100 * (1.0 if action in ("delete", "replace") else 0.5 if action == "update" else 0.1), 2)

    recommendations: List[Dict[str, Any]] = []

    def recommend(priority: str, title: str, description: str, rtype: str = "risk_reduction", effort: str = "low"):
        recommendations.append({
            "type": rtype, "priority": priority, "title": title, "description": description,
            "implementation_effort": effort, "potential_benefits": [], "risks_if_ignored": [],
        })

    if any(t.type in DATA_TYPES for t in targets) and action != "create":
        recommend("critical" if is_prod else "high", "Back up data first",
                  "Snapshot the affected data stores and verify the restore before applying the change.")
    if indirect:
        recommend("high", "Coordinate with dependent services",
                  f"{len(indirect)} resource(s) depend on what is changing: "
                  + ", ".join(sorted({r.name for r in indirect})[:5]) + ".")
    if is_prod and action != "create":
        recommend("high", "Use a staged rollout",
                  "Apply the change in staging first, then roll out to production during a maintenance window.",
                  rtype="best_practice", effort="medium")
    if action == "delete":
        recommend("high", "Confirm nothing still needs this resource",
                  "Check traffic and dependents before deleting; keep the final backup for a retention period.")
    if compliance:
        recommend("medium", "Record the change for compliance",
                  f"Document approval and evidence for {', '.join(sorted(compliance))}.", rtype="best_practice")
    if not recommendations:
        recommend("low", "Validate after the change", "Run smoke tests against the affected resources.",
                  rtype="best_practice")

    approvals = []
    if is_prod:
        approvals.append("Change Advisory Board")
    if action in ("delete", "replace"):
        approvals.append("Resource owner")
    if compliance:
        approvals.append("Compliance officer")

    def dep_impact(r: InventoryResource, propagation: float) -> Dict[str, Any]:
        return {
            "resource_id": r.id,
            "resource_name": r.name,
            "dependency_type": "data" if r.type in DATA_TYPES else "hard",
            "impact_propagation_risk": propagation,
            "failure_scenarios": [],
            "contingency_plans": [],
        }

    based_on_llm = any(t.from_llm_services for t in targets)
    return {
        "id": f"ana_{hashlib.sha1(repr(sorted(target_ids)).encode() + action.encode() + environment.encode()).hexdigest()[:12]}",
        "change_request_id": str(change_request.get("id") or ""),
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_risk_score": score,
        "risk_level": level,
        # Lower when the resources are fallback placeholders rather than LLM-recommended services
        "confidence_score": 0.8 if based_on_llm else 0.6,
        "blast_radius": {
            "directly_affected": [impact(t, True) for t in targets],
            "indirectly_affected": [impact(r, False) for r in indirect],
            "total_affected_count": len(targets) + len(indirect),
            "affected_environments": [environment],
            "affected_regions": sorted({r.region for r in [*targets, *indirect] if r.region}),
        },
        "dependency_analysis": {
            "upstream_dependencies": [dep_impact(index[u], 0.2) for u in upstream_ids],
            "downstream_dependencies": [
                dep_impact(r, 0.8 if action in ("delete", "replace") else 0.4) for r in indirect
            ],
            "circular_dependencies": [],
            "cascade_potential": round(len(indirect) / max(1, len(inventory)), 2),
        },
        "business_impact": {
            "service_disruption_risk": disruption,
            "user_impact_assessment": {
                "affected_users": affected_users,
                "user_groups": ["end users"] if affected_users else [],
                "impact_severity": (
                    "none" if not affected_users else "severe" if level == "critical"
                    else "moderate" if level == "high" else "minimal"
                ),
            },
            "financial_impact": {
                "potential_cost_change": round(cost_change, 2),
                "downtime_cost_estimate": 0,  # needs revenue data the assessment doesn't hold
                "recovery_cost_estimate": 0,
            },
            "sla_impact": {
                "affected_slas": sorted(sla_targets) if user_facing else [],
                "availability_risk": disruption if user_facing else 0,
                "performance_risk": round(disruption / 2, 2) if user_facing else 0,
            },
        },
        "compliance_impact": {
            "policy_violations": [],
            "regulatory_concerns": [],
            "security_implications": [],
            "audit_requirements": [f"Retain change records for {c}" for c in sorted(compliance)],
        },
        "operational_impact": {
            "monitoring_changes_needed": (
                [f"Add monitoring for new {t.type} resource {t.name}" for t in targets] if action == "create" else []
            ),
            "alerting_updates_required": (
                [f"Remove alerts for {t.name}" for t in targets] if action == "delete" else []
            ),
            "documentation_updates": ["Update the architecture diagram and runbooks"],
            "team_notifications": sorted({f"Owners of {r.name}" for r in indirect}),
            "skill_requirements": sorted({f"{t.provider.upper()} {t.type}" for t in targets}),
        },
        "risk_mitigation": {
            "recommendations": recommendations,
            "required_approvals": approvals,
            "testing_requirements": [],
            "rollback_procedures": [],
        },
        "timeline_analysis": {
            "estimated_duration": ACTION_DURATION[action],
            "maintenance_windows": [],
            "critical_path_resources": [t.id for t in targets if t.type in DATA_TYPES],
            "parallel_execution_opportunities": (
                [t.id for t in targets if t.type not in DATA_TYPES] if len(targets) > 1 else []
            ),
        },
        "alternatives": {
            "alternative_approaches": [],
            "phased_rollout_options": [],
            "blue_green_feasibility": action in ("update", "replace") and not any(t.type in DATA_TYPES for t in targets),
            "canary_deployment_options": [],
        },
    }
