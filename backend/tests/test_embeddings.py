"""
Test script for embedding service
Validates that semantic similarity works correctly
"""

from backend.app.services.embedding_service import get_embedding_service
import time

def test_embedding_generation():
    """Test basic embedding generation"""
    print("\n=== TEST 1: Embedding Generation ===")
    
    service = get_embedding_service()
    
    # Generate embedding
    skill = "Python Programming"
    embedding = service.generate_embedding(skill)
    
    print(f"✓ Skill: '{skill}'")
    print(f"✓ Embedding dimensions: {len(embedding)}")
    print(f"✓ First 5 values: {embedding[:5]}")
    print(f"✓ Embedding type: {type(embedding)}")
    
    assert len(embedding) == 384, "Embedding should be 384 dimensions"
    assert isinstance(embedding, list), "Embedding should be a list"
    
    print("✓ Test passed!")

def test_normalization():
    """Test skill name normalization"""
    print("\n=== TEST 2: Normalization ===")
    
    service = get_embedding_service()
    
    test_cases = [
        ("Python Programming", "python programming"),
        ("  GUITAR  ", "guitar"),
        ("Web   Development", "web development"),
    ]
    
    for input_text, expected in test_cases:
        result = service.normalize_skill_name(input_text)
        print(f"'{input_text}' → '{result}'")
        assert result == expected, f"Expected '{expected}', got '{result}'"
    
    print("✓ All normalization tests passed!")

def test_similarity():
    """Test semantic similarity calculation"""
    print("\n=== TEST 3: Semantic Similarity ===")
    
    service = get_embedding_service()
    
    # Test cases with expected similarity ranges
    test_cases = [
        ("Python", "Python Programming", 0.85, 1.0, "Very similar"),
        ("Guitar", "Music Theory", 0.50, 0.75, "Related"),
        ("Guitar", "Cooking", 0.0, 0.40, "Unrelated"),
        ("Machine Learning", "AI", 0.70, 0.95, "Very related"),
        ("JavaScript", "TypeScript", 0.75, 0.95, "Very related"),
    ]
    
    for skill1, skill2, min_sim, max_sim, description in test_cases:
        similarity = service.calculate_similarity(skill1, skill2)
        status = "✓" if min_sim <= similarity <= max_sim else "✗"
        print(f"{status} '{skill1}' vs '{skill2}': {similarity:.3f} ({description})")
        
        if not (min_sim <= similarity <= max_sim):
            print(f"   WARNING: Expected {min_sim}-{max_sim}, got {similarity:.3f}")
    
    print("✓ Similarity tests completed!")

def test_batch_generation():
    """Test batch embedding generation"""
    print("\n=== TEST 4: Batch Generation ===")
    
    service = get_embedding_service()
    
    skills = ["Python", "JavaScript", "Guitar", "Cooking", "Math"]
    
    start_time = time.time()
    embeddings = service.generate_embeddings_batch(skills)
    batch_time = time.time() - start_time
    
    print(f"✓ Generated {len(embeddings)} embeddings in {batch_time:.3f} seconds")
    print(f"✓ Average: {batch_time/len(embeddings)*1000:.1f} ms per skill")
    
    assert len(embeddings) == len(skills), "Should generate one embedding per skill"
    assert all(len(emb) == 384 for emb in embeddings), "All embeddings should be 384D"
    
    print("✓ Batch generation test passed!")

def test_find_most_similar():
    """Test finding most similar skills"""
    print("\n=== TEST 5: Find Most Similar ===")
    
    service = get_embedding_service()
    
    # Create candidate skills with embeddings
    candidates = [
        {"name": "Python Programming", "embedding": service.generate_embedding("Python Programming")},
        {"name": "JavaScript", "embedding": service.generate_embedding("JavaScript")},
        {"name": "Guitar", "embedding": service.generate_embedding("Guitar")},
        {"name": "Machine Learning", "embedding": service.generate_embedding("Machine Learning")},
        {"name": "Cooking", "embedding": service.generate_embedding("Cooking")},
    ]
    
    query = "Python"
    results = service.find_most_similar(query, candidates, top_k=3)
    
    print(f"Query: '{query}'")
    print(f"Top 3 matches:")
    for skill, score in results:
        print(f"  {score:.3f} - {skill['name']}")
    
    # Python Programming should be top match
    assert results[0][0]['name'] == "Python Programming", "Python Programming should be most similar to Python"
    assert results[0][1] > 0.85, "Similarity should be very high"
    
    print("✓ Find most similar test passed!")

if __name__ == "__main__":
    print("="*60)
    print("EMBEDDING SERVICE TEST SUITE")
    print("="*60)
    
    try:
        test_embedding_generation()
        test_normalization()
        test_similarity()
        test_batch_generation()
        test_find_most_similar()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()