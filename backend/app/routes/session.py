# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from datetime import datetime, timezone
# from app.models.qa_verdict import QAVerdict
# from app.db.database import get_db
# from app.models.barter import Barter
# from app.models.session_contract import SessionContract
# from app.models.confirmation import Confirmation
# from app.schemas.session import (
#     SessionCreateRequest,
#     SessionCreateResponse,
#     SessionStartResponse,
#     SessionConfirmRequest,
#     SessionConfirmResponse,
#     SessionStatusResponse,
#     SessionTerminateRequest,
#     SessionTerminateResponse,
#     DriftSummaryRequest,
#     DriftSummaryResponse,
# )
# import json
# from datetime import datetime, timezone
# import requests
# from app.services.integration_service import (
#     notify_contract_service,
#     notify_monitoring_service,
#     notify_completion_service
# )

# router = APIRouter(prefix="/session", tags=["Session Lifecycle"])


# @router.post("/create", response_model=SessionCreateResponse)
# def create_session(request: SessionCreateRequest, db: Session = Depends(get_db)):
#     user_a_id = 1
#     user_b_id = 2

#     barter = Barter(
#         user_a_id=user_a_id,
#         user_b_id=user_b_id,
#         skill_a=request.skill_a,
#         skill_b=request.skill_b,
#         status="proposed"
#     )
#     db.add(barter)
#     db.commit()
#     db.refresh(barter)

#     notify_contract_service(barter.barter_id)

#     contract = SessionContract(
#         barter_id=barter.barter_id,
#         topic=request.topic,
#         scope=request.scope,
#         allowed_concepts=",".join(request.allowed_concepts),
#         disallowed_concepts=",".join(request.disallowed_concepts),
#         agreed_duration_minutes=request.agreed_duration_minutes
#     )
#     db.add(contract)
#     db.commit()
#     db.refresh(contract)

#     return SessionCreateResponse(
#         barter_id=barter.barter_id,
#         contract_id=contract.contract_id,
#         status=barter.status
#     )


# @router.post("/{barter_id}/start", response_model=SessionStartResponse)
# def start_session(barter_id: int, db: Session = Depends(get_db)):
#     barter = db.query(Barter).filter(Barter.barter_id == barter_id).first()
#     if not barter:
#         raise HTTPException(status_code=404, detail="Barter not found")

#     contract = db.query(SessionContract).filter(SessionContract.barter_id == barter_id).first()
#     if not contract:
#         raise HTTPException(status_code=404, detail="Session contract not found")

#     contract.started_at = datetime.now(timezone.utc)
#     barter.status = "active"

#     db.commit()
#     db.refresh(contract)
#     db.refresh(barter)

#     return SessionStartResponse(
#         barter_id=barter.barter_id,
#         started_at=contract.started_at,
#         status=barter.status
#     )


# @router.post("/{barter_id}/confirm", response_model=SessionConfirmResponse)
# def confirm_session(barter_id: int, request: SessionConfirmRequest, db: Session = Depends(get_db)):
#     barter = db.query(Barter).filter(Barter.barter_id == barter_id).first()
#     if not barter:
#         raise HTTPException(status_code=404, detail="Barter not found")

#     if request.user_id not in [barter.user_a_id, barter.user_b_id]:
#         raise HTTPException(status_code=400, detail="User is not part of this barter")

#     existing_confirmation = (
#         db.query(Confirmation)
#         .filter(
#             Confirmation.barter_id == barter_id,
#             Confirmation.user_id == request.user_id
#         )
#         .first()
#     )

#     if existing_confirmation:
#         raise HTTPException(status_code=400, detail="User already confirmed this session")

#     confirmation = Confirmation(
#         barter_id=barter_id,
#         user_id=request.user_id
#     )
#     db.add(confirmation)
#     db.commit()

#     confirmations = db.query(Confirmation).filter(Confirmation.barter_id == barter_id).all()
#     confirmed_by = [c.user_id for c in confirmations]

#     both_confirmed = (
#         barter.user_a_id in confirmed_by and barter.user_b_id in confirmed_by
#     )

#     if both_confirmed:
#         barter.status = "completed"
#         contract = db.query(SessionContract).filter(SessionContract.barter_id == barter_id).first()
#         if contract:
#             contract.completed_at = datetime.now(timezone.utc)
#         db.commit()

#     return SessionConfirmResponse(
#         barter_id=barter_id,
#         confirmed_by=confirmed_by,
#         both_confirmed=both_confirmed
#     )


# @router.get("/{barter_id}/status", response_model=SessionStatusResponse)
# def get_session_status(barter_id: int, db: Session = Depends(get_db)):
#     barter = db.query(Barter).filter(Barter.barter_id == barter_id).first()
#     if not barter:
#         raise HTTPException(status_code=404, detail="Barter not found")

#     contract = db.query(SessionContract).filter(SessionContract.barter_id == barter_id).first()
#     if not contract:
#         raise HTTPException(status_code=404, detail="Session contract not found")

#     confirmations = db.query(Confirmation).filter(Confirmation.barter_id == barter_id).all()
#     confirmed_by = [c.user_id for c in confirmations]

#     both_confirmed = (
#         barter.user_a_id in confirmed_by and barter.user_b_id in confirmed_by
#     )

#     elapsed_minutes = 0
#     if contract.started_at:
#         now = datetime.now(timezone.utc)
#         started_at = contract.started_at

#         if started_at.tzinfo is None:
#             started_at = started_at.replace(tzinfo=timezone.utc)

#         elapsed_minutes = int((now - started_at).total_seconds() // 60)

#     can_complete = barter.status in ["active", "completed"]

#     return SessionStatusResponse(
#         barter_id=barter_id,
#         status=barter.status,
#         elapsed_minutes=elapsed_minutes,
#         agreed_duration_minutes=contract.agreed_duration_minutes,
#         can_complete=can_complete,
#         both_confirmed=both_confirmed
#     )


# @router.post("/{barter_id}/terminate", response_model=SessionTerminateResponse)
# def terminate_session(barter_id: int, request: SessionTerminateRequest, db: Session = Depends(get_db)):
#     barter = db.query(Barter).filter(Barter.barter_id == barter_id).first()
#     if not barter:
#         raise HTTPException(status_code=404, detail="Barter not found")

#     contract = db.query(SessionContract).filter(SessionContract.barter_id == barter_id).first()
#     if not contract:
#         raise HTTPException(status_code=404, detail="Session contract not found")

#     barter.status = "terminated"
#     contract.completed_at = datetime.now(timezone.utc)

#     existing_verdict = db.query(QAVerdict).filter(QAVerdict.barter_id == barter_id).first()
#     if not existing_verdict:
#         verdict = QAVerdict(
#             barter_id=barter_id,
#             verdict="DISPUTE",
#             duration_check=False,
#             confirmation_check=False,
#             drift_summary=request.reason
#         )
#         db.add(verdict)

#     db.commit()

#     return SessionTerminateResponse(
#         barter_id=barter_id,
#         status=barter.status
#     )


# @router.post("/{barter_id}/drift-summary", response_model=DriftSummaryResponse)
# def receive_drift_summary(barter_id: int, request: DriftSummaryRequest, db: Session = Depends(get_db)):
#     barter = db.query(Barter).filter(Barter.barter_id == barter_id).first()
#     if not barter:
#         raise HTTPException(status_code=404, detail="Barter not found")

#     contract = db.query(SessionContract).filter(SessionContract.barter_id == barter_id).first()
#     if not contract:
#         raise HTTPException(status_code=404, detail="Session contract not found")

#     confirmations = db.query(Confirmation).filter(Confirmation.barter_id == barter_id).all()
#     confirmed_by = [c.user_id for c in confirmations]

#     both_confirmed = (
#         barter.user_a_id in confirmed_by and barter.user_b_id in confirmed_by
#     )

#     duration_check = False
#     if contract.started_at and contract.completed_at:
#         started_at = contract.started_at
#         completed_at = contract.completed_at

#         if started_at.tzinfo is None:
#             started_at = started_at.replace(tzinfo=timezone.utc)
#         if completed_at.tzinfo is None:
#             completed_at = completed_at.replace(tzinfo=timezone.utc)

#         actual_minutes = (completed_at - started_at).total_seconds() / 60
#         duration_check = actual_minutes >= (0.8 * contract.agreed_duration_minutes)

#     confirmation_check = both_confirmed

#     if request.terminated_early:
#         verdict = "DISPUTE"
#     elif duration_check and confirmation_check:
#         verdict = "SUCCESSFUL"
#     elif duration_check or confirmation_check:
#         verdict = "PARTIAL"
#     else:
#         verdict = "DISPUTE"

#     drift_summary_data = {
#         "total_windows": request.total_windows,
#         "incorrect_windows": request.incorrect_windows,
#         "percent_incorrect": request.percent_incorrect,
#         "max_consecutive_incorrect": request.max_consecutive_incorrect,
#         "warning_count": request.warning_count,
#         "terminated_early": request.terminated_early
#     }

#     existing_verdict = db.query(QAVerdict).filter(QAVerdict.barter_id == barter_id).first()
#     if existing_verdict:
#         existing_verdict.verdict = verdict
#         existing_verdict.duration_check = duration_check
#         existing_verdict.confirmation_check = confirmation_check
#         existing_verdict.drift_summary = json.dumps(drift_summary_data)
#     else:
#         qa_verdict = QAVerdict(
#             barter_id=barter_id,
#             verdict=verdict,
#             duration_check=duration_check,
#             confirmation_check=confirmation_check,
#             drift_summary=json.dumps(drift_summary_data)
#         )
#         db.add(qa_verdict)

#     db.commit()

#     return DriftSummaryResponse(
#     message="Drift summary received and verdict generated successfully",
#     barter_id=barter_id,
#     verdict=verdict,
#     duration_check=duration_check,
#     confirmation_check=confirmation_check
# )


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.qa_verdict import QAVerdict
from app.db.database import get_db
from app.models.barter import Barter
from app.models.session_contract import SessionContract
from app.models.confirmation import Confirmation
from app.schemas.session import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionStartResponse,
    SessionConfirmRequest,
    SessionConfirmResponse,
    SessionStatusResponse,
    SessionTerminateRequest,
    SessionTerminateResponse,
    DriftSummaryRequest,
    DriftSummaryResponse,
)
import json
from app.services.integration_service import (
    notify_contract_service,
    notify_monitoring_service,
    notify_completion_service
)

router = APIRouter(prefix="/session", tags=["Session Lifecycle"])


# ✅ CREATE SESSION
@router.post("/create", response_model=SessionCreateResponse)
def create_session(request: SessionCreateRequest, db: Session = Depends(get_db)):
    user_a_id = 1
    user_b_id = 2

    barter = Barter(
        user_a_id=user_a_id,
        user_b_id=user_b_id,
        skill_a=request.skill_a,
        skill_b=request.skill_b,
        status="proposed"
    )
    db.add(barter)
    db.commit()
    db.refresh(barter)

    # 🔥 ADDED (Notify Contract Service)
    notify_contract_service(barter.barter_id)

    contract = SessionContract(
        barter_id=barter.barter_id,
        topic=request.topic,
        scope=request.scope,
        allowed_concepts=",".join(request.allowed_concepts),
        disallowed_concepts=",".join(request.disallowed_concepts),
        agreed_duration_minutes=request.agreed_duration_minutes
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    return SessionCreateResponse(
        barter_id=barter.barter_id,
        contract_id=contract.contract_id,
        status=barter.status
    )


# ✅ START SESSION
@router.post("/{barter_id}/start", response_model=SessionStartResponse)
def start_session(barter_id: int, db: Session = Depends(get_db)):
    barter = db.query(Barter).filter(Barter.barter_id == barter_id).first()
    if not barter:
        raise HTTPException(status_code=404, detail="Barter not found")

    contract = db.query(SessionContract).filter(SessionContract.barter_id == barter_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Session contract not found")

    contract.started_at = datetime.now(timezone.utc)
    barter.status = "active"

    db.commit()
    db.refresh(contract)
    db.refresh(barter)

    # 🔥 ADDED (Notify Monitoring Service)
    notify_monitoring_service(barter.barter_id)

    return SessionStartResponse(
        barter_id=barter.barter_id,
        started_at=contract.started_at,
        status=barter.status
    )


# ✅ CONFIRM SESSION
@router.post("/{barter_id}/confirm", response_model=SessionConfirmResponse)
def confirm_session(barter_id: int, request: SessionConfirmRequest, db: Session = Depends(get_db)):
    barter = db.query(Barter).filter(Barter.barter_id == barter_id).first()
    if not barter:
        raise HTTPException(status_code=404, detail="Barter not found")

    if request.user_id not in [barter.user_a_id, barter.user_b_id]:
        raise HTTPException(status_code=400, detail="User is not part of this barter")

    existing_confirmation = (
        db.query(Confirmation)
        .filter(
            Confirmation.barter_id == barter_id,
            Confirmation.user_id == request.user_id
        )
        .first()
    )

    if existing_confirmation:
        raise HTTPException(status_code=400, detail="User already confirmed this session")

    confirmation = Confirmation(
        barter_id=barter_id,
        user_id=request.user_id
    )
    db.add(confirmation)
    db.commit()

    confirmations = db.query(Confirmation).filter(Confirmation.barter_id == barter_id).all()
    confirmed_by = [c.user_id for c in confirmations]

    both_confirmed = (
        barter.user_a_id in confirmed_by and barter.user_b_id in confirmed_by
    )

    if both_confirmed:
        barter.status = "completed"
        contract = db.query(SessionContract).filter(SessionContract.barter_id == barter_id).first()
        if contract:
            contract.completed_at = datetime.now(timezone.utc)
        db.commit()

    return SessionConfirmResponse(
        barter_id=barter_id,
        confirmed_by=confirmed_by,
        both_confirmed=both_confirmed
    )


# ✅ SESSION STATUS
@router.get("/{barter_id}/status", response_model=SessionStatusResponse)
def get_session_status(barter_id: int, db: Session = Depends(get_db)):
    barter = db.query(Barter).filter(Barter.barter_id == barter_id).first()
    if not barter:
        raise HTTPException(status_code=404, detail="Barter not found")

    contract = db.query(SessionContract).filter(SessionContract.barter_id == barter_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Session contract not found")

    confirmations = db.query(Confirmation).filter(Confirmation.barter_id == barter_id).all()
    confirmed_by = [c.user_id for c in confirmations]

    both_confirmed = (
        barter.user_a_id in confirmed_by and barter.user_b_id in confirmed_by
    )

    elapsed_minutes = 0
    if contract.started_at:
        now = datetime.now(timezone.utc)
        started_at = contract.started_at

        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)

        elapsed_minutes = int((now - started_at).total_seconds() // 60)

    can_complete = barter.status in ["active", "completed"]

    return SessionStatusResponse(
        barter_id=barter_id,
        status=barter.status,
        elapsed_minutes=elapsed_minutes,
        agreed_duration_minutes=contract.agreed_duration_minutes,
        can_complete=can_complete,
        both_confirmed=both_confirmed
    )


# ✅ TERMINATE SESSION
@router.post("/{barter_id}/terminate", response_model=SessionTerminateResponse)
def terminate_session(barter_id: int, request: SessionTerminateRequest, db: Session = Depends(get_db)):
    barter = db.query(Barter).filter(Barter.barter_id == barter_id).first()
    if not barter:
        raise HTTPException(status_code=404, detail="Barter not found")

    contract = db.query(SessionContract).filter(SessionContract.barter_id == barter_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Session contract not found")

    barter.status = "terminated"
    contract.completed_at = datetime.now(timezone.utc)

    existing_verdict = db.query(QAVerdict).filter(QAVerdict.barter_id == barter_id).first()
    if not existing_verdict:
        verdict = QAVerdict(
            barter_id=barter_id,
            verdict="DISPUTE",
            duration_check=False,
            confirmation_check=False,
            drift_summary=request.reason
        )
        db.add(verdict)

    db.commit()

    return SessionTerminateResponse(
        barter_id=barter_id,
        status=barter.status
    )


# ✅ DRIFT SUMMARY + FINAL COMPLETION
@router.post("/{barter_id}/drift-summary", response_model=DriftSummaryResponse)
def receive_drift_summary(barter_id: int, request: DriftSummaryRequest, db: Session = Depends(get_db)):
    barter = db.query(Barter).filter(Barter.barter_id == barter_id).first()
    if not barter:
        raise HTTPException(status_code=404, detail="Barter not found")

    contract = db.query(SessionContract).filter(SessionContract.barter_id == barter_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Session contract not found")

    confirmations = db.query(Confirmation).filter(Confirmation.barter_id == barter_id).all()
    confirmed_by = [c.user_id for c in confirmations]

    both_confirmed = (
        barter.user_a_id in confirmed_by and barter.user_b_id in confirmed_by
    )

    duration_check = False
    if contract.started_at and contract.completed_at:
        started_at = contract.started_at
        completed_at = contract.completed_at

        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=timezone.utc)

        actual_minutes = (completed_at - started_at).total_seconds() / 60
        duration_check = actual_minutes >= (0.8 * contract.agreed_duration_minutes)

    confirmation_check = both_confirmed

    if request.terminated_early:
        verdict = "DISPUTE"
    elif duration_check and confirmation_check:
        verdict = "SUCCESSFUL"
    elif duration_check or confirmation_check:
        verdict = "PARTIAL"
    else:
        verdict = "DISPUTE"

    drift_summary_data = {
        "total_windows": request.total_windows,
        "incorrect_windows": request.incorrect_windows,
        "percent_incorrect": request.percent_incorrect,
        "max_consecutive_incorrect": request.max_consecutive_incorrect,
        "warning_count": request.warning_count,
        "terminated_early": request.terminated_early
    }

    existing_verdict = db.query(QAVerdict).filter(QAVerdict.barter_id == barter_id).first()
    if existing_verdict:
        existing_verdict.verdict = verdict
        existing_verdict.duration_check = duration_check
        existing_verdict.confirmation_check = confirmation_check
        existing_verdict.drift_summary = json.dumps(drift_summary_data)
    else:
        qa_verdict = QAVerdict(
            barter_id=barter_id,
            verdict=verdict,
            duration_check=duration_check,
            confirmation_check=confirmation_check,
            drift_summary=json.dumps(drift_summary_data)
        )
        db.add(qa_verdict)

    db.commit()

    # 🔥 ADDED (Notify Completion Service)
    notify_completion_service(barter_id)

    return DriftSummaryResponse(
        message="Drift summary received and verdict generated successfully",
        barter_id=barter_id,
        verdict=verdict,
        duration_check=duration_check,
        confirmation_check=confirmation_check
    )