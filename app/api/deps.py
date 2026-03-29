from sqlalchemy.orm import Session

from app.infra.db.session import get_db


def get_session() -> Session:
    yield from get_db()
