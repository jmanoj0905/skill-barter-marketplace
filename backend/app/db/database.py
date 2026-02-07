"""
In-memory database for minimal 2-user demo.
Matches the frontend mock data structure.
"""

from datetime import datetime
from typing import Optional

# In-memory storage
USERS: dict = {}
SKILLS: dict = {}
WALLETS: dict = {}
BARTERS: dict = {}
CHAT_MESSAGES: dict = {}

# Auto-increment counters
_user_id_counter = 0
_skill_id_counter = 0
_barter_id_counter = 0
_message_id_counter = 0


def _get_next_user_id():
    global _user_id_counter
    _user_id_counter += 1
    return _user_id_counter


def _get_next_skill_id():
    global _skill_id_counter
    _skill_id_counter += 1
    return _skill_id_counter


def _get_next_barter_id():
    global _barter_id_counter
    _barter_id_counter += 1
    return _barter_id_counter


def _get_next_message_id():
    global _message_id_counter
    _message_id_counter += 1
    return _message_id_counter


# User functions
def get_user_by_email(email: str) -> Optional[dict]:
    for user in USERS.values():
        if user["email"] == email:
            return user
    return None


def get_user_by_id(user_id: int) -> Optional[dict]:
    return USERS.get(user_id)


def create_user(email: str, password: str, name: str) -> dict:
    user_id = _get_next_user_id()
    now = datetime.utcnow().isoformat() + "Z"
    user = {
        "user_id": user_id,
        "email": email,
        "password": password,
        "name": name,
        "trust_score": 0.5,
        "created_at": now,
        "updated_at": now,
    }
    USERS[user_id] = user

    # Create wallet for user
    WALLETS[user_id] = {
        "wallet_id": user_id,
        "user_id": user_id,
        "available_balance": 50,
        "locked_balance": 0,
        "total_earned": 50,
        "total_spent": 0,
        "created_at": now,
        "updated_at": now,
    }

    # Initialize empty skills
    SKILLS[user_id] = {"offered": [], "wanted": []}

    return user


# Skills functions
def get_user_skills(user_id: int) -> dict:
    return SKILLS.get(user_id, {"offered": [], "wanted": []})


def add_skill(user_id: int, skill_name: str, skill_type: str, proficiency_level: str = None) -> dict:
    skill_id = _get_next_skill_id()
    now = datetime.utcnow().isoformat() + "Z"
    skill = {
        "skill_id": skill_id,
        "user_id": user_id,
        "skill_name": skill_name.lower(),
        "skill_type": skill_type,
        "proficiency_level": proficiency_level,
        "created_at": now,
    }

    if user_id not in SKILLS:
        SKILLS[user_id] = {"offered": [], "wanted": []}

    if skill_type == "offer":
        SKILLS[user_id]["offered"].append(skill)
    else:
        SKILLS[user_id]["wanted"].append(skill)

    return skill


def delete_skill(user_id: int, skill_id: int, skill_type: str) -> bool:
    if user_id not in SKILLS:
        return False

    key = "offered" if skill_type == "offer" else "wanted"
    skills = SKILLS[user_id][key]

    for i, skill in enumerate(skills):
        if skill["skill_id"] == skill_id:
            skills.pop(i)
            return True
    return False


# Wallet functions
def get_wallet(user_id: int) -> Optional[dict]:
    return WALLETS.get(user_id)


# Barter functions
def get_user_barters(user_id: int) -> list:
    return [b for b in BARTERS.values() if b["user_a_id"] == user_id or b["user_b_id"] == user_id]


def get_barter(barter_id: int) -> Optional[dict]:
    return BARTERS.get(barter_id)


def create_barter(user_a_id: int, user_b_id: int, skill_a: str, skill_b: str) -> dict:
    barter_id = _get_next_barter_id()
    now = datetime.utcnow().isoformat() + "Z"
    barter = {
        "barter_id": barter_id,
        "user_a_id": user_a_id,
        "user_b_id": user_b_id,
        "skill_a": skill_a,
        "skill_b": skill_b,
        "status": "confirmed",
        "proposed_at": now,
        "scheduled_time": None,
        "agreed_duration_minutes": None,
        "actual_start_time": None,
        "actual_end_time": None,
        "actual_duration_minutes": None,
    }
    BARTERS[barter_id] = barter
    CHAT_MESSAGES[barter_id] = []
    return barter


def update_barter(barter_id: int, updates: dict) -> Optional[dict]:
    if barter_id not in BARTERS:
        return None
    BARTERS[barter_id].update(updates)
    return BARTERS[barter_id]


# Chat functions
def get_chat_messages(barter_id: int) -> list:
    return CHAT_MESSAGES.get(barter_id, [])


def add_chat_message(barter_id: int, sender_id: int, content: str) -> dict:
    message_id = _get_next_message_id()
    now = datetime.utcnow().isoformat() + "Z"
    message = {
        "message_id": message_id,
        "barter_id": barter_id,
        "sender_id": sender_id,
        "content": content,
        "created_at": now,
    }
    if barter_id not in CHAT_MESSAGES:
        CHAT_MESSAGES[barter_id] = []
    CHAT_MESSAGES[barter_id].append(message)
    return message


# Matching function
def find_matches(user_id: int, wanted_skill: str) -> list:
    matches = []
    for other_user_id, skills in SKILLS.items():
        if other_user_id == user_id:
            continue

        for offered in skills["offered"]:
            if offered["skill_name"].lower() == wanted_skill.lower():
                user = get_user_by_id(other_user_id)
                if user:
                    # Check if user wants something we offer
                    our_skills = SKILLS.get(user_id, {"offered": [], "wanted": []})
                    wants_our_skill = None
                    for wanted in skills["wanted"]:
                        for our_offered in our_skills["offered"]:
                            if wanted["skill_name"].lower() == our_offered["skill_name"].lower():
                                wants_our_skill = wanted["skill_name"]
                                break

                    matches.append({
                        "match_id": other_user_id * 100 + len(matches),
                        "user_id": other_user_id,
                        "user_name": user["name"],
                        "trust_score": user["trust_score"],
                        "offers_skill": offered["skill_name"],
                        "proficiency_level": offered.get("proficiency_level"),
                        "wants_skill": wants_our_skill,
                        "match_score": 0.9 if wants_our_skill else 0.7,
                    })
    return matches


# Seed data function
def seed_database():
    """Initialize database with 2 test users matching frontend mock data."""
    global _user_id_counter, _skill_id_counter

    # Clear existing data
    USERS.clear()
    SKILLS.clear()
    WALLETS.clear()
    BARTERS.clear()
    CHAT_MESSAGES.clear()
    _user_id_counter = 0
    _skill_id_counter = 0

    now = datetime.utcnow().isoformat() + "Z"

    # Create User A manually (plaintext password for demo)
    user_a_id = _get_next_user_id()
    user_a = {
        "user_id": user_a_id,
        "email": "usera@test.com",
        "password": "password",
        "name": "User A",
        "trust_score": 0.75,
        "created_at": now,
        "updated_at": now,
    }
    USERS[user_a_id] = user_a
    WALLETS[user_a_id] = {
        "wallet_id": user_a_id,
        "user_id": user_a_id,
        "available_balance": 50,
        "locked_balance": 0,
        "total_earned": 50,
        "total_spent": 0,
        "created_at": now,
        "updated_at": now,
    }
    SKILLS[user_a_id] = {"offered": [], "wanted": []}

    # Create User B manually (plaintext password for demo)
    user_b_id = _get_next_user_id()
    user_b = {
        "user_id": user_b_id,
        "email": "userb@test.com",
        "password": "password",
        "name": "User B",
        "trust_score": 0.80,
        "created_at": now,
        "updated_at": now,
    }
    USERS[user_b_id] = user_b
    WALLETS[user_b_id] = {
        "wallet_id": user_b_id,
        "user_id": user_b_id,
        "available_balance": 50,
        "locked_balance": 0,
        "total_earned": 50,
        "total_spent": 0,
        "created_at": now,
        "updated_at": now,
    }
    SKILLS[user_b_id] = {"offered": [], "wanted": []}

    # Add skills for User A
    add_skill(user_a_id, "javascript", "offer", "intermediate")
    add_skill(user_a_id, "guitar", "want")

    # Add skills for User B
    add_skill(user_b_id, "guitar", "offer", "advanced")
    add_skill(user_b_id, "javascript", "want")

    print("Database seeded with 2 users:")
    print(f"  - User A: usera@test.com / password")
    print(f"  - User B: userb@test.com / password")


# Seed on import
seed_database()
