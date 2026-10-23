from datetime import datetime, timedelta
import ipaddress

from sqlalchemy.orm import Session

from app.models.device import DeviceFingerprint
from app.models.identity_score import IdentityConfidenceScore
from app.models.user import User


def _safe_breakdown(value):
    return value if isinstance(value, dict) else {}


def _is_public_ip(ip_address: str | None) -> bool:
    if not ip_address:
        return False

    try:
        parsed = ipaddress.ip_address(ip_address)
    except ValueError:
        return False

    # Ignore non-routable addresses to reduce false positives in local/dev/NAT networks.
    if (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_reserved
        or parsed.is_multicast
    ):
        return False

    return True


def derive_fraud_policy_action(fraud_score: int, fraud_level: str) -> dict:
    """Map score/level to a backend action plan.

    This function is intentionally deterministic so the same score always produces
    the same action and can be audited from persisted JSON records.
    """
    if fraud_score >= 80 or fraud_level == "high":
        return {
            "action": "restrict",
            "requires_step_up": True,
            "requires_manual_review": True,
        }

    if fraud_score >= 50 or fraud_level == "medium":
        return {
            "action": "step_up_verification",
            "requires_step_up": True,
            "requires_manual_review": False,
        }

    if fraud_score >= 25 or fraud_level == "low":
        return {
            "action": "monitor",
            "requires_step_up": False,
            "requires_manual_review": False,
        }

    return {
        "action": "allow",
        "requires_step_up": False,
        "requires_manual_review": False,
    }


def record_device_fingerprint(
    db: Session,
    user_id: int,
    fingerprint_hash: str | None,
    user_agent: str | None,
) -> None:
    if not fingerprint_hash:
        return

    now = datetime.utcnow()
    existing = (
        db.query(DeviceFingerprint)
        .filter(
            DeviceFingerprint.user_id == user_id,
            DeviceFingerprint.fingerprint_hash == fingerprint_hash,
        )
        .first()
    )

    if existing:
        existing.last_seen_at = now
        existing.user_agent = user_agent
        db.commit()
        return

    db.add(
        DeviceFingerprint(
            user_id=user_id,
            fingerprint_hash=fingerprint_hash,
            user_agent=user_agent,
            os_info="unknown",
            screen_resolution=None,
            timezone=None,
            language=None,
            is_trusted=True,
            created_at=now,
            last_seen_at=now,
        )
    )
    db.commit()


def evaluate_and_store_account_fraud(
    db: Session,
    user_id: int,
    event_type: str,
    fingerprint_hash: str | None,
    ip_address: str | None,
) -> dict:
    now = datetime.utcnow()

    shared_device_accounts = 0
    recent_same_fingerprint_events = 0

    if fingerprint_hash:
        shared_device_accounts = (
            db.query(DeviceFingerprint.user_id)
            .filter(DeviceFingerprint.fingerprint_hash == fingerprint_hash)
            .distinct()
            .count()
        )

        recent_same_fingerprint_events = (
            db.query(DeviceFingerprint)
            .filter(
                DeviceFingerprint.fingerprint_hash == fingerprint_hash,
                DeviceFingerprint.last_seen_at >= now - timedelta(minutes=10),
            )
            .count()
        )

    # Read latest JSON breakdown rows and count users with same ip in the last hour.
    ip_linked_users = set()
    if _is_public_ip(ip_address):
        recent_identity_rows = (
            db.query(IdentityConfidenceScore)
            .filter(IdentityConfidenceScore.updated_at >= now - timedelta(hours=1))
            .all()
        )
        for row in recent_identity_rows:
            meta = _safe_breakdown(row.breakdown)
            if meta.get("ip_address") == ip_address:
                ip_linked_users.add(row.user_id)

    shared_ip_accounts = len(ip_linked_users)

    ip_risk = min(35, max(0, shared_ip_accounts - 1) * 12)
    device_risk = min(45, max(0, shared_device_accounts - 1) * 20)
    time_risk = min(20, max(0, recent_same_fingerprint_events - 1) * 10)
    fraud_score = int(ip_risk + device_risk + time_risk)

    if fraud_score >= 80:
        fraud_level = "high"
    elif fraud_score >= 50:
        fraud_level = "medium"
    elif fraud_score >= 25:
        fraud_level = "low"
    else:
        fraud_level = "minimal"

    reasons = []
    if shared_device_accounts > 1:
        reasons.append(f"shared_fingerprint_with_{shared_device_accounts}_accounts")
    if shared_ip_accounts > 1:
        reasons.append(f"shared_ip_with_{shared_ip_accounts}_accounts_last_hour")
    if recent_same_fingerprint_events > 1:
        reasons.append("high_velocity_for_same_fingerprint")

    user = db.query(User).filter(User.id == user_id).first()
    confidence_score = user.trust_score if user else 0.3
    policy = derive_fraud_policy_action(fraud_score, fraud_level)

    summary = {
        "event_type": event_type,
        "fraud_score": fraud_score,
        "fraud_level": fraud_level,
        "policy_action": policy["action"],
        "requires_step_up": policy["requires_step_up"],
        "requires_manual_review": policy["requires_manual_review"],
        "ip_risk": ip_risk,
        "device_risk": device_risk,
        "time_risk": time_risk,
        "linked_accounts_count": max(shared_device_accounts, shared_ip_accounts),
        "reasons": reasons,
        "fingerprint_hash": fingerprint_hash,
        "ip_address": ip_address,
        "evaluated_at": now.isoformat(),
    }

    db.add(
        IdentityConfidenceScore(
            user_id=user_id,
            confidence_score=confidence_score,
            breakdown=summary,
        )
    )
    db.commit()

    return summary