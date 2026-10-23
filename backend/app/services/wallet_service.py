from app.models.wallet import Wallet
from app.models.transaction import Transaction
from datetime import datetime

def create_wallet_with_initial_credits(db, user_id: int):
    existing_wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if existing_wallet:
        return existing_wallet

    # total credits = 50
    total_credits = 50

    wallet = Wallet(
        user_id=user_id,
        available_balance=total_credits,
        locked_balance=0,
        total_earned=total_credits,
        total_spent=0,
        last_transaction_at=datetime.utcnow()
    )

    db.add(wallet)
    db.add(
        Transaction(
            user_id=user_id,
            amount=total_credits,
            type="earned",
            description="Initial onboarding credits",
        )
    )
    db.commit()
    db.refresh(wallet)

    print(f"Wallet created with {total_credits} credits for user {user_id}")

    return wallet