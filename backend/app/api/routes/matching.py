"""
Matching API Routes
Endpoints for finding and accepting barter matches
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.services.matching_service import get_matching_service
from backend.app.core.database import get_connection, return_connection, execute_query
from psycopg2.extras import RealDictCursor
from datetime import datetime

router = APIRouter(prefix="/matching", tags=["matching"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class MatchingRequest(BaseModel):
    """Request body for finding matches"""
    desired_skill: str = Field(..., min_length=1, max_length=100)
    min_similarity: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    max_results: Optional[int] = Field(5, ge=1, le=20)


class MatchResponse(BaseModel):
    """Single match result"""
    user_id: int
    name: str
    trust_score: float
    skills_offered: List[str]
    skills_wanted: List[str]
    match_score: float
    skill_similarity: float
    has_mutual_interest: bool
    mutual_skill: Optional[str]
    compatibility_reason: str


class MatchingResponse(BaseModel):
    """Response containing all matches"""
    matches: List[MatchResponse]
    total_matches: int


class AcceptMatchRequest(BaseModel):
    """Request body for accepting a match"""
    match_user_id: int
    your_skill: str = Field(..., min_length=1, max_length=50)
    their_skill: str = Field(..., min_length=1, max_length=50)


class AcceptMatchResponse(BaseModel):
    """Response after accepting a match"""
    barter_id: int
    chat_id: int
    status: str
    user_a_id: int
    user_b_id: int
    skill_a: str
    skill_b: str
    proposed_at: str
    message: str

class MatchRejectRequest(BaseModel):
    candidate_user_id: int

# ============================================
# TEMPORARY AUTH (Replace with real JWT later)
# ============================================

def get_current_user_id() -> int:
    """
    Get current authenticated user ID
    
    TODO: Replace with actual JWT authentication from your auth system
    For now, returns hardcoded user ID for testing Phase 4
    """
    return 7  # bob for testing


# ============================================
# API ENDPOINTS
# ============================================

@router.post("/request", response_model=MatchingResponse)
async def find_matches(
    request: MatchingRequest,
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Find potential barter partners based on desired skill
    
    Uses AI-powered semantic matching with multi-factor scoring
    """
    try:
        matching_service = get_matching_service()
        conn = get_connection()
        try:
            matching_service.validate_match_request(current_user_id, conn)
        finally:
            return_connection(conn)
        
        matches = matching_service.find_matches(
            user_id=current_user_id,
            desired_skill=request.desired_skill,
            min_similarity=request.min_similarity,
            max_results=request.max_results
        )
        
        match_responses = [
            MatchResponse(**m) for m in matches
        ]
        
        return MatchingResponse(
            matches=match_responses,
            total_matches=len(match_responses)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding matches: {str(e)}")


@router.post("/accept", response_model=AcceptMatchResponse, status_code=201)
async def accept_match(
    request: AcceptMatchRequest,
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Accept a match and create a barter proposal
    """
    # Validate: Cannot match with yourself
    if current_user_id == request.match_user_id:
        raise HTTPException(status_code=400, detail="Cannot barter with yourself")
    
    # Check if user exists
    user_check = execute_query(
        "SELECT id, name FROM users WHERE id = %s",
        (request.match_user_id,)
    )
    if not user_check:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check for existing active barter
    existing = execute_query(
        """
        SELECT id FROM barters
        WHERE ((user_a_id = %s AND user_b_id = %s) OR (user_a_id = %s AND user_b_id = %s))
          AND status NOT IN ('settled', 'disputed')
        """,
        (current_user_id, request.match_user_id, request.match_user_id, current_user_id)
    )
    if existing:
        raise HTTPException(status_code=400, detail="Active barter already exists with this user")
    
    # Step 1: create match record
    matching_service = get_matching_service()
    match_id = matching_service._create_match_record(
        requester_id=current_user_id,
        partner_id=request.match_user_id
    )

    # Step 2: create barter
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute(
            """
            INSERT INTO barters (user_a_id, user_b_id, skill_a, skill_b, status, proposed_at)
            VALUES (%s, %s, %s, %s, 'proposed', %s)
            RETURNING id, user_a_id, user_b_id, skill_a, skill_b, status, proposed_at
            """,
            (current_user_id, request.match_user_id, request.your_skill, 
             request.their_skill, datetime.utcnow())
        )
        
        barter = cursor.fetchone()
        conn.commit()
        
        return AcceptMatchResponse(
            barter_id=barter['id'],
            chat_id=barter['id'],
            status=barter['status'],
            user_a_id=barter['user_a_id'],
            user_b_id=barter['user_b_id'],
            skill_a=barter['skill_a'],
            skill_b=barter['skill_b'],
            proposed_at=barter['proposed_at'].isoformat() + 'Z',
            message=f"Match accepted! (Match ID: {match_id}) You can now chat with {user_check[0]['name']}"
        )
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating barter: {str(e)}")
    finally:
        cursor.close()
        return_connection(conn)


@router.get("/statistics")
async def get_statistics(current_user_id: int = Depends(get_current_user_id)):
    """Get matching statistics for current user"""
    try:
        matching_service = get_matching_service()
        return matching_service.get_match_statistics(current_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reject", status_code=200)
async def reject_match(
    request: MatchRejectRequest,
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Reject a suggested match.
    Phase 4: Rejections are not persisted.
    """
    if request.candidate_user_id == current_user_id:
        raise HTTPException(status_code=400, detail="Cannot reject yourself")

    # Phase 4 design choice:
    # Matching is ephemeral → no DB write here

    return {
        "message": "Match rejected successfully"
    }


@router.get("/health")
async def health_check():
    """Health check for matching service"""
    try:
        matching_service = get_matching_service()
        return {
            "status": "healthy",
            "service": "matching",
            "embedding_model_loaded": matching_service.embedding_service.model is not None
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}