"""
Seed database with test users and skills
Generates embeddings for all skills
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.database import init_connection_pool, execute_query, get_connection, return_connection
from services.embedding_service import get_embedding_service
import bcrypt
from psycopg2.extras import RealDictCursor
import json

# Test users with diverse skills
TEST_USERS = [
    {
        "email": "alice@test.com",
        "password": "Password123",
        "name": "Alice Chen",
        "trust_score": 0.80,
        "skills_offered": [
            ("python programming", "expert"),
            ("data analysis", "advanced"),
            ("machine learning", "intermediate"),
        ],
        "skills_wanted": [
            ("guitar", None),
            ("spanish", "beginner"),
        ]
    },
    {
        "email": "bob@test.com",
        "password": "Password123",
        "name": "Bob Singh",
        "trust_score": 0.60,
        "skills_offered": [
            ("guitar", "expert"),
            ("music theory", "advanced"),
            ("singing", "intermediate"),
        ],
        "skills_wanted": [
            ("python", None),
            ("web development", "beginner"),
        ]
    },
    {
        "email": "carol@test.com",
        "password": "Password123",
        "name": "Carol Lee",
        "trust_score": 0.75,
        "skills_offered": [
            ("spanish", "expert"),
            ("french", "advanced"),
            ("translation", "expert"),
        ],
        "skills_wanted": [
            ("data analysis", None),
            ("photography", "beginner"),
        ]
    },
    {
        "email": "david@test.com",
        "password": "Password123",
        "name": "David Kumar",
        "trust_score": 0.50,
        "skills_offered": [
            ("web development", "expert"),
            ("react", "advanced"),
            ("javascript", "expert"),
        ],
        "skills_wanted": [
            ("python programming", None),
            ("machine learning", "beginner"),
        ]
    },
    {
        "email": "eve@test.com",
        "password": "Password123",
        "name": "Eve Martinez",
        "trust_score": 0.65,
        "skills_offered": [
            ("photography", "expert"),
            ("video editing", "advanced"),
            ("graphic design", "intermediate"),
        ],
        "skills_wanted": [
            ("music theory", None),
            ("spanish", "beginner"),
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
        'settlements',
        'qa_verdicts',
        'feedback',
        'chat_messages',
        'escrows',
        'barters',
        'transactions',
        'wallets',
        'trust_scores',
        'skills',
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
    Create a user with skills and initial wallet
    Returns user_id
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Hash password using bcrypt directly (FIX for compatibility)
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

def add_skills(user_id, skills_offered, skills_wanted):
    """
    Add skills for a user (without embeddings initially)
    Returns list of skill IDs
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    skill_ids = []
    
    try:
        # Add offered skills
        for skill_name, proficiency in skills_offered:
            cursor.execute(
                """
                INSERT INTO skills (user_id, skill_name, skill_type, proficiency_level)
                VALUES (%s, %s, 'offer', %s)
                RETURNING id
                """,
                (user_id, skill_name, proficiency)
            )
            skill_ids.append(cursor.fetchone()['id'])
        
        # Add wanted skills
        for skill_name, proficiency in skills_wanted:
            cursor.execute(
                """
                INSERT INTO skills (user_id, skill_name, skill_type, proficiency_level)
                VALUES (%s, %s, 'want', %s)
                RETURNING id
                """,
                (user_id, skill_name, proficiency)
            )
            skill_ids.append(cursor.fetchone()['id'])
        
        conn.commit()
        return skill_ids
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error adding skills for user {user_id}: {e}")
        raise
    finally:
        cursor.close()
        return_connection(conn)

def generate_embeddings_for_all_skills():
    """
    Generate embeddings for all skills in database
    This is the AI/ML step!
    """
    print("\n🤖 Generating embeddings for all skills...")
    
    # Get embedding service
    embedding_service = get_embedding_service()
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all skills without embeddings
        cursor.execute(
            """
            SELECT id, skill_name
            FROM skills
            WHERE embedding IS NULL
            ORDER BY id
            """
        )
        skills = cursor.fetchall()
        
        print(f"  Found {len(skills)} skills to process")
        
        # Generate embeddings
        skill_names = [skill['skill_name'] for skill in skills]
        embeddings = embedding_service.generate_embeddings_batch(skill_names)
        
        # Update database with embeddings
        for skill, embedding in zip(skills, embeddings):
            # Convert list to PostgreSQL vector format
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            cursor.execute(
                """
                UPDATE skills
                SET embedding = %s::vector
                WHERE id = %s
                """,
                (embedding_str, skill['id'])
            )
            
            print(f"  ✓ Generated embedding for '{skill['skill_name']}'")
        
        conn.commit()
        print(f"✓ Generated {len(skills)} embeddings")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error generating embeddings: {e}")
        raise
    finally:
        cursor.close()
        return_connection(conn)

def verify_seeded_data():
    """
    Verify data was seeded correctly
    """
    print("\n📊 Verifying seeded data...")
    
    # Check users
    result = execute_query("SELECT COUNT(*) as count FROM users")
    print(f"  Users: {result[0]['count']}")
    
    # Check skills
    result = execute_query("SELECT COUNT(*) as count FROM skills")
    total_skills = result[0]['count']
    print(f"  Skills: {total_skills}")
    
    # Check embeddings
    result = execute_query("SELECT COUNT(*) as count FROM skills WHERE embedding IS NOT NULL")
    embedded_skills = result[0]['count']
    print(f"  Skills with embeddings: {embedded_skills}/{total_skills}")
    
    # Check wallets
    result = execute_query("SELECT COUNT(*) as count FROM wallets")
    print(f"  Wallets: {result[0]['count']}")
    
    # Show sample user
    result = execute_query(
        """
        SELECT u.name, u.email, u.trust_score, w.available_balance,
               COUNT(s.id) as skill_count
        FROM users u
        LEFT JOIN wallets w ON u.id = w.user_id
        LEFT JOIN skills s ON u.id = s.user_id
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
        print(f"    Skills: {user['skill_count']}")

def main():
    """
    Main seeding function
    """
    print("="*60)
    print("DATABASE SEEDING SCRIPT")
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
        print("\n👥 Creating test users...")
        for user_data in TEST_USERS:
            user_id = create_user(user_data)
            skill_ids = add_skills(
                user_id,
                user_data["skills_offered"],
                user_data["skills_wanted"]
            )
            print(f"  ✓ Created {user_data['name']} with {len(skill_ids)} skills")
        
        # Step 3: Generate embeddings
        generate_embeddings_for_all_skills()
        
        # Step 4: Verify
        verify_seeded_data()
        
        print("\n" + "="*60)
        print("✓ DATABASE SEEDING COMPLETE!")
        print("="*60)
        print("\nTest credentials (all have password: Password123):")
        for user in TEST_USERS:
            print(f"  - {user['email']}")
        
    except Exception as e:
        print(f"\n✗ Seeding failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()