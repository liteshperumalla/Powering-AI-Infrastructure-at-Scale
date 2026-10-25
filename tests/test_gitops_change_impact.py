"""
Tests for GitOps IaC templates and change-impact resources/analysis.

The endpoint tests run through FastAPI against a small in-memory stand-in for the
Motor collections they use, so persistence and per-user scoping are exercised.
"""

import copy
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from src.infra_mind.api.endpoints.auth import get_current_user
from src.infra_mind.core.dependencies import get_database
from src.infra_mind.main import create_app
from src.infra_mind.services.change_impact_service import (
    analyze_change,
    build_inventory,
    dependency_view,
)


# ---------------------------------------------------------------- in-memory Motor stand-in

def _matches(doc, query):
    for key, cond in query.items():
        value = doc.get(key)
        if isinstance(cond, dict) and "$in" in cond:
            if value not in cond["$in"]:
                return False
        elif isinstance(cond, dict) and "$ne" in cond:
            if value == cond["$ne"]:
                return False
        elif value != cond:
            return False
    return True


class _Cursor:
    def __init__(self, docs):
        self._docs = docs

    def sort(self, key, direction):
        self._docs.sort(key=lambda d: d.get(key) or "", reverse=direction < 0)
        return self

    async def to_list(self, length=None):
        return copy.deepcopy(self._docs)


class _Collection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def find(self, query=None):
        return _Cursor([d for d in self.docs if _matches(d, query or {})])

    async def find_one(self, query):
        return next((copy.deepcopy(d) for d in self.docs if _matches(d, query)), None)

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))

    async def find_one_and_update(self, query, update, return_document=False):
        for d in self.docs:
            if _matches(d, query):
                d.update(update.get("$set", {}))
                return copy.deepcopy(d)
        return None

    async def delete_one(self, query):
        before = len(self.docs)
        self.docs = [d for d in self.docs if not _matches(d, query)]
        return SimpleNamespace(deleted_count=before - len(self.docs))


# ---------------------------------------------------------------- sample data

ALICE, BOB = "user-alice", "user-bob"


def _assessment(_id, user_id, title="Shop", provider="Azure", users=1000, compliance=("HIPAA",)):
    return {
        "_id": _id,
        "user_id": user_id,
        "title": title,
        "business_requirements": {
            "geographic_regions": ["Europe"],
            "growth_projection": {"current_users": users},
            "compliance_requirements": list(compliance),
        },
        "technical_requirements": {
            "current_cloud_providers": [provider],
            "performance_requirements": {"uptime_percentage": 99.9},
        },
    }


def _rec(_id, assessment_id, category, title, cost="100", services=None):
    return {
        "_id": _id,
        "assessment_id": assessment_id,
        "category": category,
        "title": title,
        "total_estimated_monthly_cost": cost,
        "recommended_services": services or [],
    }


ASSESSMENTS = [_assessment("a1", ALICE), _assessment("b1", BOB, title="Bob's app")]
RECOMMENDATIONS = [
    _rec("r1", "a1", "compute", "Compute Infrastructure [LLM Analysis Unavailable]", "200"),
    _rec("r2", "a1", "database", "Database Services [LLM Analysis Unavailable]", "150"),
    _rec("r3", "a1", "storage", "Storage Solution [LLM Analysis Unavailable]", "50"),
    _rec("r4", "a1", "compute", "Compute Infrastructure [LLM Analysis Unavailable]", "200"),  # duplicate
    _rec("r5", "a1", "general", "Synthesized General Recommendations", "1500"),  # not a resource
    _rec("r6", "b1", "database", "Bob Database", "80"),
]


# ---------------------------------------------------------------- service unit tests

def _by_name(inventory):
    return {r.name: r for r in inventory}


def test_inventory_maps_dedupes_and_infers_dependencies():
    inventory = build_inventory([ASSESSMENTS[0]], RECOMMENDATIONS)
    names = _by_name(inventory)
    assert set(names) == {"Compute Infrastructure", "Database Services", "Storage Solution"}
    compute, db, storage = names["Compute Infrastructure"], names["Database Services"], names["Storage Solution"]
    assert {r.provider for r in inventory} == {"azure"}
    assert compute.region == "Europe" and compute.monthly_cost == 200.0
    assert set(compute.depends_on) == {db.id, storage.id}
    assert db.dependents == [compute.id] and storage.dependents == [compute.id]
    assert not compute.from_llm_services


def test_inventory_prefers_llm_recommended_services():
    rec = _rec("r9", "a1", "compute", "Compute plan", services=[
        {"service_name": "EC2 m6i.large", "provider": "aws", "service_category": "compute", "estimated_monthly_cost": "70"},
        {"service_name": "RDS Postgres", "provider": "aws", "service_category": "database", "estimated_monthly_cost": "120"},
    ])
    names = _by_name(build_inventory([ASSESSMENTS[0]], [rec]))
    assert set(names) == {"EC2 m6i.large", "RDS Postgres"}
    assert names["EC2 m6i.large"].provider == "aws" and names["EC2 m6i.large"].from_llm_services
    assert names["EC2 m6i.large"].depends_on == [names["RDS Postgres"].id]


def test_provider_filter_and_dependency_view():
    inventory = build_inventory([ASSESSMENTS[0]], RECOMMENDATIONS)
    assert build_inventory([ASSESSMENTS[0]], RECOMMENDATIONS, provider_filter="aws") == []
    db = _by_name(inventory)["Database Services"]
    view = dependency_view(db.id, inventory, depth=2, environment="prod")
    assert [r["name"] for r in view["downstream"]] == ["Compute Infrastructure"]
    assert view["upstream"] == []
    assert {"from": view["downstream"][0]["id"], "to": db.id} in view["dependency_graph"]["edges"]


def _analyze(names, action, env):
    inventory = build_inventory([ASSESSMENTS[0]], RECOMMENDATIONS)
    by_name = _by_name(inventory)
    request = {
        "id": "chg-1",
        "change_type": action,
        "target_environment": env,
        "resources": [{"resource_id": by_name[n].id} for n in names],
    }
    return analyze_change(request, inventory, {"a1": ASSESSMENTS[0]})


def test_deleting_prod_database_is_high_risk_with_cascade():
    result = _analyze(["Database Services"], "delete", "prod")
    assert result["risk_level"] == "critical" and result["overall_risk_score"] >= 80
    assert [r["resource_name"] for r in result["blast_radius"]["indirectly_affected"]] == ["Compute Infrastructure"]
    assert result["blast_radius"]["total_affected_count"] == 2
    assert result["business_impact"]["user_impact_assessment"]["affected_users"] == 1000
    assert result["business_impact"]["financial_impact"]["potential_cost_change"] == -150.0
    assert result["business_impact"]["sla_impact"]["affected_slas"] == ["99.9% uptime"]
    titles = [r["title"] for r in result["risk_mitigation"]["recommendations"]]
    assert "Back up data first" in titles and "Record the change for compliance" in titles
    assert set(result["risk_mitigation"]["required_approvals"]) == {
        "Change Advisory Board", "Resource owner", "Compliance officer"}
    assert result["compliance_impact"]["audit_requirements"] == ["Retain change records for HIPAA"]
    assert result["confidence_score"] == 0.6  # placeholder resources, not LLM services


def test_creating_dev_storage_is_low_risk_and_user_neutral():
    result = _analyze(["Storage Solution"], "create", "dev")
    assert result["risk_level"] == "low"
    assert result["business_impact"]["user_impact_assessment"]["affected_users"] == 0
    assert result["business_impact"]["financial_impact"]["potential_cost_change"] == 50.0
    assert result["business_impact"]["sla_impact"]["affected_slas"] == []
    assert "Back up data first" not in [r["title"] for r in result["risk_mitigation"]["recommendations"]]


# ---------------------------------------------------------------- endpoint tests

@pytest.fixture
def api():
    app = create_app()
    db = SimpleNamespace(
        assessments=_Collection(ASSESSMENTS),
        recommendations=_Collection(RECOMMENDATIONS),
        iac_templates=_Collection(),
    )
    user = SimpleNamespace(id=ALICE, email="alice@example.com")
    app.dependency_overrides[get_database] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, user=user, db=db)
    app.dependency_overrides.clear()


TEMPLATE = {
    "name": "VPC baseline",
    "description": "Network baseline",
    "provider": "terraform",
    "language": "hcl",
    "template": 'resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }',
    "variables": {"region": "eu-west-1"},
    "outputs": {},
    "tags": ["network"],
    "version": "1.0.0",
}


@pytest.mark.parametrize("prefix", ["/api/v1/gitops", "/api/v2/gitops"])
def test_template_crud_round_trip(api, prefix):
    created = api.client.post(f"{prefix}/templates", json=TEMPLATE)
    assert created.status_code == 201
    tid = created.json()["id"]
    assert "user_id" not in created.json()

    listed = api.client.get(f"{prefix}/templates").json()
    assert [t["id"] for t in listed] == [tid]

    updated = api.client.put(f"{prefix}/templates/{tid}", json={"version": "1.1.0"})
    assert updated.status_code == 200 and updated.json()["version"] == "1.1.0"
    assert updated.json()["name"] == "VPC baseline"  # untouched fields kept

    assert api.client.get(f"{prefix}/templates/{tid}").json()["version"] == "1.1.0"
    assert api.client.delete(f"{prefix}/templates/{tid}").status_code == 204
    assert api.client.get(f"{prefix}/templates/{tid}").status_code == 404
    assert api.client.get(f"{prefix}/templates").json() == []


def test_templates_are_private_to_their_owner(api):
    tid = api.client.post("/api/v1/gitops/templates", json=TEMPLATE).json()["id"]
    api.user.id = BOB
    assert api.client.get("/api/v1/gitops/templates").json() == []
    assert api.client.get(f"/api/v1/gitops/templates/{tid}").status_code == 404
    assert api.client.put(f"/api/v1/gitops/templates/{tid}", json={"name": "x"}).status_code == 404
    assert api.client.delete(f"/api/v1/gitops/templates/{tid}").status_code == 404
    assert len(api.db.iac_templates.docs) == 1


@pytest.mark.parametrize("bad", [
    {"provider": "ansible"},
    {"template": ""},
    {"name": ""},
])
def test_template_validation(api, bad):
    assert api.client.post("/api/v1/gitops/templates", json={**TEMPLATE, **bad}).status_code == 422


def test_resources_are_scoped_to_the_current_user(api):
    alice = api.client.get("/api/v2/change-impact/resources?environment=prod")
    assert alice.status_code == 200
    names = sorted(r["name"] for r in alice.json())
    assert names == ["Compute Infrastructure", "Database Services", "Storage Solution"]
    assert {r["environment"] for r in alice.json()} == {"prod"}

    api.user.id = BOB
    assert [r["name"] for r in api.client.get("/api/v2/change-impact/resources").json()] == ["Bob Database"]

    api.user.id = "nobody"
    assert api.client.get("/api/v2/change-impact/resources").json() == []


def test_resource_detail_dependencies_and_bad_environment(api):
    resources = {r["name"]: r for r in api.client.get("/api/v2/change-impact/resources").json()}
    db_id = resources["Database Services"]["id"]
    assert api.client.get(f"/api/v2/change-impact/resources/{db_id}").json()["type"] == "database"
    deps = api.client.get(f"/api/v2/change-impact/resources/{db_id}/dependencies?depth=1").json()
    assert [r["name"] for r in deps["downstream"]] == ["Compute Infrastructure"]
    assert api.client.get("/api/v2/change-impact/resources/res_missing").status_code == 404
    assert api.client.get("/api/v2/change-impact/resources?environment=qa").status_code == 422


def test_analyze_endpoint(api):
    resources = {r["name"]: r for r in api.client.get("/api/v2/change-impact/resources").json()}
    body = {
        "id": "1",
        "title": "Drop DB",
        "change_type": "delete",
        "target_environment": "prod",
        "resources": [{"resource_id": resources["Database Services"]["id"], "action": "delete"}],
    }
    result = api.client.post("/api/v2/change-impact/analyze", json=body)
    assert result.status_code == 200
    assert result.json()["risk_level"] == "critical"
    assert result.json()["blast_radius"]["total_affected_count"] == 2

    single = api.client.post(
        f"/api/v2/change-impact/resources/{resources['Storage Solution']['id']}/analyze?environment=dev",
        json={"action": "create", "change_attributes": []},
    )
    assert single.status_code == 200 and single.json()["risk_level"] == "low"

    assert api.client.post("/api/v2/change-impact/analyze", json={**body, "resources": []}).status_code == 400
    missing = api.client.post("/api/v2/change-impact/analyze",
                              json={**body, "resources": [{"resource_id": "res_missing"}]})
    assert missing.status_code == 404

    # Another user's resource is unknown to Alice
    api.user.id = BOB
    bob_db = api.client.get("/api/v2/change-impact/resources").json()[0]["id"]
    api.user.id = ALICE
    assert api.client.post("/api/v2/change-impact/analyze",
                           json={**body, "resources": [{"resource_id": bob_db}]}).status_code == 404
