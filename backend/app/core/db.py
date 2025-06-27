from sqlmodel import Session, create_engine, select, SQLModel
from contextlib import asynccontextmanager
from typing import Generator

from app import crud
from app.core.config import settings
from app.models import User, UserCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # For SQLite development, create tables directly
    if settings.USE_SQLITE:
        SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            full_name="System Administrator"
        )
        user = crud.create_user(session=session, user_create=user_in)


def get_session() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def get_session_context():
    """Async context manager for database sessions in background tasks"""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
