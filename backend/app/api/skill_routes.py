from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.skill import Skill

from app.db.session import get_db
from app.schemas.skill_schema import (
    AddSkillRequest,
    LearningPathResponse,
    SkillCreate,
    SkillResponse,
    UserSkillsResponse,
)
from app.services.skill_service import (
    add_user_skill,
    create_skill,
    delete_skill,
    get_embedding_by_skill_id,
    get_user_skills,
    generate_learning_path,
    search_skills,
    suggest_skills,
    update_skill,
)

router = APIRouter(prefix="/users", tags=["Skills"])
api_router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.post("/skills")
def add_skill(skill: SkillCreate, db: Session = Depends(get_db)):
    try:
        return create_skill(db, skill.user_id, skill)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/skills")
def retrieve_skills(user_id: int, db: Session = Depends(get_db)):
    return get_user_skills(db, user_id)


@router.put("/skills/{skill_id}")
def update_user_skill(
    skill_id: int,
    skill: SkillCreate,
    db: Session = Depends(get_db),
):
    updated_skill = update_skill(db, skill_id, skill)
    if not updated_skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    return updated_skill


@router.delete("/skills/{skill_id}")
def delete_user_skill(
    skill_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    result = delete_skill(db, skill_id, user_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    if result == "unauthorized":
        raise HTTPException(status_code=403, detail="Not allowed to delete this skill")

    return {"message": "Skill deleted successfully"}


@router.get("/skills/suggestions")
def get_skill_suggestions(query: str, db: Session = Depends(get_db)):
    return suggest_skills(db, query)


@router.get("/skills/{skill_id}/embedding")
def get_skill_embedding(skill_id: int, db: Session = Depends(get_db)):
    embedding = get_embedding_by_skill_id(db, skill_id)
    if embedding is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"skill_id": skill_id, "embedding": embedding}


@api_router.post("", response_model=SkillResponse)
def add_api_skill(request: AddSkillRequest, db: Session = Depends(get_db)):
    try:
        result = add_user_skill(db, request)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return result["skill"]


@api_router.get("/user/{user_id}", response_model=UserSkillsResponse)
def get_api_user_skills(user_id: int, db: Session = Depends(get_db)):
    skills = db.query(Skill).filter(Skill.user_id == user_id).all()
    return {
        "offered": [skill for skill in skills if skill.skill_type == "offered"],
        "desired": [skill for skill in skills if skill.skill_type == "desired"],
    }


@api_router.put("/{skill_id}", response_model=SkillResponse)
def update_api_skill(
    skill_id: int,
    request: AddSkillRequest,
    db: Session = Depends(get_db),
):
    updated_skill = update_skill(db, skill_id, request)
    if not updated_skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return updated_skill


@api_router.delete("/{skill_id}", status_code=204)
def delete_api_skill(
    skill_id: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    result = delete_skill(db, skill_id, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    if result == "unauthorized":
        raise HTTPException(status_code=403, detail="Not allowed to delete this skill")


@api_router.get("/search", response_model=list[SkillResponse])
def search_api_skills(
    query: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return search_skills(db, query, limit)


@api_router.get("/suggestions", response_model=list[SkillResponse])
def suggest_api_skills(query: str = Query(..., min_length=1, max_length=50), db: Session = Depends(get_db)):
    return suggest_skills(db, query)


@api_router.get("/learning-path", response_model=LearningPathResponse)
def get_learning_path(skill_name: str = Query(..., min_length=1, max_length=50)):
    return generate_learning_path(skill_name)