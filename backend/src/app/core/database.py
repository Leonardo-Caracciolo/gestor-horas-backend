"""
database.py — Configuración de la conexión a SQL Server.

En producción: SQL Server via pyodbc.
En tests (APP_ENV=testing): SQLite en memoria para velocidad y aislamiento.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator
from app.core.config import get_settings

settings = get_settings()


def _build_engine():
    """Construye el engine según el entorno."""
    if settings.APP_ENV == "testing":
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            echo=False,
        )
    # Producción / desarrollo: SQL Server
    url = (
        f"mssql+pyodbc://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_SERVER}:{settings.DB_PORT}/{settings.DB_NAME}"
        f"?driver={settings.DB_DRIVER.replace(' ', '+')}"
    )
    return create_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=20,
                         pool_recycle=3600, echo=settings.is_development)


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI que provee sesión de BD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
