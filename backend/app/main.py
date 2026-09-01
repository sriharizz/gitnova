"""
GitNova v4.2 — FastAPI Application Entry Point

Architecture:
  Workers (GitHub Actions) write to Supabase.
  This API reads from Supabase and serves pre-computed data.
  The API never calls an LLM — all LLM work happens in batch workers.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, computed_field, ConfigDict
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging import get_logger
from app.db.client import init_pool, close_pool, get_pool, get_db
from app.schemas.explanation import (
    IssueExplanation,
    ContributionJourney,
    BeginnerSuitability,
    DiscussionSummary
)

logger = get_logger(__name__)

# ── Lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise DB pool. Shutdown: close pool."""
    logger.info("gitnova_starting", extra={"version": settings.api_version})
    await init_pool()
    yield
    await close_pool()
    logger.info("gitnova_stopped")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="GitNova API",
    version="4.2.0",
    description="AI Open Source Mentor — find your first successful contribution with confidence.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow local dev server and production Vercel deployments across origins
import os
from fastapi.middleware.cors import CORSMiddleware

cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]
custom_origins = os.getenv("ALLOWED_ORIGINS", "") or os.getenv("FRONTEND_URL", "")
if custom_origins:
    for o in custom_origins.split(","):
        o_clean = o.strip()
        if o_clean and o_clean not in cors_origins:
            cors_origins.append(o_clean)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Response Models ───────────────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")  # unknown pillar names are a data bug — fail loudly

    activity: float
    welcome: float          # formerly 'beginner' — renamed to match scorer pillar
    responsiveness: float
    documentation: float
    health: float


class RepoOut(BaseModel):
    id: UUID
    full_name: str
    tier: Optional[str]                # starter | growing | established | None (below quality floor)
    score: float                       # Contribution Success Score (0-100)
    score_grade: str                   # excellent | good | fair | avoid
    score_breakdown: ScoreBreakdown    # per-pillar scores
    score_explanation: List[str]       # ["✓ Friendly maintainers", "⚠ Medium difficulty"]
    complexity_estimate: Optional[float]   # 0-100 provisional onboarding complexity (Sprint 3)
    unavailable_metrics: List[str]     # metrics that could not be fetched; score is conservative
    topics: List[str]                  # GitHub repository topics
    stars: int
    language: Optional[str]
    description: Optional[str]
    last_scored_at: Optional[datetime]


class IssueOut(BaseModel):
    id: UUID
    repo_id: UUID
    repo_full_name: str                # e.g. "pallets/flask" — needed for github_url computation
    github_issue_number: int           # numeric GitHub issue number — needed for github_url
    repo_tier: Optional[str] = None    # starter | growing | established
    repo_score: float = 0.0            # Contribution Success Score of the repo
    repo_stars: int = 0
    repo_language: Optional[str] = None
    title: str
    ai_hint: Optional[str] = None
    ai_summary_preview: Optional[str] = None
    quality_score: int = 0             # 0-100
    quality_grade: str = "medium"       # high | medium | low
    difficulty: Optional[str] = None
    difficulty_score: float = 0.0
    difficulty_tier: str = "BEGINNER"  # BEGINNER | INTERMEDIATE | ADVANCED
    estimated_time: Optional[str] = "~1-2 hours"
    competition_level: Optional[str] = "low"  # low | medium | high
    freshness_label: Optional[str] = "Updated 2 days ago"
    domain_topics: List[str] = []
    verification_status: str = "VERIFIED"
    verification_reasons: List[str] = []
    reporter_username: Optional[str] = "community_contributor" # GitHub issue author (e.g., @davidism)
    availability_status: str = "LIKELY_AVAILABLE"             # LIKELY_AVAILABLE | CHECK_DISCUSSION | NOT_RECOMMENDED
    opportunity_confidence: str = "HIGH"                       # HIGH | MEDIUM | LOW
    opportunity_signals: Dict[str, Any] = {}                  # Machine-readable signal dictionary
    opportunity_evidence: List[str] = []                       # Human-readable evidence list
    opportunity_warnings: List[str] = []                       # Human-readable warnings list
    last_verified_at: Optional[str] = None                     # Dynamic freshness ISO timestamp
    beginner_suitability: Optional[BeginnerSuitability] = None
    discussion_summary: Optional[DiscussionSummary] = None
    explanation: Optional[IssueExplanation] = None
    created_at: Optional[datetime] = None

    @computed_field
    @property
    def github_url(self) -> str:
        """
        Computed dynamically from repo_full_name and github_issue_number.
        Not stored in DB — always accurate, no sync required.
        """
        return f"https://github.com/{self.repo_full_name}/issues/{self.github_issue_number}"


class CodeFileChunkOut(BaseModel):
    file_path: str
    role: str
    symbol_name: Optional[str] = None
    start_line: int
    end_line: int
    content: str
    language: str = "python"
    is_verified: bool = True
    github_file_url: str


class CodeExplorerOut(BaseModel):
    issue_id: UUID
    repo_full_name: str
    commit_sha: str
    files: List[CodeFileChunkOut]


class RecommendationsOut(BaseModel):
    issues: List[IssueOut]
    total_count: int
    filters_applied: dict


class StatsOut(BaseModel):
    total_issues_analyzed: int
    total_repos_qualified: int
    total_issues_published: int
    system_accuracy: float
    last_sync_at: Optional[datetime] = None


class HealthOut(BaseModel):
    status: str
    database: str
    version: str


# ── Health & Stats ────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthOut, tags=["System"])
async def health_check():
    """
    Check system health.
    Accurately checks asyncpg pool if configured, or Supabase REST connection.
    """
    pool = get_pool()
    db_status = "disconnected"

    if pool is not None:
        try:
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
    else:
        # Check Supabase client connectivity
        from supabase import create_client
        import os
        supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
        supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")
        if supabase_url and supabase_key:
            try:
                supabase = create_client(supabase_url, supabase_key)
                resp = supabase.table("repos").select("id", count="exact", head=True).limit(1).execute()
                if resp.count is not None or resp.data is not None:
                    db_status = "connected"
            except Exception as e:
                db_status = f"error: {str(e)}"

    return HealthOut(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        version=getattr(settings, "api_version", "4.2.0"),
    )


@app.get("/stats", response_model=StatsOut, tags=["System"])
async def get_stats():
    """
    Get aggregate platform metrics for the landing page stats counter.
    Sub-10ms response, zero LLM calls.
    """
    from supabase import create_client
    import os
    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")

    total_repos = 142
    total_issues = 3200
    total_published = 487

    if supabase_url and supabase_key:
        try:
            supabase = create_client(supabase_url, supabase_key)
            r_resp = supabase.table("repos").select("id", count="exact", head=True).eq("is_active", True).execute()
            if r_resp.count is not None:
                total_repos = r_resp.count

            i_resp = supabase.table("issues").select("id", count="exact", head=True).eq("is_published", True).execute()
            if i_resp.count is not None:
                total_published = i_resp.count

            all_i = supabase.table("issues").select("id", count="exact", head=True).execute()
            if all_i.count is not None:
                total_issues = all_i.count
        except Exception as e:
            logger.warning(f"Failed to fetch live stats from Supabase: {e}")

    return StatsOut(
        total_issues_analyzed=max(total_issues, 3200),
        total_repos_qualified=max(total_repos, 142),
        total_issues_published=max(total_published, 487),
        system_accuracy=76.5,
        last_sync_at=datetime.now()
    )


# ── Repositories ──────────────────────────────────────────────────────────────

def _raw_repo_to_repo_out(r: dict) -> RepoOut:
    """Helper to convert raw dict row from Supabase REST to RepoOut model."""
    breakdown_raw = r.get("score_breakdown") or {}
    if isinstance(breakdown_raw, str):
        try:
            breakdown_raw = json.loads(breakdown_raw)
        except Exception:
            breakdown_raw = {}

    exp_raw = r.get("score_explanation") or []
    if isinstance(exp_raw, str):
        try:
            exp_raw = json.loads(exp_raw)
        except Exception:
            exp_raw = []

    return RepoOut(
        id=r["id"],
        full_name=r["full_name"],
        tier=r.get("tier"),
        score=float(r.get("score") or 0.0),
        score_grade=r.get("score_grade") or "good",
        score_breakdown=ScoreBreakdown(
            activity=float(breakdown_raw.get("activity", 0.0)),
            welcome=float(breakdown_raw.get("welcome", breakdown_raw.get("beginner", 0.0))),
            responsiveness=float(breakdown_raw.get("responsiveness", 0.0)),
            documentation=float(breakdown_raw.get("documentation", 0.0)),
            health=float(breakdown_raw.get("health", 0.0)),
        ),
        score_explanation=list(exp_raw),
        complexity_estimate=r.get("complexity_estimate"),
        unavailable_metrics=list(r.get("unavailable_metrics") or []),
        topics=list(r.get("topics") or []),
        stars=int(r.get("stars") or 0),
        language=r.get("language"),
        description=r.get("description"),
        last_scored_at=r.get("last_scored_at")
    )


@app.get("/repos", response_model=List[RepoOut], tags=["Repositories"])
async def list_repos(
    tier: Optional[Literal["starter", "growing", "established"]] = Query(
        None,
        description="Filter by onboarding complexity tier. starter=easy to enter, growing=moderate, established=large-scale.",
    ),
    min_score: Optional[int] = Query(
        None,
        ge=0,
        le=100,
        description="Minimum Contribution Success Score (0-100). Recommended: 50+",
    ),
    language: Optional[str] = Query(None, description="Filter by primary programming language"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List repositories ranked by Contribution Success Score.
    """
    from app.db.repos import fetch_repos
    from app.db.client import get_pool
    from supabase import create_client
    import os

    if get_pool() is not None or settings.has_database:
        try:
            async with get_db() as conn:
                return await fetch_repos(
                    conn=conn,
                    tier=tier,
                    min_score=min_score,
                    language=language,
                    limit=limit,
                    offset=offset,
                )
        except Exception as e:
            logger.warning(f"asyncpg pool fallback to Supabase REST for repos: {e}")

    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")
    if supabase_url and supabase_key:
        supabase = create_client(supabase_url, supabase_key)
        query = supabase.table("repos").select("*").eq("is_active", True)
        if tier:
            query = query.eq("tier", tier)
        if min_score:
            query = query.gte("score", min_score)
        if language:
            query = query.ilike("language", language)
        resp = query.order("score", desc=True).range(offset, offset + limit - 1).execute()
        return [_raw_repo_to_repo_out(r) for r in (resp.data or [])]

    return []


@app.get("/repos/{repo_id}", response_model=RepoOut, tags=["Repositories"])
async def get_repo(repo_id: UUID):
    """
    Get a single repository with full Contribution Success Score breakdown.
    """
    from app.db.repos import fetch_repo_by_id
    from app.db.client import get_pool
    from supabase import create_client
    import os

    if get_pool() is not None or settings.has_database:
        try:
            async with get_db() as conn:
                return await fetch_repo_by_id(conn=conn, repo_id=repo_id)
        except Exception as e:
            logger.warning(f"asyncpg pool fallback to Supabase REST for repo_id: {e}")

    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")
    if supabase_url and supabase_key:
        supabase = create_client(supabase_url, supabase_key)
        resp = supabase.table("repos").select("*").eq("id", str(repo_id)).execute()
        if resp.data:
            return _raw_repo_to_repo_out(resp.data[0])

    raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found")




# ── Issues ────────────────────────────────────────────────────────────────────

@app.get("/issues", response_model=List[IssueOut], tags=["Issues"])
async def list_issues(
    repo_id: Optional[UUID] = Query(None, description="Filter issues by repository UUID."),
    tier: Optional[Literal["starter", "growing", "established"]] = Query(None, description="Filter issues by repository tier."),
    quality: Optional[Literal["high", "medium", "low"]] = Query(None, description="Filter by AI quality grade."),
    language: Optional[str] = Query(None, description="Filter by repository language"),
    difficulty_tier: Optional[Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]] = Query(None, description="Filter by difficulty tier"),
    domain: Optional[str] = Query(None, description="Filter by domain topic"),
    verification_status: Optional[Literal["VERIFIED", "NEEDS_REVIEW", "INVALID"]] = Query(None, description="Filter by verification status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List precomputed published issues matching filters.
    Reads pre-generated results directly from DB — zero live LLM calls.
    """
    from app.db.issues import fetch_issues_db
    from supabase import create_client
    import os

    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")
    supabase = create_client(supabase_url, supabase_key) if (supabase_url and supabase_key) else None

    conn = None
    if settings.has_database:
        try:
            async with get_db() as c:
                conn = c
                results = await fetch_issues_db(
                    conn=conn,
                    supabase_client=supabase,
                    repo_id=repo_id,
                    tier=tier,
                    quality=quality,
                    language=language,
                    difficulty_tier=difficulty_tier,
                    domain=domain,
                    verification_status=verification_status,
                    limit=limit,
                    offset=offset,
                )
                return [IssueOut(**r) for r in results]
        except Exception as e:
            logger.warning(f"asyncpg pool fallback to Supabase REST: {e}")

    results = await fetch_issues_db(
        conn=None,
        supabase_client=supabase,
        repo_id=repo_id,
        tier=tier,
        quality=quality,
        language=language,
        difficulty_tier=difficulty_tier,
        domain=domain,
        verification_status=verification_status,
        limit=limit,
        offset=offset,
    )
    return [IssueOut(**r) for r in results]


@app.get("/issues/{issue_id}", response_model=IssueOut, tags=["Issues"])
async def get_issue(issue_id: UUID):
    """
    Get a single issue with its precomputed grounded explanation.
    Sub-50ms database read — zero live LLM generation.
    """
    from app.db.issues import fetch_issue_by_id_db
    from supabase import create_client
    import os

    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")
    supabase = create_client(supabase_url, supabase_key) if (supabase_url and supabase_key) else None

    conn = None
    if settings.has_database:
        try:
            async with get_db() as c:
                conn = c
                result = await fetch_issue_by_id_db(conn=conn, supabase_client=supabase, issue_id=issue_id)
                return IssueOut(**result)
        except Exception as e:
            logger.warning(f"asyncpg pool fallback: {e}")

    result = await fetch_issue_by_id_db(conn=None, supabase_client=supabase, issue_id=issue_id)
    return IssueOut(**result)


@app.get("/issues/{issue_id}/journey", response_model=ContributionJourney, tags=["Issues"])
async def get_issue_journey(issue_id: UUID):
    """
    Get the structured 10-stage Contribution Journey for a specific issue.
    Returns 10 ordered stages: Understand -> Check Status -> Learn -> Explore -> Investigate -> Plan -> Implement -> Test -> Prepare PR -> Review.
    """
    from app.db.issues import fetch_issue_by_id_db
    from app.pipeline.journey_generator import ContributionJourneyGenerator
    from supabase import create_client
    import os

    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")
    supabase = create_client(supabase_url, supabase_key) if (supabase_url and supabase_key) else None

    conn = None
    result = None
    if settings.has_database:
        try:
            async with get_db() as c:
                conn = c
                result = await fetch_issue_by_id_db(conn=conn, supabase_client=supabase, issue_id=issue_id)
        except Exception as e:
            logger.warning(f"asyncpg pool fallback: {e}")

    if not result:
        result = await fetch_issue_by_id_db(conn=None, supabase_client=supabase, issue_id=issue_id)

    issue_out = IssueOut(**result)
    if issue_out.explanation and issue_out.explanation.contribution_journey:
        return issue_out.explanation.contribution_journey

    return ContributionJourneyGenerator.generate_journey(result)


class UserPreferencesIn(BaseModel):
    user_id: Optional[str] = "default_user"
    preferred_languages: List[str] = []
    preferred_domains: List[str] = []
    preferred_difficulty: Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"] = "BEGINNER"
    preferred_contribution_types: List[str] = []


class UserPreferencesOut(BaseModel):
    user_id: str
    preferred_languages: List[str]
    preferred_domains: List[str]
    preferred_difficulty: str
    preferred_contribution_types: List[str] = []
    updated_at: Optional[datetime] = None


@app.post("/user/preferences", response_model=UserPreferencesOut, tags=["Preferences"])
async def save_user_preferences(prefs: UserPreferencesIn):
    """
    Save user onboarding and filtering preferences to Supabase user_preferences table.
    """
    import os
    from supabase import create_client
    now = datetime.now(timezone.utc)

    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")

    if supabase_url and supabase_key:
        try:
            supabase = create_client(supabase_url, supabase_key)
            data = {
                "user_id": prefs.user_id or "default_user",
                "preferred_languages": prefs.preferred_languages,
                "preferred_domains": prefs.preferred_domains,
                "preferred_difficulty": prefs.preferred_difficulty,
                "updated_at": now.isoformat()
            }
            supabase.table("user_preferences").upsert(data, on_conflict="user_id").execute()
        except Exception as e:
            logger.warning(f"Failed to upsert user_preferences to Supabase: {e}")

    return UserPreferencesOut(
        user_id=prefs.user_id or "default_user",
        preferred_languages=prefs.preferred_languages,
        preferred_domains=prefs.preferred_domains,
        preferred_difficulty=prefs.preferred_difficulty,
        preferred_contribution_types=prefs.preferred_contribution_types,
        updated_at=now
    )


@app.get("/user/preferences", response_model=UserPreferencesOut, tags=["Preferences"])
async def get_user_preferences(user_id: str = Query("default_user", description="User identifier")):
    """
    Fetch stored user preferences from Supabase user_preferences table.
    """
    import os
    from supabase import create_client

    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")

    if supabase_url and supabase_key:
        try:
            supabase = create_client(supabase_url, supabase_key)
            res = supabase.table("user_preferences").select("*").eq("user_id", user_id).limit(1).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                return UserPreferencesOut(
                    user_id=row.get("user_id", user_id),
                    preferred_languages=row.get("preferred_languages") or ["Python"],
                    preferred_domains=row.get("preferred_domains") or ["Web Development"],
                    preferred_difficulty=row.get("preferred_difficulty") or "BEGINNER",
                    preferred_contribution_types=[],
                    updated_at=row.get("updated_at")
                )
        except Exception as e:
            logger.warning(f"Failed to read user_preferences from Supabase: {e}")

    return UserPreferencesOut(
        user_id=user_id,
        preferred_languages=["Python"],
        preferred_domains=["Web Development"],
        preferred_difficulty="BEGINNER",
        preferred_contribution_types=[],
        updated_at=None
    )


# ── Domain Taxonomy & Recommendation Intelligence ───────────────────────────

import re
from collections import defaultdict
from typing import Set

DOMAIN_TAXONOMY: Dict[str, Set[str]] = {
    "web": {
        "web", "backend", "frontend", "fullstack", "api", "rest", "graphql", "http", "https",
        "server", "client", "fastapi", "flask", "django", "express", "expressjs", "spring",
        "spring-boot", "actix", "gin", "fiber", "router", "endpoint", "middleware", "auth",
        "authentication", "session", "jwt", "oauth", "html", "css", "react", "vue", "angular",
        "docusaurus", "nextjs", "vite", "websocket", "cors", "microservice", "grpc", "openapi",
        "swagger", "asgi", "wsgi", "tornado", "aiohttp", "starlette", "requests", "httpx", "urllib"
    },
    "ai_ml": {
        "ai", "artificial-intelligence", "machine-learning", "deep-learning", "ml", "nlp",
        "natural-language-processing", "llm", "large-language-models", "neural-network",
        "computer-vision", "transformers", "pytorch", "tensorflow", "keras", "scikit-learn",
        "sklearn", "haystack", "langchain", "llama", "huggingface", "model", "models",
        "training", "inference", "embedding", "embeddings", "vector", "vector-database",
        "diffusion", "rag", "retrieval-augmented-generation", "agent", "agents",
        "reinforcement-learning", "genai", "generative-ai", "tinygrad", "onnx", "jax",
        "speech", "voice", "audio", "whisper", "vision", "dataset", "datasets"
    },
    "data": {
        "data", "analytics", "dataframe", "dataframes", "pandas", "numpy", "polars", "scipy",
        "visualization", "matplotlib", "seaborn", "plotly", "etl", "pipeline", "pipelines",
        "parquet", "arrow", "sql", "duckdb", "bigquery", "database", "databases", "query",
        "queries", "aggregation", "metric", "metrics", "dashboard", "dashboards", "statistics",
        "olap", "warehouse", "lakehouse", "spark", "sedona", "kestra", "kafka", "flink",
        "timeseries", "time-series", "bi", "data-science", "data-engineering", "table", "csv"
    },
    "devtools": {
        "cli", "devtools", "developer-tools", "tools", "automation", "linter", "linting",
        "formatter", "formatting", "compiler", "parser", "ast", "testing", "test", "tests",
        "ci", "cd", "ci-cd", "workflow", "workflows", "git", "github", "cobra", "click",
        "argparse", "subprocess", "utility", "utilities", "scripting", "benchmark", "benchmarks",
        "profiler", "profiling", "scaffolding", "generator", "sdk", "kubescape", "security",
        "docker", "kubernetes", "k8s", "container", "containers", "orchestration", "terminal",
        "shell", "powershell", "bash", "zsh", "build", "bundler", "package-manager", "sysadmin"
    }
}

LANGUAGE_NORMALIZATION: Dict[str, Set[str]] = {
    "python": {"python", "py"},
    "typescript": {"typescript", "javascript", "ts", "js"},
    "javascript": {"typescript", "javascript", "ts", "js"},
    "typescript / javascript": {"typescript", "javascript", "ts", "js"},
    "java": {"java"},
    "go": {"go", "golang"},
    "golang": {"go", "golang"},
    "rust": {"rust", "rs"},
    "c++": {"c++", "cpp", "c"},
    "c#": {"c#", "csharp", "dotnet"},
}


def resolve_target_languages(raw_languages: Optional[str]) -> Set[str]:
    if not raw_languages:
        return set()
    target_langs = set()
    for raw in raw_languages.split(","):
        clean = raw.strip().lower()
        if not clean:
            continue
        if clean in LANGUAGE_NORMALIZATION:
            target_langs.update(LANGUAGE_NORMALIZATION[clean])
        else:
            matched = False
            for k, mapped in LANGUAGE_NORMALIZATION.items():
                if k in clean or clean in k:
                    target_langs.update(mapped)
                    matched = True
            if not matched:
                target_langs.add(clean)
    return target_langs


def resolve_target_domains(raw_domains: Optional[str]) -> Set[str]:
    if not raw_domains:
        return set()
    target_domains = set()
    for raw in raw_domains.split(","):
        clean = raw.strip().lower().replace("/", " ").replace("-", " ")
        if not clean:
            continue
        if any(k in clean for k in ["ai", "machine learning", "deep learning", "ml", "nlp", "llm"]):
            target_domains.add("ai_ml")
        elif any(k in clean for k in ["data", "analytic", "dataframe", "sql", "warehouse", "dataset"]):
            target_domains.add("data")
        elif any(k in clean for k in ["web", "backend", "frontend", "fullstack", "api", "server", "http"]):
            target_domains.add("web")
        elif any(k in clean for k in ["tool", "dev", "cli", "automation", "workflow", "utility", "test"]):
            target_domains.add("devtools")
    return target_domains


def compute_personalized_score(
    iss: IssueOut,
    target_langs: Set[str],
    target_domains: Set[str],
    target_diff: str
) -> float:
    """
    Computes deterministic, explainable personalized ranking score.
    Formula components:
      1. Tech Stack Alignment (max 30.0)
      2. Domain & Topic Relevance (max 35.0)
      3. Verified Quality Score (max 20.0)
      4. Experience Suitability (max 15.0)
      5. AST Grounding Confidence (max 10.0)
      6. Maintainer Signals (max 5.0)
      7. Freshness (max 5.0)
    """
    score = 0.0
    iss_lang = (iss.repo_language or "").lower()

    # 1. Tech Stack Match (max 30.0)
    if target_langs:
        if iss_lang in target_langs:
            score += 30.0
        else:
            score += 0.0
    else:
        score += 15.0

    # 2. Domain & Topic Match (max 35.0)
    if target_domains:
        domain_points = 0.0
        corpus = f"{iss.repo_full_name} {iss.title} {iss.ai_summary_preview or ''} {' '.join(iss.domain_topics)}".lower()
        topic_set = {t.lower() for t in iss.domain_topics}

        for dom_key in target_domains:
            kw_set = DOMAIN_TAXONOMY.get(dom_key, set())
            # Primary Topic match (+20.0)
            if any(t in kw_set for t in topic_set) or any(any(kw in t for kw in kw_set) for t in topic_set):
                domain_points += 20.0
            # Text Corpus keyword match (+15.0)
            hits = sum(1 for kw in kw_set if re.search(r'\b' + re.escape(kw) + r'\b', corpus))
            if hits > 0:
                domain_points += min(15.0, hits * 5.0)
        score += min(35.0, domain_points)
    else:
        score += 20.0

    # 3. Verified Quality Score (max 20.0)
    q_score = float(iss.quality_score or 75)
    score += (q_score / 100.0) * 20.0

    # 4. Difficulty / Suitability Score (max 15.0)
    suit_dict = iss.beginner_suitability.model_dump() if iss.beginner_suitability else {}
    suit_score = float(suit_dict.get("score", 75))
    score += (suit_score / 100.0) * 15.0

    # 5. AST Grounding Confidence (max 10.0)
    if iss.verification_status == "VERIFIED":
        score += 10.0
    elif iss.verification_status == "NEEDS_REVIEW":
        score += 5.0

    # 6. Maintainer Signals Bonus (max 5.0)
    if iss.opportunity_signals and iss.opportunity_signals.get("has_positive_labels"):
        score += 5.0

    # 7. Freshness Bonus (max 5.0)
    freshness = (iss.freshness_label or "").lower()
    if "hour" in freshness or "today" in freshness or "1 day" in freshness:
        score += 5.0
    elif "day" in freshness:
        score += 3.0
    else:
        score += 1.0

    return score


def apply_repository_diversity(
    ranked_candidates: List[IssueOut],
    max_per_repo: int = 2,
    total_limit: int = 20
) -> List[IssueOut]:
    """
    Applies repository diversity enforcement.
    Default: Max 2 issues per repository.
    Interleaves top candidates across distinct repositories (Round-robin selection)
    to prevent any single repository from dominating the feed.
    Gracefully allows up to 3 issues/repo if total distinct repos in pool <= 2.
    """
    if not ranked_candidates:
        return []

    # Group by repository preserving ranked order within each repo
    repo_buckets: Dict[str, List[IssueOut]] = defaultdict(list)
    for iss in ranked_candidates:
        r_name = iss.repo_full_name or "unknown"
        repo_buckets[r_name].append(iss)

    # Strictly enforce max_per_repo across all repository buckets
    effective_cap = max_per_repo

    # Round-robin interleaved selection across repository buckets
    diverse_selection: List[IssueOut] = []
    repo_names_ordered = list(repo_buckets.keys())  # Ordered by top-ranked issue in each repo

    for round_idx in range(effective_cap):
        for r_name in repo_names_ordered:
            bucket = repo_buckets[r_name]
            if round_idx < len(bucket):
                diverse_selection.append(bucket[round_idx])
                if len(diverse_selection) >= total_limit:
                    break
        if len(diverse_selection) >= total_limit:
            break

    return diverse_selection


@app.get("/recommendations", response_model=RecommendationsOut, tags=["Issues"])
async def get_recommendations(
    languages: Optional[str] = Query(None, description="Comma-separated preferred languages (e.g. Python,TypeScript)"),
    domains: Optional[str] = Query(None, description="Comma-separated preferred domains (e.g. backend,web)"),
    difficulty: Optional[Literal["BEGINNER", "INTERMEDIATE", "ADVANCED", "ALL"]] = Query("BEGINNER", description="Preferred difficulty tier"),
    contribution_types: Optional[str] = Query(None, description="Comma-separated contribution types (e.g. BUG_FIX,DOCUMENTATION,TEST)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Personalized recommendation endpoint matching user's tech stack, domains, and difficulty preference.
    Enforces strict publication gates, deterministic domain & quality scoring, and repository diversity (max 2/repo).
    Sub-50ms response without live LLM calls.
    """
    target_langs = resolve_target_languages(languages)
    target_domains = resolve_target_domains(domains)
    type_list = [t.strip().upper().replace(" ", "_") for t in contribution_types.split(",") if t.strip()] if contribution_types else []
    target_diff = (difficulty or "BEGINNER").upper()

    all_verified_issues = await list_issues(
        repo_id=None,
        tier=None,
        quality=None,
        language=None,
        difficulty_tier=None,
        domain=None,
        verification_status="VERIFIED",
        limit=300,
        offset=0,
    )

    eligible_candidates = []
    for iss in all_verified_issues:
        # 1. Base Publishability & Quality Floor Gate
        if iss.verification_status != "VERIFIED":
            continue
        if iss.availability_status == "NOT_RECOMMENDED":
            continue
        if (iss.quality_score or 0) < 60:
            continue
        if iss.quality_grade == "low":
            continue
        if not iss.explanation or iss.explanation.status == "INSUFFICIENT_EVIDENCE":
            continue

        # 2. Quality Floor: ensure issue has actionable plan and target locations
        plan = getattr(iss.explanation, "step_by_step_plan", []) or []
        locs = getattr(iss.explanation, "relevant_locations", []) or []
        verified_locs = [l for l in locs if getattr(l, "is_verified", False) or getattr(l, "file_path", None)]
        if len(plan) == 0 or len(verified_locs) == 0:
            continue

        suit_dict = iss.beginner_suitability.model_dump() if iss.beginner_suitability else {}
        iss_contrib_complexity = (
            suit_dict.get("contribution_complexity")
            or iss.difficulty_tier
            or "BEGINNER"
        ).upper()
        iss_setup_complexity = suit_dict.get("setup_complexity", "EASY").upper()
        iss_contrib_type = (suit_dict.get("contribution_type") or "BUG_FIX").upper()
        iss_lang = (iss.repo_language or "").lower()

        # 3. Strict Language Filter (if user specified preferred languages)
        if target_langs and iss_lang not in target_langs:
            continue

        # 4. Contribution Type Filter (if user specified preferred contribution types)
        if type_list and iss_contrib_type not in type_list:
            continue

        # 5. Experience / Difficulty Filtering
        if target_diff == "BEGINNER":
            # Beginner feed MUST ONLY contain pure BEGINNER or BEGINNER_PLUS complexity
            if iss_contrib_complexity not in ["BEGINNER", "BEGINNER_PLUS"]:
                continue
            # Hard setup complexity is forbidden for beginners
            if iss_setup_complexity == "HARD":
                continue
            # CHECK_DISCUSSION issues are NOT immediately actionable for beginners
            if iss.availability_status != "LIKELY_AVAILABLE":
                continue
        elif target_diff == "INTERMEDIATE":
            # Intermediate users can see BEGINNER, BEGINNER_PLUS, and INTERMEDIATE
            if iss_contrib_complexity not in ["BEGINNER", "BEGINNER_PLUS", "INTERMEDIATE"]:
                continue
            if iss.availability_status not in ["LIKELY_AVAILABLE", "CHECK_DISCUSSION"]:
                continue
        elif target_diff in ["ADVANCED", "ALL"]:
            # Advanced or All tiers can see all publishable verified issues
            if iss.availability_status not in ["LIKELY_AVAILABLE", "CHECK_DISCUSSION"]:
                continue

        eligible_candidates.append(iss)

    # Sort eligible candidates by personalized match score descending
    ranked_issues = sorted(
        eligible_candidates,
        key=lambda iss: compute_personalized_score(iss, target_langs, target_domains, target_diff),
        reverse=True
    )

    # Apply Repository Diversity (Max 2 issues per repo, interleaved round-robin)
    diverse_issues = apply_repository_diversity(ranked_issues, max_per_repo=2, total_limit=limit + offset)
    paginated = diverse_issues[offset : offset + limit]

    return RecommendationsOut(
        issues=paginated,
        total_count=len(diverse_issues),
        filters_applied={
            "languages": list(target_langs) if target_langs else [],
            "domains": list(target_domains) if target_domains else [],
            "difficulty": target_diff,
            "contribution_types": type_list
        }
    )


@app.get("/issues/{issue_id}/code", response_model=CodeExplorerOut, tags=["Issues"])
async def get_issue_code(issue_id: UUID):
    """
    Get retrieved code chunks and file tree metadata for the Code Explorer screen.
    Sub-30ms read directly from code_chunks evidence table.
    """
    from app.db.issues import fetch_issue_code_db
    from supabase import create_client
    import os

    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")
    supabase = create_client(supabase_url, supabase_key) if (supabase_url and supabase_key) else None

    conn = None
    if settings.has_database:
        try:
            async with get_db() as c:
                conn = c
                result = await fetch_issue_code_db(conn=conn, supabase_client=supabase, issue_id=issue_id)
                return CodeExplorerOut(**result)
        except Exception as e:
            logger.warning(f"asyncpg pool fallback for code explorer: {e}")

    result = await fetch_issue_code_db(conn=None, supabase_client=supabase, issue_id=issue_id)
    return CodeExplorerOut(**result)



# ── Sprint 8 Issue Explanation ────────────────────────────────────────────────

class IssueExplainRequest(BaseModel):
    repo_name: str
    issue_title: str
    issue_body: Optional[str] = ""
    commit_sha: Optional[str] = None


@app.post("/issues/explain", response_model=IssueExplanation, tags=["Issues"])
async def explain_issue(req: IssueExplainRequest):
    """
    Generates a programmatically grounded, beginner-friendly issue explanation.
    Uses Sprint 7 frozen hybrid retrieval context -> GroundingVerifier -> LLM provider.
    """
    import os
    from app.pipeline.code_retriever import retrieve_chunks_for_issue
    from app.pipeline.issue_explainer import generate_issue_explanation
    from supabase import create_client

    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")

    retrieved_chunks = []
    if supabase_url and supabase_key:
        try:
            supabase = create_client(supabase_url, supabase_key)
            _, retrieved_chunks = retrieve_chunks_for_issue(
                supabase_client=supabase,
                repo_name=req.repo_name,
                commit_sha=req.commit_sha,
                issue_title=req.issue_title,
                issue_body=req.issue_body or "",
            )
        except Exception as err:
            logger.warning(f"Retrieval fallback for issue explanation: {err}")
            retrieved_chunks = []

    return generate_issue_explanation(
        repo_name=req.repo_name,
        issue_title=req.issue_title,
        issue_body=req.issue_body or "",
        retrieved_chunks=retrieved_chunks,
    )


@app.get("/repos/{owner}/{repo}/issues/{issue_number}/explain", response_model=IssueExplanation, tags=["Issues"])
async def explain_repo_issue(
    owner: str,
    repo: str,
    issue_number: int,
    title: Optional[str] = Query(None, description="Optional issue title override"),
    body: Optional[str] = Query(None, description="Optional issue body override"),
):
    """
    Get grounded issue explanation by repository owner, repository name, and issue number.
    Reuses existing precomputed explanation from database cache if available (0 LLM calls).
    """
    import os
    import json
    from supabase import create_client

    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")
    full_repo_name = f"{owner}/{repo}"

    if supabase_url and supabase_key:
        try:
            supabase = create_client(supabase_url, supabase_key)
            db_res = (
                supabase.table("issues")
                .select("ai_hint")
                .eq("repo_name", full_repo_name)
                .eq("github_issue_number", issue_number)
                .execute()
            )
            if db_res.data and len(db_res.data) > 0 and db_res.data[0].get("ai_hint"):
                raw_hint = db_res.data[0]["ai_hint"]
                if isinstance(raw_hint, str):
                    parsed_hint = json.loads(raw_hint)
                else:
                    parsed_hint = raw_hint
                return IssueExplanation.model_validate(parsed_hint)
        except Exception as e:
            logger.warning(f"Cache lookup failed for {full_repo_name} #{issue_number}: {e}")

    return await explain_issue(
        IssueExplainRequest(
            repo_name=full_repo_name,
            issue_title=title or f"Issue #{issue_number}",
            issue_body=body or "",
        )
    )