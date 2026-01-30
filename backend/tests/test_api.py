"""
Test FastAPI matching endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_health_check():
    """Test health check endpoint"""
    print("\n=== TEST 1: Health Check ===")
    
    response = requests.get(f"{BASE_URL}/matching/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
    
    print("✓ Health check passed!")


def test_find_matches():
    """Test finding matches"""
    print("\n=== TEST 2: Find Matches ===")
    
    payload = {
        "desired_skill": "guitar",
        "min_similarity": 0.5,
        "max_results": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/matching/request",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Total Matches: {data['total_matches']}")
    
    for i, match in enumerate(data['matches'], 1):
        print(f"\n{i}. {match['name']}")
        print(f"   Score: {match['match_score']}")
        print(f"   Explanation: {match['compatibility_reason']}")
    
    assert response.status_code == 200
    assert data['total_matches'] > 0
    
    print("\n✓ Find matches passed!")


def test_accept_match():
    """Test accepting a match"""
    print("\n=== TEST 3: Accept Match ===")
    
    payload = {
        "match_user_id": 2,
        "your_skill": "python programming",
        "their_skill": "guitar"
    }
    
    response = requests.post(
        f"{BASE_URL}/matching/accept",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 201
    
    print("✓ Accept match passed!")


def test_get_statistics():
    """Test getting match statistics"""
    print("\n=== TEST 4: Get Statistics ===")
    
    response = requests.get(f"{BASE_URL}/matching/statistics")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    
    print("✓ Get statistics passed!")


def main():
    print("="*60)
    print("MATCHING API TEST SUITE")
    print("="*60)
    print("\nMake sure API is running: uvicorn app.main:app --reload")
    print()
    
    try:
        test_health_check()
        test_find_matches()
        test_accept_match()
        test_get_statistics()
        
        print("\n" + "="*60)
        print("✓ ALL API TESTS PASSED!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to API. Is it running?")
        print("Run: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()