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
        index = next((i for i, d in enumerate(self.docs) if _matches(d, query)), None)
        if index is not None:
            del self.docs[index]
        return SimpleNamespace(deleted_count=before - len(self.docs))

    async def delete_many(self, query):
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
        gitops_repositories=_Collection(),
        gitops_applications=_Collection(),
        gitops_deployments=_Collection(),
        gitops_deployment_plans=_Collection(),
        gitops_drift=_Collection(),
        gitops_pull_requests=_Collection(),
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


# ---------------------------------------------------------------- legacy GitOps endpoints

GITOPS = "/api/v1/gitops"


def test_every_gitops_route_requires_login():
    """Enumerates the router so a newly added route without auth fails this test."""
    app = create_app()
    app.dependency_overrides[get_database] = lambda: SimpleNamespace()
    checked = 0
    with TestClient(app) as client:
        # The OpenAPI schema lists every route, however routers are nested
        for path, operations in app.openapi()["paths"].items():
            if "/gitops/" not in path:  # mounted under /api, /api/v1 and /api/v2
                continue
            url = path.replace("{", "").replace("}", "")  # concrete placeholder values
            for method in operations:
                response = client.request(method.upper(), url, json={})
                assert response.status_code in (401, 403), f"{method} {path} -> {response.status_code}"
                checked += 1
    assert checked >= 80  # guards against enumerating nothing (29 operations x 3 prefixes today)


def _connect(api, url="https://github.com/acme/infra.git", **extra):
    return api.client.post(f"{GITOPS}/repositories", json={"provider": "github", "repo_url": url, **extra})


def test_repository_connect_list_and_disconnect(api):
    created = _connect(api, access_token="ghp_secret")
    assert created.status_code == 201
    repo = created.json()
    assert repo["name"] == "infra" and repo["url"] == "https://github.com/acme/infra.git"
    assert repo["has_credentials"] is True
    # The token is never stored or returned
    assert "access_token" not in repo
    assert "ghp_secret" not in repr(api.db.gitops_repositories.docs)

    assert [r["id"] for r in api.client.get(f"{GITOPS}/repositories").json()] == [repo["id"]]
    assert _connect(api).status_code == 409  # same URL twice
    assert api.client.delete(f"{GITOPS}/repositories/{repo['id']}").status_code == 204
    assert api.client.get(f"{GITOPS}/repositories").json() == []


@pytest.mark.parametrize("url", ["not a url", "ftp://example.com/repo", ""])
def test_repository_url_is_validated(api, url):
    assert _connect(api, url=url).status_code == 422


def test_repositories_are_private_and_in_use_ones_cannot_be_removed(api):
    repo = _connect(api).json()
    app = api.client.post(f"{GITOPS}/applications", json={"name": "web", "repository_id": repo["id"]})
    assert app.status_code == 201
    assert api.client.get(f"{GITOPS}/repositories").json()[0]["applications"] == ["web"]
    blocked = api.client.delete(f"{GITOPS}/repositories/{repo['id']}")
    assert blocked.status_code == 409 and "web" in blocked.json()["detail"]

    api.user.id = BOB
    assert api.client.get(f"{GITOPS}/repositories").json() == []
    assert api.client.get(f"{GITOPS}/applications").json() == []
    assert api.client.get(f"{GITOPS}/repositories/{repo['id']}").status_code == 404
    assert api.client.delete(f"{GITOPS}/repositories/{repo['id']}").status_code == 404
    # Can't attach an application to someone else's repository
    assert api.client.post(f"{GITOPS}/applications",
                           json={"name": "x", "repository_id": repo["id"]}).status_code == 404


def test_sync_and_rollback_are_recorded_not_executed(api):
    repo = _connect(api).json()
    app = api.client.post(f"{GITOPS}/applications",
                          json={"name": "web", "repository_id": repo["id"], "target_revision": "v2"}).json()

    sync = api.client.post(f"{GITOPS}/applications/{app['id']}/sync", json={"prune": True})
    assert sync.status_code == 200 and sync.json()["status"] == "pending"
    assert "not executed" in sync.json()["message"]
    rollback = api.client.post(f"{GITOPS}/applications/{app['id']}/rollback", json={"target_revision": "v1"})
    assert rollback.status_code == 200
    assert api.client.post(f"{GITOPS}/applications/{app['id']}/rollback", json={}).status_code == 422

    history = api.client.get(f"{GITOPS}/deployments?application_id={app['id']}").json()
    assert {(d["kind"], d["revision"], d["status"]) for d in history} == {
        ("sync", "v2", "pending"), ("rollback", "v1", "pending")}
    assert api.client.get(f"{GITOPS}/applications/{app['id']}").json()["deployment_status"] == "pending"
    status_resp = api.client.get(f"{GITOPS}/deployments/{sync.json()['deployment_id']}/status")
    assert status_resp.json()["status"] == "pending"
    assert api.client.post(f"{GITOPS}/applications/missing/sync", json={}).status_code == 404


def test_deployment_plan_create_list_and_deploy(api):
    repo = _connect(api).json()
    template = api.client.post(f"{GITOPS}/templates", json=TEMPLATE).json()
    plan = api.client.post(f"{GITOPS}/deployment-plans", json={
        "name": "vpc-dev", "repository": repo, "template": template, "environment": "dev",
        "variables": {"region": "eu-west-1"},
    })
    assert plan.status_code == 201
    body = plan.json()
    assert body["repository"]["id"] == repo["id"] and body["template"]["id"] == template["id"]

    assert [p["id"] for p in api.client.get(f"{GITOPS}/deployment-plans").json()] == [body["id"]]
    deployed = api.client.post(f"{GITOPS}/deployment-plans/{body['id']}/deploy", json={"environment": "staging"})
    assert deployed.status_code == 200 and deployed.json()["status"] == "pending"
    recorded = api.client.get(f"{GITOPS}/deployments").json()
    assert [(d["kind"], d["plan_id"], d["environment"]) for d in recorded] == [("plan", body["id"], "staging")]

    # References must belong to the user
    api.user.id = BOB
    assert api.client.post(f"{GITOPS}/deployment-plans", json={
        "name": "steal", "repository": repo, "template": template}).status_code == 404
    assert api.client.post(f"{GITOPS}/deployment-plans/{body['id']}/deploy", json={}).status_code == 404


def test_drift_analytics_and_health_reflect_stored_data(api):
    assert api.client.get(f"{GITOPS}/drift").json() == []
    assert api.client.post(f"{GITOPS}/drift/missing/fix").status_code == 404

    repo = _connect(api).json()
    app = api.client.post(f"{GITOPS}/applications", json={"name": "web", "repository_id": repo["id"]}).json()
    api.client.post(f"{GITOPS}/applications/{app['id']}/sync", json={})

    analytics = api.client.get(f"{GITOPS}/analytics?timeframe=30d").json()
    assert analytics["summary"]["total_repositories"] == 1
    assert analytics["summary"]["total_applications"] == 1
    assert analytics["summary"]["deployment_requests"] == 1
    assert analytics["summary"]["success_rate"] is None  # nothing has completed
    assert analytics["deployments_by_status"] == {"pending": 1}
    assert api.client.get(f"{GITOPS}/analytics?timeframe=forever").status_code == 422

    health = api.client.get(f"{GITOPS}/health").json()
    assert health["status"] == "not_connected" and health["pending_requests"] == 1


# ---------------------------------------------------------------- pull requests

def _open_pr(api, repo_id, source="feature/vpc", target="main", title="Add VPC"):
    return api.client.post(f"{GITOPS}/repositories/{repo_id}/pull-requests",
                           json={"title": title, "description": "d", "source_branch": source, "target_branch": target})


def test_pull_request_create_list_and_get(api):
    repo = _connect(api).json()
    created = _open_pr(api, repo["id"])
    assert created.status_code == 201
    pr = created.json()
    assert pr["id"] == 1 and pr["state"] == "open" and pr["author"] == "alice@example.com"
    assert pr["url"] == "https://github.com/acme/infra/compare/main...feature/vpc"
    assert pr["checks_status"] == "pending" and "not a pull request on the Git host" in pr["note"]
    assert _open_pr(api, repo["id"], source="feature/dns").json()["id"] == 2  # numbered per repository

    listed = api.client.get(f"{GITOPS}/repositories/{repo['id']}/pull-requests").json()
    assert [p["id"] for p in listed] == [2, 1]
    assert api.client.get(f"{GITOPS}/repositories/{repo['id']}/pull-requests/1").json()["title"] == "Add VPC"
    assert api.client.get(f"{GITOPS}/repositories/{repo['id']}/pull-requests/99").status_code == 404


@pytest.mark.parametrize("source,target,code", [
    ("feature/vpc", "feature/vpc", 400),   # same branch
    ("a..b", "main", 422),                 # invalid branch names
    ("feature/", "main", 422),
    ("ok", "bad name", 422),
])
def test_pull_request_branch_validation(api, source, target, code):
    repo = _connect(api).json()
    assert _open_pr(api, repo["id"], source=source, target=target).status_code == code


def test_duplicate_open_pull_request_is_rejected(api):
    repo = _connect(api).json()
    assert _open_pr(api, repo["id"]).status_code == 201
    assert _open_pr(api, repo["id"]).status_code == 409
    assert _open_pr(api, repo["id"], target="develop").status_code == 201  # different target is fine


def test_review_and_merge_rules(api):
    repo = _connect(api).json()
    base = f"{GITOPS}/repositories/{repo['id']}/pull-requests/1"
    _open_pr(api, repo["id"])

    assert api.client.post(f"{base}/reject", json={}).status_code == 422  # a reason is required
    rejected = api.client.post(f"{base}/reject", json={"comment": "Needs tags"}).json()
    assert [(a["user"], a["status"]) for a in rejected["approvals"]] == [("alice@example.com", "rejected")]
    blocked = api.client.post(f"{base}/merge", json={})
    assert blocked.status_code == 409 and "Changes requested" in blocked.json()["detail"]

    # A new review from the same reviewer replaces the earlier one
    approved = api.client.post(f"{base}/approve", json={"comment": "Fixed"}).json()
    assert [(a["user"], a["status"]) for a in approved["approvals"]] == [("alice@example.com", "approved")]

    merged = api.client.post(f"{base}/merge", json={"merge_method": "squash"})
    assert merged.status_code == 200
    assert merged.json()["state"] == "merged" and merged.json()["merge_method"] == "squash"
    assert api.client.post(f"{base}/merge", json={}).status_code == 409
    assert api.client.post(f"{base}/approve", json={}).status_code == 409
    assert api.client.post(f"{base}/merge", json={"merge_method": "fast-forward"}).status_code in (409, 422)

    states = {s: [p["id"] for p in api.client.get(
        f"{GITOPS}/repositories/{repo['id']}/pull-requests?state={s}").json()] for s in ("open", "merged", "all")}
    assert states == {"open": [], "merged": [1], "all": [1]}


def test_pull_requests_are_private_and_removed_with_their_repository(api):
    repo = _connect(api).json()
    _open_pr(api, repo["id"])
    api.user.id = BOB
    assert api.client.get(f"{GITOPS}/repositories/{repo['id']}/pull-requests").status_code == 404
    assert _open_pr(api, repo["id"]).status_code == 404
    assert api.client.post(f"{GITOPS}/repositories/{repo['id']}/pull-requests/1/approve", json={}).status_code == 404

    api.user.id = ALICE
    assert api.client.delete(f"{GITOPS}/repositories/{repo['id']}").status_code == 204
    assert api.db.gitops_pull_requests.docs == []

