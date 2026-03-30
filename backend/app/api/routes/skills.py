"""
Skills API Routes
FEAT-1.4.1 – 1.4.4 : skill CRUD
FEAT-1.4.7          : skill search
FEAT-2.4.1          : skill suggestions
FEAT-2.4.2          : learning path recommendations  ← NEW
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.services.skill_normalization_service import get_skill_normalization_service
from backend.app.services.learning_path_service import get_learning_path_service   # FEAT-2.4.2
from backend.app.api.routes.matching import get_current_user_id

router = APIRouter(prefix="/skills", tags=["skills"])


# ------------------------------------------------------------------ #
# Request / Response models                                            #
# ------------------------------------------------------------------ #

class AddSkillRequest(BaseModel):
    skill_name: str = Field(..., min_length=3, max_length=100)
    skill_type: str = Field(..., pattern="^(offer|want)$")
    proficiency_level: Optional[str] = Field(
        None, pattern="^(beginner|intermediate|advanced|expert)$"
    )
    category: Optional[str] = Field(None, max_length=50)


class SkillResponse(BaseModel):
    user_skills_id: int
    skill_graph_id: int
    skill_name: str
    skill_type: str
    proficiency_level: Optional[str]
    skill_category: Optional[str]
    popularity_score: float


class UserSkillsResponse(BaseModel):
    skills_offered: List[SkillResponse]
    skills_wanted: List[SkillResponse]
    total_skills: int


class SkillSearchResult(BaseModel):
    skill_graph_id: int
    skill_name: str
    skill_category: Optional[str]
    popularity_score: float
    similarity: float


class LearningPathSkill(BaseModel):
    """Single skill entry inside a learning path section."""
    skill_name: str
    skill_category: Optional[str]
    similarity: float
    reason: str


class LearningPathResponse(BaseModel):
    """FEAT-2.4.2 response model."""
    skill: str
    user_level: Optional[str]
    prerequisites: List[LearningPathSkill]
    complementary: List[LearningPathSkill]
    next_level: List[LearningPathSkill]


# ------------------------------------------------------------------ #
# Endpoints                                                            #
# ------------------------------------------------------------------ #

@router.post("/", response_model=SkillResponse, status_code=201)
async def add_skill(
    request: AddSkillRequest,
    current_user_id: int = Depends(get_current_user_id)
):
    """Add a skill to user's profile (FEAT-1.4.1)."""
    try:
        skill_service = get_skill_normalization_service()
        result = skill_service.add_user_skill(
            user_id=current_user_id,
            skill_name=request.skill_name,
            skill_type=request.skill_type,
            proficiency_level=request.proficiency_level,
            category=request.category
        )
        skills = skill_service.get_user_skills(current_user_id, request.skill_type)
        added_skill = next(
            (s for s in skills if s['user_skills_id'] == result['user_skills_id']),
            None
        )
        if not added_skill:
            raise HTTPException(status_code=500, detail="Skill added but could not retrieve")
        return SkillResponse(**added_skill)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding skill: {str(e)}")


@router.get("/", response_model=UserSkillsResponse)
async def get_user_skills(current_user_id: int = Depends(get_current_user_id)):
    """Get all skills for current user (FEAT-1.4.2)."""
    try:
        skill_service = get_skill_normalization_service()
        all_skills = skill_service.get_user_skills(current_user_id)
        skills_offered = [SkillResponse(**s) for s in all_skills if s['skill_type'] == 'offer']
        skills_wanted  = [SkillResponse(**s) for s in all_skills if s['skill_type'] == 'want']
        return UserSkillsResponse(
            skills_offered=skills_offered,
            skills_wanted=skills_wanted,
            total_skills=len(all_skills)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving skills: {str(e)}")


@router.put("/{user_skills_id}", response_model=SkillResponse)
async def update_skill(
    user_skills_id: int,
    proficiency_level: str = Query(..., pattern="^(beginner|intermediate|advanced|expert)$"),
    current_user_id: int = Depends(get_current_user_id)
):
    """Update skill proficiency level (FEAT-1.4.3)."""
    from backend.app.core.database import get_connection, return_connection
    from psycopg2.extras import RealDictCursor

    conn   = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            """
            UPDATE user_skills SET proficiency_level = %s
            WHERE id = %s AND user_id = %s RETURNING id
            """,
            (proficiency_level, user_skills_id, current_user_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Skill not found or not owned by user")
        conn.commit()

        skill_service = get_skill_normalization_service()
        all_skills    = skill_service.get_user_skills(current_user_id)
        updated_skill = next(
            (s for s in all_skills if s['user_skills_id'] == user_skills_id), None
        )
        if not updated_skill:
            raise HTTPException(status_code=500, detail="Update succeeded but could not retrieve")
        return SkillResponse(**updated_skill)
    except HTTPException:
        conn.rollback(); raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating skill: {str(e)}")
    finally:
        cursor.close(); return_connection(conn)


@router.delete("/{user_skills_id}", status_code=204)
async def delete_skill(
    user_skills_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    """Delete a skill from user's profile (FEAT-1.4.4)."""
    try:
        skill_service = get_skill_normalization_service()
        if not skill_service.remove_user_skill(current_user_id, user_skills_id):
            raise HTTPException(status_code=404, detail="Skill not found or not owned by user")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting skill: {str(e)}")


@router.get("/search", response_model=List[SkillSearchResult])
async def search_skills(
    query: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50)
):
    """Search skills by name or semantic similarity (FEAT-1.4.7)."""
    try:
        skill_service = get_skill_normalization_service()
        results = skill_service.search_skills(query, limit)
        return [SkillSearchResult(**r) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching skills: {str(e)}")


@router.get("/suggestions")
async def get_skill_suggestions(current_user_id: int = Depends(get_current_user_id)):
    """
    Get personalised skill suggestions (FEAT-2.4.1).
    Returns popular skills in the same categories as user's current skills.
    """
    from backend.app.core.database import get_connection, return_connection
    from psycopg2.extras import RealDictCursor

    conn   = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            """
            SELECT DISTINCT sg.skill_category
            FROM user_skills us
            JOIN skill_graph sg ON us.skill_graph_id = sg.id
            WHERE us.user_id = %s AND sg.skill_category IS NOT NULL
            """,
            (current_user_id,)
        )
        user_categories = [r['skill_category'] for r in cursor.fetchall()]

        if not user_categories:
            cursor.execute(
                """
                SELECT id AS skill_graph_id, skill_name, skill_category, popularity_score
                FROM skill_graph
                WHERE popularity_score > 0
                ORDER BY popularity_score DESC LIMIT 10
                """
            )
        else:
            cursor.execute(
                """
                SELECT sg.id AS skill_graph_id, sg.skill_name, sg.skill_category, sg.popularity_score
                FROM skill_graph sg
                WHERE sg.skill_category = ANY(%s)
                  AND sg.id NOT IN (SELECT skill_graph_id FROM user_skills WHERE user_id = %s)
                  AND sg.popularity_score > 0
                ORDER BY sg.popularity_score DESC LIMIT 10
                """,
                (user_categories, current_user_id)
            )
        suggestions = cursor.fetchall()
        return {'suggestions': suggestions, 'based_on_categories': user_categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")
    finally:
        cursor.close(); return_connection(conn)


@router.get("/learning-path", response_model=LearningPathResponse)
async def get_learning_path(
    skill: str = Query(..., min_length=2, max_length=100,
                       description="The skill you want to learn, e.g. 'Python'"),
    level: Optional[str] = Query(
        None,
        pattern="^(beginner|intermediate|advanced|expert)$",
        description="Your current level — affects which prerequisites are shown"
    )
):
    """
    Get a structured learning path for any skill (FEAT-2.4.2).

    Returns three sections:
    - **prerequisites**  — foundational skills to learn first
    - **complementary**  — skills that pair well with this one
    - **next_level**     — what to tackle after mastering this skill

    Example:
        GET /api/skills/learning-path?skill=Python&level=beginner
    """
    try:
        lp_service = get_learning_path_service()
        path = lp_service.get_learning_path(skill_name=skill, user_level=level)
        return LearningPathResponse(**path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating learning path: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check for skills service."""
    try:
        skill_service = get_skill_normalization_service()
        return {
            "status": "healthy",
            "service": "skills",
            "embedding_service_loaded": skill_service.embedding_service.model is not None
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}