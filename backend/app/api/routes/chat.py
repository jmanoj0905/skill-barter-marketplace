from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from psycopg2.extras import RealDictCursor

from app.core.database import get_connection, return_connection
from app.api.routes.matching import get_current_user_id

router = APIRouter(prefix="/chat", tags=["chat"])


class SendMessageRequest(BaseModel):
    barter_id: int
    content: str = Field(..., min_length=1, max_length=5000)


class SendMessageResponse(BaseModel):
    message_id: int
    barter_id: int
    sender_id: int
    content: str
    sent_at: str

@router.post("/send", response_model=SendMessageResponse, status_code=201)
async def send_message(
    request: SendMessageRequest,
    current_user_id: int = Depends(get_current_user_id)
):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1️⃣ Validate barter & participant
        cursor.execute(
            """
            SELECT id, user_a_id, user_b_id
            FROM barters
            WHERE id = %s
            """,
            (request.barter_id,)
        )
        barter = cursor.fetchone()

        if not barter:
            raise HTTPException(status_code=404, detail="Barter not found")

        if current_user_id not in (barter['user_a_id'], barter['user_b_id']):
            raise HTTPException(status_code=403, detail="Not a participant in this chat")

        # 2️⃣ Insert message
        cursor.execute(
            """
            INSERT INTO chat_messages (barter_id, sender_id, content, sent_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id, barter_id, sender_id, content, sent_at
            """,
            (request.barter_id, current_user_id, request.content, datetime.utcnow())
        )

        message = cursor.fetchone()
        conn.commit()

        return SendMessageResponse(
            message_id=message['id'],
            barter_id=message['barter_id'],
            sender_id=message['sender_id'],
            content=message['content'],
            sent_at=message['sent_at'].isoformat() + "Z"
        )

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")
    finally:
        cursor.close()
        return_connection(conn)
