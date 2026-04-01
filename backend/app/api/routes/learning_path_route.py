"""
FastAPI route — Learning Path Recommendations
Phase 2 | FEAT-2.4.2 | Skill Barter Marketplace

Drop this file into:
    backend/app/api/routes/learning_path.py

Then register in main.py:
    from app.api.routes.learning_path import router as learning_path_router
    app.include_router(learning_path_router, prefix="/api", tags=["Learning Path"])
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
import os

from app.services.learning_path_engine import LearningPathEngine

router = APIRouter()

# ── Engine singleton — loaded once at startup ──────────────────────────────────
TAXONOMY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "skill_taxonomy.json"
)
_engine: LearningPathEngine | None = None


def get_engine() -> LearningPathEngine:
    global _engine
    if _engine is None:
        _engine = LearningPathEngine(TAXONOMY_PATH)
    return _engine


# ── Response schemas ───────────────────────────────────────────────────────────

class SkillEntry(BaseModel):
    skill_name: str
    skill_category: str | None
    taxonomy_level: int | None
    description: str
    reason: str


class LearningPathResponse(BaseModel):
    skill: str
    user_level: str
    found_as: dict
    prerequisites: list[SkillEntry]
    complementary: list[SkillEntry]
    next_level: list[SkillEntry]


class SkillInfoResponse(BaseModel):
    skill: str
    metadata: dict
    parents: list[str]
    children: list[str]
    siblings: list[str]


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get(
    "/learning-path",
    response_model=LearningPathResponse,
    summary="Get learning path recommendations for a skill",
    description="""
Returns structured learning path with:
- **prerequisites**: skills you should know first (depth varies by level)
- **complementary**: sibling/cousin skills that pair well
- **next_level**: skills to learn after mastering this one

`user_level` affects prerequisite depth:
- `beginner` → shows up to 3 ancestor levels
- `intermediate` → shows up to 2 ancestor levels
- `advanced` → shows only direct parent
- `expert` → no prerequisites listed
    """,
)
async def get_learning_path(
    skill: str = Query(..., description="Skill name (e.g. 'Machine Learning', 'Docker', 'React')"),
    user_level: Literal["beginner", "intermediate", "advanced", "expert"] = Query(
        "intermediate", description="User's current expertise level"
    ),
):
    engine = get_engine()
    result = engine.get_learning_path(skill, user_level)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get(
    "/skills/info",
    response_model=SkillInfoResponse,
    summary="Get taxonomy info for a specific skill",
    description="Returns a skill's metadata, parent, children, and siblings in the taxonomy graph.",
)
async def get_skill_info(
    skill: str = Query(..., description="Skill name to look up"),
):
    engine = get_engine()
    result = engine.get_skill_info(skill)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get(
    "/skills/all",
    summary="List all skills available in the taxonomy",
    description="Returns a flat list of all 198 skills with domain and level info.",
)
async def list_all_skills():
    engine = get_engine()
    return {
        "total": len(engine.list_all_skills()),
        "skills": engine.list_all_skills(),
    }