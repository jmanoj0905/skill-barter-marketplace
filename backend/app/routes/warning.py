from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.barter import Barter
from app.models.warning import Warning
from app.schemas.warning import WarningLogRequest, WarningLogResponse
from app.services.warning_ws_manager import manager

router = APIRouter(prefix="/warnings", tags=["Warnings"])


@router.post("/log", response_model=WarningLogResponse)
async def log_warning(request: WarningLogRequest, db: Session = Depends(get_db)):
    barter = db.query(Barter).filter(Barter.barter_id == request.barter_id).first()
    if not barter:
        raise HTTPException(status_code=404, detail="Barter not found")

    warning = Warning(
        barter_id=request.barter_id,
        severity=request.severity,
        reason=request.reason,
        window_ids=request.window_ids,
        timestamp=request.timestamp
    )
    db.add(warning)
    db.commit()
    db.refresh(warning)

    await manager.broadcast(
        request.barter_id,
        {
            "warning_id": warning.warning_id,
            "barter_id": warning.barter_id,
            "severity": warning.severity,
            "reason": warning.reason,
            "window_ids": warning.window_ids,
            "timestamp": str(warning.timestamp)
        }
    )

    return WarningLogResponse(warning_id=warning.warning_id)


@router.websocket("/ws/{barter_id}")
async def warning_websocket(websocket: WebSocket, barter_id: int):
    await manager.connect(barter_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(barter_id, websocket)