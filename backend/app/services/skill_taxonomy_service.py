from app.data.skill_taxonomy import SKILL_TAXONOMY

def map_skill_to_taxonomy(normalized_skill: str):
    matches = []

    for category, skills in SKILL_TAXONOMY.items():
        for skill in skills:
            if skill in normalized_skill or normalized_skill in skill:
                matches.append({
                    "canonical_name": skill,
                    "category": category
                })

    # return top 3 matches
    return matches[:3]