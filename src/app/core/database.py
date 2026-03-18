"""
database.py — Configuracion de la conexion a SQL Server.

- APP_ENV=testing  → SQLite en memoria (StaticPool)
- DB_USER vacio    → Windows Authentication (Trusted_Connection)
- DB_USER presente → SQL Authentication via taxteclib
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_ODBC_DRIVERS = [
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "SQL Server",
]


def _try_drivers_trusted(server: str, database: str):
    """Conecta usando Windows Authentication (sin usuario/password)."""
    last_error = None
    for driver in _ODBC_DRIVERS:
        try:
            conn_str = (
                f"mssql+pyodbc://@{server}/{database}"
                f"?driver={driver.replace(' ', '+')}"
                f"&Trusted_Connection=yes"
            )
            engine = create_engine(conn_str, echo=False)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Conectado a SQL Server (Windows Auth) usando driver: {driver}")
            return engine
        except Exception as e:
            logger.warning(f"Driver '{driver}' fallo (Windows Auth): {e}")
            last_error = e
    raise RuntimeError(f"No se pudo conectar con Windows Authentication. Ultimo error: {last_error}")


def _try_drivers_sql(server: str, database: str, user: str, password: str):
    """Conecta usando SQL Authentication via taxteclib."""
    from taxteclib import SqlServerClient
    last_error = None
    for driver in _ODBC_DRIVERS:
        try:
            client = SqlServerClient(
                user=user,
                password=password,
                host=server,
                dbname=database,
                driver=driver,
            )
            with client.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Conectado a SQL Server (SQL Auth) usando driver: {driver}")
            return client.engine
        except Exception as e:
            logger.warning(f"Driver '{driver}' fallo: {e}")
            last_error = e
    raise RuntimeError(f"No se pudo conectar a SQL Server. Ultimo error: {last_error}")


def _build_engine():
    if settings.APP_ENV == "testing":
        from sqlalchemy.pool import StaticPool
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )

    if not settings.DB_USER:
        return _try_drivers_trusted(settings.DB_SERVER, settings.DB_NAME)

    return _try_drivers_sql(
        server=settings.DB_SERVER,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
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