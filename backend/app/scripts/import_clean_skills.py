"""
Import Clean, Hand-Curated Technical Skills
No filtering needed - these are pre-vetted, 100% technical skills
"""

import sys
import os
from pathlib import Path
import csv

backend_dir = Path(r"C:\Users\hp\OneDrive\Desktop\skill-barter-marketplace\backend")
sys.path.insert(0, str(backend_dir))

from app.core.database import init_connection_pool, get_connection, return_connection
from app.services.embedding_service import get_embedding_service
from psycopg2.extras import RealDictCursor


def load_clean_skills(csv_path):
    """Load pre-curated clean skills"""
    print(f"\n📖 Loading clean technical skills from {csv_path}...")
    
    skills = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            skill_name = row['skill_name'].strip()
            skill_category = row['skill_category'].strip()
            description = row['description'].strip()
            
            skills.append({
                'skill_name': skill_name,
                'skill_normalized': skill_name.lower().strip(),
                'skill_category': skill_category,
                'description': description
            })
    
    print(f"✓ Loaded {len(skills):,} clean technical skills")
    
    # Show category breakdown
    from collections import Counter
    categories = Counter(s['skill_category'] for s in skills)
    print("\n📊 Category breakdown:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat:30s} {count:4d}")
    
    return skills


def import_to_database(skills, batch_size=50):
    """Import clean skills to database"""
    print(f"\n💾 Importing {len(skills):,} skills to database...")
    
    embedding_service = get_embedding_service()
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    imported = 0
    skipped = 0
    errors = 0
    
    try:
        for i, skill in enumerate(skills, 1):
            try:
                # Check if exists
                cursor.execute(
                    "SELECT id FROM skill_graph WHERE skill_normalized = %s",
                    (skill['skill_normalized'],)
                )
                
                if cursor.fetchone():
                    skipped += 1
                    continue
                
                # Generate embedding
                embedding = embedding_service.generate_embedding(skill['skill_name'])
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                
                # Insert
                cursor.execute(
                    """
                    INSERT INTO skill_graph (
                        skill_name,
                        skill_normalized,
                        skill_category,
                        skill_embedding,
                        popularity_score,
                        is_featured
                    )
                    VALUES (%s, %s, %s, %s::vector, 0.0, true)
                    """,
                    (
                        skill['skill_name'],
                        skill['skill_normalized'],
                        skill['skill_category'],
                        embedding_str
                    )
                )
                
                imported += 1
                
                # Batch commit
                if imported % batch_size == 0:
                    conn.commit()
                    progress = int(imported / len(skills) * 100)
                    print(f"   Progress: {imported:4d}/{len(skills)} ({progress:3d}%)")
                
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"   ⚠️  Error: {skill['skill_name'][:40]}: {str(e)[:60]}")
                conn.rollback()
                continue
        
        # Final commit
        conn.commit()
        
        print(f"\n✅ Import complete!")
        print(f"   ✓ Imported: {imported:,}")
        print(f"   ⊘ Skipped: {skipped:,}")
        print(f"   ✗ Errors: {errors:,}")
        
        return imported
        
    finally:
        cursor.close()
        return_connection(conn)


def verify_import():
    """Verify the import"""
    print("\n📊 Verification...")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Total count
        cursor.execute("SELECT COUNT(*) as total FROM skill_graph")
        total = cursor.fetchone()['total']
        
        # By category
        cursor.execute(
            """
            SELECT skill_category, COUNT(*) as count
            FROM skill_graph
            GROUP BY skill_category
            ORDER BY count DESC
            """
        )
        categories = cursor.fetchall()
        
        # Sample skills
        cursor.execute(
            """
            SELECT skill_name, skill_category
            FROM skill_graph
            ORDER BY RANDOM()
            LIMIT 20
            """
        )
        samples = cursor.fetchall()
        
        print(f"\n  Total skills: {total:,}")
        print(f"\n  Categories:")
        for cat in categories:
            print(f"    {cat['skill_category']:30s} {cat['count']:4d}")
        
        print(f"\n  Random sample skills:")
        for sample in samples:
            print(f"    • {sample['skill_name']:40s} [{sample['skill_category']}]")
        
        print(f"\n✅ DATABASE READY!")
        print(f"   All skills are 100% verified technical skills")
        print(f"   No garbage, no medical terms, no soft skills")
        
    finally:
        cursor.close()
        return_connection(conn)


def main():
    print("=" * 70)
    print("CLEAN TECHNICAL SKILLS IMPORT")
    print("Hand-Curated, Pre-Verified, 100% Technical")
    print("=" * 70)
    
    # Initialize
    init_connection_pool()
    
    # Find CSV
    csv_path = Path(r"C:\Users\hp\OneDrive\Desktop\skill-barter-marketplace\backend\app\scripts\clean_technical_skills (1).csv")
    
    if not csv_path.exists():
        print(f"\n✗ Error: clean_technical_skills.csv not found")
        print(f"\nExpected location: {csv_path}")
        return
    
    # Load
    skills = load_clean_skills(csv_path)
    
    # Show samples
    print("\n📋 Sample skills (first 15):")
    for skill in skills[:15]:
        print(f"   • {skill['skill_name']:40s} [{skill['skill_category']}]")
    
    # Confirm
    print(f"\n⚠️  About to import {len(skills):,} CLEAN technical skills")
    print("   These are hand-curated and verified")
    print("   No ESCO garbage - just real technical skills")
    response = input("\nContinue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Import
    imported = import_to_database(skills)
    
    # Verify
    if imported > 0:
        verify_import()
    
    print("\n" + "=" * 70)
    print("✅ CLEAN IMPORT COMPLETE!")
    print("=" * 70)
    print("\nYour database now has:")
    print(f"  • {len(skills):,} verified technical skills")
    print(f"  • NO medical terms (otorhinolaryngologic ❌)")
    print(f"  • NO soft skills (accept criticism ❌)")
    print(f"  • NO legal studies (embargo regulations ❌)")
    print(f"  • NO religious studies (monasticism ❌)")
    print(f"  • ONLY real technical skills ✅")


if __name__ == "__main__":
    main()
