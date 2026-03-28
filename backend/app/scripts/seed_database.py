"""
Seed database with test users and skills (Updated for skill_graph schema)
Uses skill normalization service to populate canonical skill_graph
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from backend.app.core.database import init_connection_pool, execute_query, get_connection, return_connection
from backend.app.services.skill_normalization_service import get_skill_normalization_service
import bcrypt
from psycopg2.extras import RealDictCursor

# Test users with diverse skills
TEST_USERS = [
    {
        "email": "alice@test.com",
        "password": "Password123",
        "name": "Alice Chen",
        "trust_score": 0.80,
        "skills_offered": [
            ("Python Programming", "expert"),
            ("Data Analysis", "advanced"),
            ("Machine Learning", "intermediate"),
        ],
        "skills_wanted": [
            ("Guitar", None),
            ("Spanish", "beginner"),
        ]
    },
    {
        "email": "bob@test.com",
        "password": "Password123",
        "name": "Bob Singh",
        "trust_score": 0.60,
        "skills_offered": [
            ("Guitar", "expert"),
            ("Music Theory", "advanced"),
            ("Singing", "intermediate"),
        ],
        "skills_wanted": [
            ("Python", None),
            ("Web Development", "beginner"),
        ]
    },
    {
        "email": "carol@test.com",
        "password": "Password123",
        "name": "Carol Lee",
        "trust_score": 0.75,
        "skills_offered": [
            ("Spanish", "expert"),
            ("French", "advanced"),
            ("Translation", "expert"),
        ],
        "skills_wanted": [
            ("Data Analysis", None),
            ("Photography", "beginner"),
        ]
    },
    {
        "email": "david@test.com",
        "password": "Password123",
        "name": "David Kumar",
        "trust_score": 0.50,
        "skills_offered": [
            ("Web Development", "expert"),
            ("React", "advanced"),
            ("JavaScript", "expert"),
        ],
        "skills_wanted": [
            ("Python Programming", None),
            ("Machine Learning", "beginner"),
        ]
    },
    {
        "email": "eve@test.com",
        "password": "Password123",
        "name": "Eve Martinez",
        "trust_score": 0.65,
        "skills_offered": [
            ("Photography", "expert"),
            ("Video Editing", "advanced"),
            ("Graphic Design", "intermediate"),
        ],
        "skills_wanted": [
            ("Music Theory", None),
            ("Spanish", "beginner"),
        ]
    },
]


def clear_existing_data():
    """
    Clear all existing test data (BE CAREFUL!)
    Only use in development
    """
    print("\n⚠️  Clearing existing data...")
    
    # Delete in correct order due to foreign keys
    tables = [
        'qa_verdicts',
        'session_feedback',
        'chat_messages',
        'escrows',
        'barters',
        'matches',
        'user_availability',
        'transactions',
        'wallets',
        'trust_scores',
        'user_skills',       # NEW: must delete before skill_graph
        'users'
    ]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            print(f"  ✓ Cleared {table}")
        
        conn.commit()
        print("✓ All tables cleared")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error clearing tables: {e}")
        raise
    finally:
        cursor.close()
        return_connection(conn)


def create_user(user_data):
    """
    Create a user with trust score and wallet
    Returns user_id
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Hash password using bcrypt
        password_bytes = user_data["password"].encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        # Insert user
        cursor.execute(
            """
            INSERT INTO users (email, password_hash, name, trust_score)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (user_data["email"], password_hash, user_data["name"], user_data["trust_score"])
        )
        user_id = cursor.fetchone()['id']
        
        # Create trust score record
        cursor.execute(
            """
            INSERT INTO trust_scores (user_id, score)
            VALUES (%s, %s)
            """,
            (user_id, user_data["trust_score"])
        )
        
        # Create wallet with initial 50 credits
        cursor.execute(
            """
            INSERT INTO wallets (user_id, available_balance, total_earned)
            VALUES (%s, 50, 50)
            """,
            (user_id,)
        )
        
        # Create initial transaction record
        cursor.execute(
            """
            INSERT INTO transactions (user_id, amount, type, balance_after)
            VALUES (%s, 50, 'initial', 50)
            """,
            (user_id,)
        )
        
        conn.commit()
        return user_id
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error creating user {user_data['email']}: {e}")
        raise
    finally:
        cursor.close()
        return_connection(conn)


def add_skills_to_user(user_id, skills_offered, skills_wanted):
    """
    Add skills to user using normalization service
    
    NEW: This uses the skill normalization flow:
    1. Each skill name is normalized
    2. System searches for similar skills in skill_graph
    3. If match found (similarity > 0.85) → reuse existing
    4. If no match → create new skill_graph entry with embedding
    5. Link user to skill via user_skills table
    
    Returns count of skills added
    """
    skill_service = get_skill_normalization_service()
    total_added = 0
    
    try:
        # Add offered skills
        for skill_name, proficiency in skills_offered:
            skill_service.add_user_skill(
                user_id=user_id,
                skill_name=skill_name,
                skill_type='offer',
                proficiency_level=proficiency
            )
            total_added += 1
            print(f"    ✓ Added offer: {skill_name} ({proficiency})")
        
        # Add wanted skills
        for skill_name, proficiency in skills_wanted:
            skill_service.add_user_skill(
                user_id=user_id,
                skill_name=skill_name,
                skill_type='want',
                proficiency_level=proficiency
            )
            total_added += 1
            print(f"    ✓ Added want: {skill_name}")
        
        return total_added
        
    except Exception as e:
        print(f"✗ Error adding skills for user {user_id}: {e}")
        raise


def verify_seeded_data():
    """
    Verify data was seeded correctly
    """
    print("\n📊 Verifying seeded data...")
    
    # Check users
    result = execute_query("SELECT COUNT(*) as count FROM users")
    print(f"  Users: {result[0]['count']}")
    
    # Check canonical skills (NEW)
    result = execute_query("SELECT COUNT(*) as count FROM skill_graph")
    total_canonical_skills = result[0]['count']
    print(f"  Canonical skills (skill_graph): {total_canonical_skills}")
    
    # Check embeddings in skill_graph
    result = execute_query(
        "SELECT COUNT(*) as count FROM skill_graph WHERE skill_embedding IS NOT NULL"
    )
    embedded_skills = result[0]['count']
    print(f"  Skills with embeddings: {embedded_skills}/{total_canonical_skills}")
    
    # Check user-skill links
    result = execute_query("SELECT COUNT(*) as count FROM user_skills")
    print(f"  User-skill links: {result[0]['count']}")
    
    # Check wallets
    result = execute_query("SELECT COUNT(*) as count FROM wallets")
    print(f"  Wallets: {result[0]['count']}")
    
    # Show sample user with skills
    result = execute_query(
        """
        SELECT 
            u.name, 
            u.email, 
            u.trust_score, 
            w.available_balance,
            COUNT(DISTINCT us.id) as skill_count,
            COUNT(DISTINCT us.id) FILTER (WHERE us.skill_type = 'offer') as offers,
            COUNT(DISTINCT us.id) FILTER (WHERE us.skill_type = 'want') as wants
        FROM users u
        LEFT JOIN wallets w ON u.id = w.user_id
        LEFT JOIN user_skills us ON u.id = us.user_id
        GROUP BY u.id, u.name, u.email, u.trust_score, w.available_balance
        LIMIT 1
        """
    )
    
    if result:
        user = result[0]
        print(f"\n  Sample user:")
        print(f"    Name: {user['name']}")
        print(f"    Email: {user['email']}")
        print(f"    Trust: {user['trust_score']}")
        print(f"    Balance: {user['available_balance']} credits")
        print(f"    Skills: {user['skill_count']} ({user['offers']} offer, {user['wants']} want)")
    
    # Show skill deduplication example
    print(f"\n  Skill normalization example:")
    result = execute_query(
        """
        SELECT 
            sg.skill_name,
            COUNT(us.id) as user_count,
            sg.popularity_score
        FROM skill_graph sg
        LEFT JOIN user_skills us ON sg.id = us.skill_graph_id
        GROUP BY sg.id, sg.skill_name, sg.popularity_score
        ORDER BY user_count DESC
        LIMIT 3
        """
    )
    for skill in result:
        print(f"    '{skill['skill_name']}': {skill['user_count']} users, popularity={skill['popularity_score']:.2f}")


def main():
    """
    Main seeding function
    """
    print("="*60)
    print("DATABASE SEEDING SCRIPT (Updated for skill_graph schema)")
    print("="*60)
    
    # Initialize database connection
    init_connection_pool()
    
    # Ask for confirmation before clearing
    response = input("\n⚠️  This will DELETE all existing data. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return
    
    try:
        # Step 1: Clear existing data
        clear_existing_data()
        
        # Step 2: Create users with skills
        print("\n👥 Creating test users with skills...")
        for user_data in TEST_USERS:
            user_id = create_user(user_data)
            print(f"  ✓ Created {user_data['name']} (ID: {user_id})")
            
            # Add skills using normalization service
            # This will auto-populate skill_graph and generate embeddings
            skill_count = add_skills_to_user(
                user_id,
                user_data["skills_offered"],
                user_data["skills_wanted"]
            )
        
        # Step 3: Verify
        verify_seeded_data()
        
        print("\n" + "="*60)
        print("✓ DATABASE SEEDING COMPLETE!")
        print("="*60)
        print("\nTest credentials (all have password: Password123):")
        for user in TEST_USERS:
            print(f"  - {user['email']}")
        
        print("\n📌 Key improvements in new schema:")
        print("  • Canonical skill_graph table (one embedding per skill)")
        print("  • Automatic skill normalization (deduplicates similar skills)")
        print("  • Popularity scoring (tracks how many users offer/want each skill)")
        print("  • More efficient vector search (shared embeddings)")
        
    except Exception as e:
        print(f"\n✗ Seeding failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()