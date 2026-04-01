from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.profile_schema import ProfileUpdateRequest
from app.services.user_service import update_profile
from app.services.user_service import get_user_profile
from fastapi import APIRouter, UploadFile, File
from app.services.image_service import generate_thumbnail
from app.services.storage_service import upload_file
from app.utils.file_validator import validate_image
from app.services.user_service import is_username_available
from app.schemas.skill_schema import SkillCreate
from app.services.skill_service import create_skill
from app.services.skill_service import get_user_skills
from app.services.skill_service import update_skill
from app.services.skill_service import delete_skill
from fastapi import HTTPException
from app.utils.logger import logger
import io
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/users", tags=["Users"])
# router = APIRouter(prefix="/users", tags=["Users"])
# router = APIRouter()


@router.put("/profile")
def update_user_profile(
    request: ProfileUpdateRequest,
    db: Session = Depends(get_db)
):

    user = update_profile(
        db,
        request.user_id,
        request.bio,
        request.location,
        request.timezone,
        request.preferred_languages
    )

    return {
        "message": "Profile updated successfully",
        "user_id": user.id,
        "bio": user.bio,
        "location": user.location,
        "timezone": user.timezone,
        "preferred_languages": user.preferred_languages
    }


@router.get("/profile")
def get_profile(user_id: int, db: Session = Depends(get_db)):

    profile = get_user_profile(db, user_id)

    return profile


@router.post("/users/{user_id}/profile/image")
async def upload_profile_image(
        user_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):

    image_bytes = await file.read()

    # Upload original image
    image_url = upload_file(io.BytesIO(image_bytes), file.filename)

    # Generate thumbnail
    thumbnail = generate_thumbnail(image_bytes)
    thumb_url = upload_file(thumbnail, "thumb_" + file.filename)

    # Update database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return {"error": "User not found"}

    user.profile_image_url = image_url

    db.commit()

    return {
        "image_url": image_url,
        "thumbnail_url": thumb_url
    }

@router.get("/users/check-username")
def check_username(
    username: str = Query(...),
    db: Session = Depends(get_db)
):

    available = is_username_available(db, username)

    return {
        "available": available
    }

@router.post("/users/skills")
def add_skill(
    skill: SkillCreate,
    db: Session = Depends(get_db)
):

    created_skill = create_skill(db, skill.user_id, skill)

    return created_skill
    
      # Validation
    valid_types = ["offered", "desired"]
    valid_levels = ["beginner", "intermediate", "advanced", "expert"]

    if skill.skill_type not in valid_types:
        return {"error": "Invalid skill type"}

    if skill.proficiency_level not in valid_levels:
        return {"error": "Invalid proficiency level"}

    created_skill = create_skill(db, user_id, skill)

    return created_skill


@router.get("/users/skills")
def retrieve_skills(
    user_id: int,
    db: Session = Depends(get_db)
):

    skills = get_user_skills(db, user_id)

    return skills


@router.put("/users/skills/{skillId}")
def update_user_skill(
    skillId: int,
    skill: SkillCreate,
    db: Session = Depends(get_db)
):
    logger.info(f"User updated skill {skillId}")

    valid_types = ["offered", "desired"]
    valid_levels = ["beginner", "intermediate", "advanced", "expert"]

    if skill.skill_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid skill type")

    if skill.proficiency_level not in valid_levels:
        raise HTTPException(status_code=400, detail="Invalid proficiency level")

    updated_skill = update_skill(db, skillId, skill)

    if not updated_skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    return updated_skill

@router.delete("/users/skills/{skillId}")
def delete_user_skill(
    skillId: int,
    user_id: int,
    db: Session = Depends(get_db)
):

    result = delete_skill(db, skillId, user_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    if result == "unauthorized":
        raise HTTPException(status_code=403, detail="Not allowed to delete this skill")

    logger.info(f"User {user_id} deleted skill {skillId}")

    return {"message": "Skill deleted successfully"}