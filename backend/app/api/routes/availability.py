from fastapi import APIRouter, HTTPException, Query
from backend.app.services.matching_service import get_matching_service
from fastapi import Body
from backend.app.schemas.availability import AvailabilityCreate
from backend.app.core.database import get_connection, return_connection
router = APIRouter(prefix="/api/availability", tags=["availability"])

@router.post("/")
def add_availability(
    data: AvailabilityCreate,
    user_id: int = 1   # TEMP (later from auth)
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO availability (user_id, day_of_week, start_time, end_time, timezone)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_id,
            data.day_of_week,
            data.start_time,
            data.end_time,
            data.timezone
        ))

        conn.commit()

        return {
            "message": "Availability added",
            "availability_id": cursor.fetchone()[0]
        }

    finally:
        cursor.close()
        return_connection(conn)

@router.get("/overlap")
def get_availability_overlap(
    user_a: int = Query(...),
    user_b: int = Query(...)
):
    """
    Get weekly availability overlap between two users
    """

    service = get_matching_service()

    try:
        overlap_score = service._calculate_schedule_overlap(user_a, user_b)

        # Convert score back to hours (since 10 hrs = 1.0)
        overlap_hours = overlap_score * 10

        return {
            "user_a": user_a,
            "user_b": user_b,
            "overlap_score": round(overlap_score, 3),
            "overlap_hours_per_week": round(overlap_hours, 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))