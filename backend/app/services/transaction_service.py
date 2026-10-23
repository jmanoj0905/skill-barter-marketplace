from app.models.transaction import Transaction
from datetime import datetime

def create_transaction(db, user_id, amount, txn_type, description, session_id=None):
    txn = Transaction(
        user_id=user_id,
        amount=amount,
        type=txn_type,
        description=description,
        created_at=datetime.utcnow()
    )

    db.add(txn)
    db.commit()
    db.refresh(txn)

    print(f"Transaction: {txn_type} {amount} for user {user_id}")

    return txn