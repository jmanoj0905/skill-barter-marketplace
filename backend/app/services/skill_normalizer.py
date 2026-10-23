import re
import inflect

p = inflect.engine()

def normalize_skill(skill: str) -> str:
    if not skill:
        return ""

    skill = skill.lower()
    skill = skill.strip()
    skill = re.sub(r"\s+", " ", skill)
    skill = re.sub(r"[^a-z0-9\s\-]", "", skill)

    words = skill.split()
    singular_words = []

    for word in words:
        singular = p.singular_noun(word)
        if singular:
            singular_words.append(singular)
        else:
            singular_words.append(word)

    skill = " ".join(singular_words)

    # 🔥 THIS LINE FIXES YOUR ISSUE
    skill = skill.replace("", "")

    skill = skill[:50]

    return skill