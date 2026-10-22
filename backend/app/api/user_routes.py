from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.schemas.profile_schema import ProfileUpdateRequest
from app.services.user_service import update_profile
from app.services.user_service import get_user_profile
from fastapi import APIRouter, UploadFile, File, Header
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
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.models.identity_score import IdentityConfidenceScore
from app.services.wallet_service import create_wallet_with_initial_credits
import io
from fastapi import APIRouter, Depends, Query
from app.services.skill_service import suggest_skills
from app.services.skill_service import get_embedding_by_skill_id

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
    image_bytes = await validate_image(file)

    # Upload original image
    image_url = upload_file(io.BytesIO(image_bytes), file.filename)

    # Generate thumbnail
    thumbnail = generate_thumbnail(image_bytes)
    thumb_url = upload_file(thumbnail, "thumb_" + file.filename)

    return {
        "user_id": user_id,
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


@router.get("/skills/suggestions")
def get_skill_suggestions(query: str, db: Session = Depends(get_db)):
    suggestions = suggest_skills(db, query)
    return suggestions


@router.get("/skills/{skill_id}/embedding")
def get_skill_embedding(skill_id: int, db: Session = Depends(get_db)):
    embedding = get_embedding_by_skill_id(db, skill_id)
    return {"skill_id": skill_id, "embedding": embedding}


@router.get("/wallet")
def get_wallet(user_id: int, db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()

    if not wallet:
        wallet = create_wallet_with_initial_credits(db, user_id)

    return {
        "user_id": wallet.user_id,
        "available_balance": wallet.available_balance,
        "locked_balance": wallet.locked_balance,
        "total_earned": wallet.total_earned,
        "total_spent": wallet.total_spent,
        "last_transaction_at": wallet.last_transaction_at
    }

@router.get("/wallet/balance")
def get_balance(user_id: int, db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()

    if not wallet:
        wallet = create_wallet_with_initial_credits(db, user_id)

    return {
        "user_id": user_id,
        "available_balance": wallet.available_balance,
        "locked_balance": wallet.locked_balance
    }

@router.get("/wallet/history")
def get_wallet_history(user_id: int, page: int = 1, db: Session = Depends(get_db)):
    limit = 50
    offset = (page - 1) * limit

    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return transactions


@router.get("/admin/fraud-events")
def get_fraud_events(
    limit: int = 50,
    user_id: int | None = None,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
    db: Session = Depends(get_db),
):
    if not settings.FRAUD_ADMIN_KEY:
        raise HTTPException(status_code=503, detail="Fraud admin key not configured")

    if x_admin_key != settings.FRAUD_ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    safe_limit = max(1, min(limit, 200))
    query = db.query(IdentityConfidenceScore)

    if user_id is not None:
        query = query.filter(IdentityConfidenceScore.user_id == user_id)

    rows = (
        query
        .order_by(IdentityConfidenceScore.updated_at.desc())
        .limit(safe_limit)
        .all()
    )

    events = []
    for row in rows:
        if not isinstance(row.breakdown, dict):
            continue
        if "fraud_score" not in row.breakdown:
            continue

        events.append({
            "id": row.id,
            "user_id": row.user_id,
            "confidence_score": row.confidence_score,
            "updated_at": row.updated_at,
            "breakdown": row.breakdown,
        })

    return {
        "count": len(events),
        "events": events,
    }