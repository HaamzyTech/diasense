from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    # TODO: Prefer Alembic migrations in production.
    Base.metadata.create_all(bind=engine)
