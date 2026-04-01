from app.models.skill import Skill




def create_skill(db, user_id, skill_data):

    skill = Skill(
        user_id=user_id,
        skill_name=skill_data.skill_name,
        skill_type=skill_data.skill_type,
        proficiency_level=skill_data.proficiency_level
    )

    db.add(skill)
    db.commit()
    db.refresh(skill)

    return skill

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
        else:
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