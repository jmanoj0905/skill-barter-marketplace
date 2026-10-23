from app.models.skill import Skill
import re
from app.services.skill_normalizer import normalize_skill
from app.services.skill_taxonomy_service import map_skill_to_taxonomy
from app.models.skill import Skill
from app.services.skill_embedding_service import generate_embedding

def create_skill(db, user_id, skill_data):
    normalized = normalize_skill(skill_data.skill_name)
    taxonomy = map_skill_to_taxonomy(normalized)
    embedding = generate_embedding(skill_data.skill_name)

    duplicate = (
        db.query(Skill)
        .filter(
            Skill.user_id == user_id,
            Skill.normalized_name == normalized,
            Skill.skill_type == skill_data.skill_type,
        )
        .first()
    )
    if duplicate:
        raise ValueError("This skill already exists for the user")

    new_skill = Skill(
        user_id=user_id,
        skill_name=skill_data.skill_name,
        normalized_name=normalized,
        skill_type=skill_data.skill_type,
        proficiency_level=skill_data.proficiency_level,
        embedding=embedding
    )

    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)

    # DEBUG (you can remove later)
    print("DEBUG NORMALIZED:", normalized)
    print("DEBUG TAXONOMY:", taxonomy)

    # ✅ return same as before (simple)
    return {
    "skill": new_skill,
    "taxonomy": taxonomy
}


def get_skill_normalization_service():
    return normalize_skill


def add_user_skill(db, skill_data):
    return create_skill(db, skill_data.user_id, skill_data)
 

def get_user_skills(db, user_id):

    skills = db.query(Skill).filter(Skill.user_id == user_id).all()

    offered = []
    desired = []

    for skill in skills:

        skill_data = {
            "id": skill.id,
            "skill_name": skill.skill_name,
            "proficiency_level": skill.proficiency_level
        }

        if skill.skill_type == "offered":
            offered.append(skill_data)
        elif skill.skill_type == "desired":
            desired.append(skill_data)

    return {
        "offered": offered,
        "desired": desired
    }


def update_skill(db, skill_id, skill_data):

    skill = db.query(Skill).filter(Skill.id == skill_id).first()

    if not skill:
        return None

    skill.skill_name = skill_data.skill_name
    skill.skill_type = skill_data.skill_type
    skill.proficiency_level = skill_data.proficiency_level

    db.commit()
    db.refresh(skill)

    return skill

def delete_skill(db, skill_id, user_id):

    skill = db.query(Skill).filter(Skill.id == skill_id).first()

    if not skill:
        return None

    # Verify skill ownership
    if skill.user_id != user_id:
        return "unauthorized"

    db.delete(skill)
    db.commit()

    return skill



def normalize_skill(skill: str) -> str:

    if not skill:
        return ""

    # 1. lowercase
    skill = skill.lower()

    # 2. remove extra spaces
    skill = " ".join(skill.split())

    # 3. remove special characters (keep hyphen)
    skill = re.sub(r"[^a-z0-9\- ]", "", skill)

    # 4. truncate to 50 chars
    skill = skill[:50]

    # 5. simple singular conversion
    if skill.endswith("s"):
        skill = skill[:-1]

    return skill


def suggest_skills(db, query: str):
    query = query.lower()

    skills = db.query(Skill).all()

    results = []

    for skill in skills:
        if query in skill.skill_name.lower():
            results.append(skill)

    # remove duplicates
    unique = {s.skill_name: s for s in results}.values()

    return list(unique)[:5]


def search_skills(db, query: str, limit: int = 20):
    normalized_query = normalize_skill(query)
    if not normalized_query:
        return []

    skills = (
        db.query(Skill)
        .filter(Skill.normalized_name.ilike(f"%{normalized_query}%"))
        .order_by(Skill.skill_name)
        .limit(limit)
        .all()
    )
    return skills


def generate_learning_path(skill_name: str):
    normalized = normalize_skill(skill_name)
    taxonomy = map_skill_to_taxonomy(normalized)
    category = taxonomy[0]["category"] if taxonomy else None
    canonical_name = taxonomy[0]["canonical_name"] if taxonomy else normalized

    steps = [
        f"Learn the fundamentals of {canonical_name}",
        f"Practice {canonical_name} with a small guided project",
        f"Build an independent project using {canonical_name}",
        f"Share your work and request feedback on your {canonical_name} skills",
    ]
    return {
        "skill_name": skill_name,
        "normalized_name": normalized,
        "category": category,
        "steps": steps,
    }


embedding_cache = {}

def get_embedding_by_skill_id(db, skill_id: int):
    # cache check
    if skill_id in embedding_cache:
        print("CACHE HIT")
        return embedding_cache[skill_id]

    skill = db.query(Skill).filter(Skill.id == skill_id).first()

    if not skill:
        return None

    embedding_cache[skill_id] = skill.embedding
    return skill.embedding