"""
GitOps Integration endpoints for Infra Mind.

Handles GitOps workflows, repository management, deployment automation, and configuration drift detection.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime, timedelta
from pydantic import AliasChoices, BaseModel, Field, field_validator
import re
import uuid
from enum import Enum
from typing import Literal

from .auth import get_current_user
from ...core.dependencies import DatabaseDep
from ...models.user import User

router = APIRouter()
security = HTTPBearer()

# Data Models
#
# Everything below is stored per user in MongoDB. This service records GitOps
# configuration and requests; it is not connected to a GitOps controller (e.g.
# Argo CD), so sync/rollback/deploy requests are recorded as `pending` and never
# executed here, and drift is only what has been recorded.

NOT_EXECUTED_NOTE = "No GitOps controller is connected; the request was recorded but not executed."


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class SyncStatus(str, Enum):
    SYNCED = "synced"
    OUT_OF_SYNC = "out_of_sync"
    UNKNOWN = "unknown"
    ERROR = "error"

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    PROGRESSING = "progressing"
    SUSPENDED = "suspended"
    MISSING = "missing"
    UNKNOWN = "unknown"

GitProvider = Literal["github", "gitlab", "bitbucket", "azure_devops", "other"]
Environment = Literal["dev", "staging", "prod"]
REPO_URL_PATTERN = r"^(https?://\S+|git@\S+:\S+)$"


class RepositoryCreate(BaseModel):
    # The frontend sends repo_url; older clients send url
    url: str = Field(validation_alias=AliasChoices("url", "repo_url"), pattern=REPO_URL_PATTERN, max_length=500)
    name: Optional[str] = Field(default=None, max_length=200)
    provider: GitProvider = "github"
    branch: str = Field(default="main", max_length=200)
    path: str = Field(default="/", max_length=500)
    auto_sync_enabled: bool = True
    # Accepted but never stored or returned: nothing here uses Git credentials
    access_token: Optional[str] = Field(default=None, exclude=True)


class ApplicationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    repository_id: str
    namespace: str = Field(default="default", max_length=200)
    project: str = Field(default="default", max_length=200)
    target_revision: str = Field(default="HEAD", max_length=200)
    path: str = Field(default=".", max_length=500)
    sync_policy: Dict[str, Any] = {}


class SyncRequest(BaseModel):
    prune: bool = False
    dry_run: bool = False
    force: bool = False
    resources: List[Dict[str, Any]] = []


class RollbackRequest(BaseModel):
    target_revision: str = Field(min_length=1, max_length=200)


class DeploymentPlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    repository: Dict[str, Any]  # frontend sends the full repository object; only its id is used
    template: Dict[str, Any]    # likewise for the IaC template
    branch: str = Field(default="main", max_length=200)
    environment: Environment = "dev"
    variables: Dict[str, Any] = {}
    approval_required: bool = True
    auto_deploy: bool = False
    rollback_enabled: bool = True
    notification_settings: Dict[str, Any] = {}


class DeployRequest(BaseModel):
    environment: Optional[Environment] = None


def _now() -> str:
    return datetime.utcnow().isoformat()


def _out(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc = dict(doc)
    doc["id"] = doc.pop("_id")
    doc.pop("user_id", None)
    return doc


def _owned(user: User, **query: Any) -> Dict[str, Any]:
    return {"user_id": str(user.id), **query}


async def _get_owned(collection, user: User, doc_id: str, label: str) -> Dict[str, Any]:
    doc = await collection.find_one(_owned(user, _id=doc_id))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return doc


async def _record_deployment(db, user: User, **fields: Any) -> Dict[str, Any]:
    doc = {
        "_id": str(uuid.uuid4()),
        "user_id": str(user.id),
        "status": DeploymentStatus.PENDING.value,
        "requested_at": _now(),
        "note": NOT_EXECUTED_NOTE,
        **fields,
    }
    await db.gitops_deployments.insert_one(doc)
    return doc


async def _repository_out(db, user: User, repo: Dict[str, Any]) -> Dict[str, Any]:
    apps = await db.gitops_applications.find(_owned(user, repository_id=repo["_id"])).to_list(length=None)
    out = _out(repo)
    out["applications"] = [a["name"] for a in apps]
    out["full_name"] = repo["name"]
    return out


# ==================== REPOSITORIES ====================

@router.get("/repositories")
async def get_gitops_repositories(
    db: DatabaseDep,
    sync_status: Optional[SyncStatus] = None,
    health_status: Optional[HealthStatus] = None,
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """The current user's connected repositories."""
    query = _owned(current_user)
    if sync_status:
        query["sync_status"] = sync_status.value
    if health_status:
        query["health_status"] = health_status.value
    repos = await db.gitops_repositories.find(query).sort("created_at", -1).to_list(length=None)
    return [await _repository_out(db, current_user, r) for r in repos]


@router.post("/repositories", status_code=status.HTTP_201_CREATED)
async def add_gitops_repository(
    repo: RepositoryCreate,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Connect a repository. A supplied access token is not stored."""
    name = repo.name or repo.url.rstrip("/").removesuffix(".git").rsplit("/", 1)[-1].rsplit(":", 1)[-1]
    if await db.gitops_repositories.find_one(_owned(current_user, url=repo.url)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Repository already connected")
    doc = {
        "_id": str(uuid.uuid4()),
        "user_id": str(current_user.id),
        "name": name,
        "url": repo.url,
        "provider": repo.provider,
        "branch": repo.branch,
        "path": repo.path,
        "auto_sync_enabled": repo.auto_sync_enabled,
        "has_credentials": bool(repo.access_token),
        "sync_status": SyncStatus.UNKNOWN.value,
        "health_status": HealthStatus.UNKNOWN.value,
        "last_sync": None,
        "created_at": _now(),
    }
    await db.gitops_repositories.insert_one(doc)
    logger.info(f"Connected GitOps repository {doc['_id']} for user {current_user.id}")
    return await _repository_out(db, current_user, doc)


@router.get("/repositories/{repository_id}")
async def get_gitops_repository(
    repository_id: str,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    repo = await _get_owned(db.gitops_repositories, current_user, repository_id, "Repository")
    return await _repository_out(db, current_user, repo)


@router.delete("/repositories/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_gitops_repository(
    repository_id: str,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> None:
    """Disconnect a repository (and its pull requests). Refused while applications still use it."""
    await _get_owned(db.gitops_repositories, current_user, repository_id, "Repository")
    apps = await db.gitops_applications.find(_owned(current_user, repository_id=repository_id)).to_list(length=None)
    if apps:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository is used by applications: {', '.join(a['name'] for a in apps)}",
        )
    await db.gitops_repositories.delete_one(_owned(current_user, _id=repository_id))
    await db.gitops_pull_requests.delete_many(_owned(current_user, repository_id=repository_id))


# ==================== APPLICATIONS ====================

@router.get("/applications")
async def get_gitops_applications(
    db: DatabaseDep,
    namespace: Optional[str] = None,
    sync_status: Optional[SyncStatus] = None,
    health_status: Optional[HealthStatus] = None,
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    query = _owned(current_user)
    if namespace:
        query["namespace"] = namespace
    if sync_status:
        query["sync_status"] = sync_status.value
    if health_status:
        query["health_status"] = health_status.value
    apps = await db.gitops_applications.find(query).sort("created_at", -1).to_list(length=None)
    return [_out(a) for a in apps]


@router.post("/applications", status_code=status.HTTP_201_CREATED)
async def create_gitops_application(
    app_data: ApplicationCreate,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    await _get_owned(db.gitops_repositories, current_user, app_data.repository_id, "Repository")
    if await db.gitops_applications.find_one(_owned(current_user, name=app_data.name, namespace=app_data.namespace)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application already exists in this namespace")
    doc = {
        "_id": str(uuid.uuid4()),
        "user_id": str(current_user.id),
        **app_data.model_dump(),
        "sync_status": SyncStatus.UNKNOWN.value,
        "health_status": HealthStatus.UNKNOWN.value,
        "deployment_status": None,
        "last_deployment": None,
        "resources": [],
        "created_at": _now(),
    }
    await db.gitops_applications.insert_one(doc)
    logger.info(f"Created GitOps application {doc['_id']} for user {current_user.id}")
    return _out(doc)


@router.get("/applications/{application_id}")
async def get_application_details(
    application_id: str,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    return _out(await _get_owned(db.gitops_applications, current_user, application_id, "Application"))


async def _request_operation(db, user: User, app: Dict[str, Any], kind: str, revision: str, **extra: Any) -> Dict[str, Any]:
    deployment = await _record_deployment(
        db, user, kind=kind, application_id=app["_id"], revision=revision, **extra
    )
    await db.gitops_applications.find_one_and_update(
        _owned(user, _id=app["_id"]),
        {"$set": {"deployment_status": DeploymentStatus.PENDING.value, "last_requested_at": deployment["requested_at"]}},
    )
    return deployment


@router.post("/applications/{application_id}/sync")
async def sync_application(
    application_id: str,
    db: DatabaseDep,
    sync_options: SyncRequest = SyncRequest(),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Record a sync request for an application."""
    app = await _get_owned(db.gitops_applications, current_user, application_id, "Application")
    deployment = await _request_operation(
        db, current_user, app, "sync", app["target_revision"], options=sync_options.model_dump()
    )
    return {
        "sync_id": deployment["_id"],
        "deployment_id": deployment["_id"],
        "application_id": application_id,
        "status": deployment["status"],
        "initiated_at": deployment["requested_at"],
        "sync_options": deployment["options"],
        "message": NOT_EXECUTED_NOTE,
    }


@router.post("/applications/{application_id}/rollback")
async def rollback_application(
    application_id: str,
    rollback_data: RollbackRequest,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Record a rollback request for an application."""
    app = await _get_owned(db.gitops_applications, current_user, application_id, "Application")
    deployment = await _request_operation(db, current_user, app, "rollback", rollback_data.target_revision)
    return {
        "rollback_id": deployment["_id"],
        "deployment_id": deployment["_id"],
        "application_id": application_id,
        "target_revision": rollback_data.target_revision,
        "status": deployment["status"],
        "initiated_at": deployment["requested_at"],
        "message": NOT_EXECUTED_NOTE,
    }


# ==================== DEPLOYMENTS ====================

@router.get("/deployments")
async def get_deployment_history(
    db: DatabaseDep,
    application_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=200),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Recorded sync, rollback and deploy requests, newest first."""
    query = _owned(current_user)
    if application_id:
        query["application_id"] = application_id
    docs = await db.gitops_deployments.find(query).sort("requested_at", -1).to_list(length=None)
    return [_out(d) for d in docs[:limit]]


@router.get("/deployments/{deployment_id}/status")
async def get_deployment_status(
    deployment_id: str,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    deployment = await _get_owned(db.gitops_deployments, current_user, deployment_id, "Deployment")
    return {
        "status": deployment["status"],
        "logs": [deployment.get("note", "")],
        "progress": 0,
        "start_time": deployment["requested_at"],
        "end_time": None,
        "error": None,
    }


# ==================== DEPLOYMENT PLANS ====================

async def _plan_out(db, user: User, plan: Dict[str, Any]) -> Dict[str, Any]:
    out = _out(plan)
    repo = await db.gitops_repositories.find_one(_owned(user, _id=plan["repository_id"]))
    template = await db.iac_templates.find_one(_owned(user, _id=plan["template_id"]))
    # Hydrated for the frontend's DeploymentPlan shape; null if since removed
    out["repository"] = await _repository_out(db, user, repo) if repo else None
    out["template"] = _out(template) if template else None
    return out


@router.post("/deployment-plans", status_code=status.HTTP_201_CREATED)
async def create_deployment_plan(
    plan: DeploymentPlanCreate,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    repo = await _get_owned(db.gitops_repositories, current_user, str(plan.repository.get("id")), "Repository")
    template = await _get_owned(db.iac_templates, current_user, str(plan.template.get("id")), "Template")
    doc = {
        "_id": str(uuid.uuid4()),
        "user_id": str(current_user.id),
        **plan.model_dump(exclude={"repository", "template"}),
        "repository_id": repo["_id"],
        "template_id": template["_id"],
        "created_at": _now(),
    }
    await db.gitops_deployment_plans.insert_one(doc)
    return await _plan_out(db, current_user, doc)


@router.get("/deployment-plans")
async def list_deployment_plans(
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    plans = await db.gitops_deployment_plans.find(_owned(current_user)).sort("created_at", -1).to_list(length=None)
    return [await _plan_out(db, current_user, p) for p in plans]


@router.post("/deployment-plans/{plan_id}/deploy")
async def deploy_plan(
    plan_id: str,
    db: DatabaseDep,
    request: DeployRequest = DeployRequest(),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Record a deploy request for a plan."""
    plan = await _get_owned(db.gitops_deployment_plans, current_user, plan_id, "Deployment plan")
    deployment = await _record_deployment(
        db, current_user, kind="plan", plan_id=plan_id,
        environment=request.environment or plan["environment"], revision=plan["branch"],
    )
    return {"deployment_id": deployment["_id"], "status": deployment["status"], "message": NOT_EXECUTED_NOTE}


# ==================== DRIFT ====================

@router.get("/drift")
async def get_configuration_drift(
    db: DatabaseDep,
    application_id: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Recorded configuration drift. Detection needs a connected cluster, so this is empty until one reports drift."""
    query = _owned(current_user)
    if application_id:
        query["application_id"] = application_id
    if severity:
        query["severity"] = severity.lower()
    docs = await db.gitops_drift.find(query).sort("detected_at", -1).to_list(length=None)
    return [_out(d) for d in docs]


@router.post("/drift/{drift_id}/fix")
async def fix_configuration_drift(
    drift_id: str,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Record a request to fix recorded drift."""
    drift = await _get_owned(db.gitops_drift, current_user, drift_id, "Drift record")
    await db.gitops_drift.find_one_and_update(
        _owned(current_user, _id=drift_id),
        {"$set": {"fix_status": "requested", "fix_requested_at": _now()}},
    )
    deployment = await _record_deployment(
        db, current_user, kind="drift_fix", drift_id=drift_id, application_id=drift.get("application_id"),
    )
    return {"fix_id": deployment["_id"], "drift_id": drift_id, "status": deployment["status"], "message": NOT_EXECUTED_NOTE}


# ==================== ANALYTICS & HEALTH (computed from stored data) ====================

def _count_by(docs: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for d in docs:
        value = d.get(key) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return counts


@router.get("/analytics")
async def get_gitops_analytics(
    db: DatabaseDep,
    timeframe: str = Query("30d", pattern=r"^\d{1,3}d$"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    since = (datetime.utcnow() - timedelta(days=int(timeframe[:-1]))).isoformat()
    owned = _owned(current_user)
    repos = await db.gitops_repositories.find(owned).to_list(length=None)
    apps = await db.gitops_applications.find(owned).to_list(length=None)
    deployments = [d for d in await db.gitops_deployments.find(owned).to_list(length=None) if d["requested_at"] >= since]
    drift = await db.gitops_drift.find(owned).to_list(length=None)
    completed = sum(1 for d in deployments if d["status"] == DeploymentStatus.COMPLETED.value)
    finished = sum(1 for d in deployments if d["status"] in (DeploymentStatus.COMPLETED.value, DeploymentStatus.FAILED.value))
    return {
        "timeframe": timeframe,
        "summary": {
            "total_repositories": len(repos),
            "total_applications": len(apps),
            "healthy_applications": sum(1 for a in apps if a.get("health_status") == HealthStatus.HEALTHY.value),
            "synced_applications": sum(1 for a in apps if a.get("sync_status") == SyncStatus.SYNCED.value),
            "deployment_requests": len(deployments),
            "success_rate": round(100 * completed / finished, 1) if finished else None,
        },
        "deployments_by_kind": _count_by(deployments, "kind"),
        "deployments_by_status": _count_by(deployments, "status"),
        "sync_status_distribution": _count_by(apps, "sync_status"),
        "health_status_distribution": _count_by(apps, "health_status"),
        "drift_detection": {
            "total_drift_events": len(drift),
            "fix_requested": sum(1 for d in drift if d.get("fix_status") == "requested"),
        },
    }


@router.get("/health")
async def get_gitops_health(
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Status of the GitOps integration for the current user."""
    owned = _owned(current_user)
    pending = await db.gitops_deployments.find({**owned, "status": DeploymentStatus.PENDING.value}).to_list(length=None)
    return {
        "status": "not_connected",
        "controller": None,
        "message": NOT_EXECUTED_NOTE,
        "repositories": len(await db.gitops_repositories.find(owned).to_list(length=None)),
        "applications": len(await db.gitops_applications.find(owned).to_list(length=None)),
        "pending_requests": len(pending),
        "checked_at": _now(),
    }


# ==================== PULL REQUESTS ====================
#
# Change reviews tracked inside Infra Mind for a connected repository. They are
# not pull requests on the Git host: approving or merging one records the
# decision but does not touch the repository.

PR_NOTE = "Tracked in Infra Mind; not a pull request on the Git host, and merging does not change the repository."
# Python re, not Field(pattern=...): pydantic's Rust regex engine has no look-around
BRANCH_RE = re.compile(r"^(?!/)(?!.*\.\.)(?!.*//)[A-Za-z0-9._/-]{1,200}(?<!/)(?<!\.lock)$")


class PullRequestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=20000)
    source_branch: str
    target_branch: str = "main"

    @field_validator("source_branch", "target_branch")
    @classmethod
    def _valid_branch(cls, value: str) -> str:
        if not BRANCH_RE.match(value):
            raise ValueError("not a valid branch name")
        return value


class ReviewRequest(BaseModel):
    comment: Optional[str] = Field(default=None, max_length=5000)


class RejectRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=5000)


class MergeRequest(BaseModel):
    merge_method: Literal["merge", "squash", "rebase"] = "merge"


def _compare_url(repo: Dict[str, Any], source: str, target: str) -> str:
    """The Git host's compare view for the two branches, where the host supports one."""
    base = repo["url"].removesuffix(".git")
    if base.startswith("http") and repo.get("provider") == "github":
        return f"{base}/compare/{target}...{source}"
    if base.startswith("http") and repo.get("provider") == "gitlab":
        return f"{base}/-/compare/{target}...{source}"
    return base


def _pr_out(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = _out(doc)
    out["uuid"], out["id"] = out["id"], doc["number"]  # the frontend addresses PRs by number
    return out


async def _get_pr(db, user: User, repository_id: str, number: int) -> Dict[str, Any]:
    pr = await db.gitops_pull_requests.find_one(_owned(user, repository_id=repository_id, number=number))
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")
    return pr


def _require_open(pr: Dict[str, Any]) -> None:
    if pr["state"] != "open":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Pull request is {pr['state']}")


@router.get("/repositories/{repository_id}/pull-requests")
async def list_pull_requests(
    repository_id: str,
    db: DatabaseDep,
    state: Literal["open", "closed", "merged", "all"] = "all",
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    await _get_owned(db.gitops_repositories, current_user, repository_id, "Repository")
    query = _owned(current_user, repository_id=repository_id)
    if state != "all":
        query["state"] = state
    docs = await db.gitops_pull_requests.find(query).sort("number", -1).to_list(length=None)
    return [_pr_out(d) for d in docs]


@router.post("/repositories/{repository_id}/pull-requests", status_code=status.HTTP_201_CREATED)
async def create_pull_request(
    repository_id: str,
    pr: PullRequestCreate,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    repo = await _get_owned(db.gitops_repositories, current_user, repository_id, "Repository")
    if pr.source_branch == pr.target_branch:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source and target branch must differ")
    existing = await db.gitops_pull_requests.find(_owned(current_user, repository_id=repository_id)).to_list(length=None)
    if any(e["state"] == "open" and e["source_branch"] == pr.source_branch and e["target_branch"] == pr.target_branch
           for e in existing):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="An open pull request already exists for these branches")
    now = _now()
    doc = {
        "_id": str(uuid.uuid4()),
        "user_id": str(current_user.id),
        "repository_id": repository_id,
        "number": max((e["number"] for e in existing), default=0) + 1,
        **pr.model_dump(),
        "state": "open",
        "author": current_user.email,
        "url": _compare_url(repo, pr.source_branch, pr.target_branch),
        "checks_status": "pending",  # no CI integration reports checks
        "approvals": [],
        "files_changed": [],
        "created_at": now,
        "updated_at": now,
        "merged_at": None,
        "merge_method": None,
        "note": PR_NOTE,
    }
    await db.gitops_pull_requests.insert_one(doc)
    return _pr_out(doc)


@router.get("/repositories/{repository_id}/pull-requests/{number}")
async def get_pull_request(
    repository_id: str,
    number: int,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    return _pr_out(await _get_pr(db, current_user, repository_id, number))


async def _review(db, user: User, pr: Dict[str, Any], decision: str, comment: Optional[str]) -> Dict[str, Any]:
    _require_open(pr)
    # One current review per reviewer: a new decision replaces their earlier one
    approvals = [a for a in pr["approvals"] if a["user"] != user.email]
    approvals.append({"user": user.email, "status": decision, "comment": comment, "timestamp": _now()})
    return await db.gitops_pull_requests.find_one_and_update(
        {"_id": pr["_id"]}, {"$set": {"approvals": approvals, "updated_at": _now()}}, return_document=True,
    )


@router.post("/repositories/{repository_id}/pull-requests/{number}/approve")
async def approve_pull_request(
    repository_id: str,
    number: int,
    db: DatabaseDep,
    review: ReviewRequest = ReviewRequest(),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    pr = await _get_pr(db, current_user, repository_id, number)
    return _pr_out(await _review(db, current_user, pr, "approved", review.comment))


@router.post("/repositories/{repository_id}/pull-requests/{number}/reject")
async def reject_pull_request(
    repository_id: str,
    number: int,
    review: RejectRequest,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    pr = await _get_pr(db, current_user, repository_id, number)
    return _pr_out(await _review(db, current_user, pr, "rejected", review.comment))


@router.post("/repositories/{repository_id}/pull-requests/{number}/merge")
async def merge_pull_request(
    repository_id: str,
    number: int,
    db: DatabaseDep,
    merge: MergeRequest = MergeRequest(),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Record a pull request as merged. Refused while any reviewer has requested changes."""
    pr = await _get_pr(db, current_user, repository_id, number)
    _require_open(pr)
    rejected_by = [a["user"] for a in pr["approvals"] if a["status"] == "rejected"]
    if rejected_by:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Changes requested by {', '.join(rejected_by)}")
    now = _now()
    merged = await db.gitops_pull_requests.find_one_and_update(
        {"_id": pr["_id"]},
        {"$set": {"state": "merged", "merged_at": now, "merge_method": merge.merge_method, "updated_at": now}},
        return_document=True,
    )
    return _pr_out(merged)


# ==================== IaC TEMPLATES (persisted per user) ====================

IaCProvider = Literal["terraform", "cloudformation", "pulumi", "arm", "cdk"]
MAX_TEMPLATE_BYTES = 256 * 1024


class IaCTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    provider: IaCProvider
    language: str = Field(default="hcl", max_length=50)
    template: str = Field(min_length=1, max_length=MAX_TEMPLATE_BYTES)
    variables: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    tags: List[str] = []
    version: str = Field(default="1.0.0", max_length=50)


class IaCTemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    provider: Optional[IaCProvider] = None
    language: Optional[str] = Field(default=None, max_length=50)
    template: Optional[str] = Field(default=None, min_length=1, max_length=MAX_TEMPLATE_BYTES)
    variables: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = Field(default=None, max_length=50)


_template_out = _out


@router.get("/templates")
async def list_iac_templates(
    db: DatabaseDep,
    provider: Optional[IaCProvider] = None,
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """The current user's IaC templates, most recently updated first."""
    query: Dict[str, Any] = {"user_id": str(current_user.id)}
    if provider:
        query["provider"] = provider
    docs = await db.iac_templates.find(query).sort("updated_at", -1).to_list(length=None)
    return [_template_out(d) for d in docs]


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_iac_template(
    template: IaCTemplateCreate,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    now = datetime.utcnow().isoformat()
    doc = {
        "_id": str(uuid.uuid4()),
        "user_id": str(current_user.id),
        **template.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    await db.iac_templates.insert_one(doc)
    logger.info(f"Created IaC template {doc['_id']} for user {current_user.id}")
    return _template_out(doc)


@router.get("/templates/{template_id}")
async def get_iac_template(
    template_id: str,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    doc = await db.iac_templates.find_one({"_id": template_id, "user_id": str(current_user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return _template_out(doc)


@router.put("/templates/{template_id}")
async def update_iac_template(
    template_id: str,
    changes: IaCTemplateUpdate,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    updates = changes.model_dump(exclude_unset=True, exclude_none=True)
    updates["updated_at"] = datetime.utcnow().isoformat()
    result = await db.iac_templates.find_one_and_update(
        {"_id": template_id, "user_id": str(current_user.id)},
        {"$set": updates},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return _template_out(result)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_iac_template(
    template_id: str,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
) -> None:
    result = await db.iac_templates.delete_one({"_id": template_id, "user_id": str(current_user.id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

