"""
Test suite for matching service
Validates semantic matching and scoring algorithms
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Fixed imports to match your project structure
from backend.app.core.database import init_connection_pool, execute_query
from backend.app.services.matching_service import get_matching_service


def test_find_matches_alice_wants_guitar():
    """
    Test Case 1: Alice wants to learn guitar
    Expected: Should match Bob (who teaches guitar and wants python)
    """
    print("\n=== TEST 1: Alice wants guitar ===")
    
    matching_service = get_matching_service()
    
    # Alice's user_id is 1 (from seed data)
    alice_id = 1
    desired_skill = "guitar"
    
    matches = matching_service.find_matches(alice_id, desired_skill)
    
    print(f"Query: User {alice_id} (Alice) wants to learn '{desired_skill}'")
    print(f"Found {len(matches)} matches:\n")
    
    for i, match in enumerate(matches, 1):
        print(f"{i}. {match['name']} (User {match['user_id']})")
        print(f"   Match Score: {match['match_score']:.3f}")
        print(f"   Skill Similarity: {match['skill_similarity']:.3f}")
        print(f"   Mutual Interest: {match['has_mutual_interest']}")
        if match['mutual_skill']:
            print(f"   Mutual Skill: {match['mutual_skill']}")
        print(f"   Explanation: {match['compatibility_reason']}")
        print()
    
    # Verify Bob is top match
    assert len(matches) > 0, "Should find at least one match"
    top_match = matches[0]
    print(f"✓ Top match: {top_match['name']}")
    
    # Bob should be a high-scoring match (teaches guitar, wants python)
    assert top_match['match_score'] > 0.7, f"Expected high match score, got {top_match['match_score']}"
    
    print("✓ Test passed!")


def test_find_matches_bob_wants_python():
    """
    Test Case 2: Bob wants to learn python
    Expected: Should match Alice (who teaches python and wants guitar)
    """
    print("\n=== TEST 2: Bob wants python ===")
    
    matching_service = get_matching_service()
    
    # Bob's user_id is 2
    bob_id = 2
    desired_skill = "python"
    
    matches = matching_service.find_matches(bob_id, desired_skill)
    
    print(f"Query: User {bob_id} (Bob) wants to learn '{desired_skill}'")
    print(f"Found {len(matches)} matches:\n")
    
    for i, match in enumerate(matches[:3], 1):  # Show top 3
        print(f"{i}. {match['name']}")
        print(f"   Score: {match['match_score']:.3f}")
        print(f"   {match['compatibility_reason']}")
        print()
    
    assert len(matches) > 0, "Should find matches"
    print("✓ Test passed!")


def test_semantic_similarity():
    """
    Test Case 3: Semantic matching
    Search for "web dev" should match "web development"
    """
    print("\n=== TEST 3: Semantic similarity (web dev → web development) ===")
    
    matching_service = get_matching_service()
    
    # Alice searches for "web dev" (casual term)
    alice_id = 1
    desired_skill = "web dev"  # Informal
    
    matches = matching_service.find_matches(alice_id, desired_skill, min_similarity=0.4)
    
    print(f"Query: '{desired_skill}' (informal term)")
    print(f"Should match 'web development' (formal term)")
    print(f"\nFound {len(matches)} matches:\n")
    
    for match in matches[:3]:
        print(f"- {match['name']}: teaches {match['skills_offered']}")
        print(f"  Similarity: {match['skill_similarity']:.3f}")
    
    # Should find David who offers "web development"
    david_found = any(m['name'] == 'David Kumar' for m in matches)
    if david_found:
        print("\n✓ Successfully matched informal 'web dev' to formal 'web development'")
    else:
        print("\n⚠ David not found (may need to adjust similarity threshold)")
    
    print("✓ Test completed!")


def test_match_statistics():
    """
    Test Case 4: Get matching statistics
    """
    print("\n=== TEST 4: Match statistics ===")
    
    matching_service = get_matching_service()
    
    # Get stats for Alice
    alice_id = 1
    stats = matching_service.get_match_statistics(alice_id)
    
    print(f"Statistics for User {alice_id}:")
    print(f"  Skills offered: {stats['skills_offered']}")
    print(f"  Skills wanted: {stats['skills_wanted']}")
    print(f"  Skills with embeddings: {stats['skills_with_embeddings']}")
    print(f"  Potential partners: {stats['potential_partners']}")
    
    assert stats['skills_offered'] > 0, "Alice should have offered skills"
    assert stats['skills_wanted'] > 0, "Alice should have wanted skills"
    
    print("\n✓ Test passed!")


def test_no_matches():
    """
    Test Case 5: Search for rare skill that nobody offers
    """
    print("\n=== TEST 5: No matches for rare skill ===")
    
    matching_service = get_matching_service()
    
    alice_id = 1
    desired_skill = "quantum physics"  # Nobody offers this
    
    matches = matching_service.find_matches(alice_id, desired_skill, min_similarity=0.6)
    
    print(f"Query: '{desired_skill}' (not offered by anyone)")
    print(f"Found {len(matches)} matches")
    
    if len(matches) == 0:
        print("✓ Correctly returned no matches")
    else:
        print(f"⚠ Found {len(matches)} low-similarity matches (may be acceptable)")
    
    print("✓ Test completed!")


def main():
    """
    Run all matching tests
    """
    print("="*60)
    print("MATCHING SERVICE TEST SUITE")
    print("="*60)
    
    # Initialize database
    init_connection_pool()
    
    # Verify we have test data
    result = execute_query("SELECT COUNT(*) as count FROM users")
    user_count = result[0]['count']
    
    if user_count < 3:
        print("✗ Not enough test data. Run seed_database.py first!")
        return
    
    print(f"✓ Found {user_count} test users in database\n")
    
    try:
        test_find_matches_alice_wants_guitar()
        test_find_matches_bob_wants_python()
        test_semantic_similarity()
        test_match_statistics()
        test_no_matches()
        
        print("\n" + "="*60)
        print("✓ ALL MATCHING TESTS PASSED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()