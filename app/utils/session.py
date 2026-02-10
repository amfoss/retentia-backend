import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import IntegrityError, DatabaseError

from app.models import Session

SESSION_TTL_DAYS = 7
MAX_TRIES = 3

def create_session(db: DBSession, user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)

    for _ in range(MAX_TRIES):
        session_id = secrets.token_urlsafe(32)

        db_session = Session(
            id=session_id,
            user_id=user_id,
            expires_at=expires_at,
        )

        try:
            db.add(db_session)
            db.commit()
            return session_id

        except IntegrityError:
            db.rollback()
            continue

        except DatabaseError:
            db.rollback()
            raise

    raise RuntimeError("Failed to create session")