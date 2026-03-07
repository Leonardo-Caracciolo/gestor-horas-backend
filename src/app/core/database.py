"""
database.py — Configuración de la conexión a SQL Server.

En producción/desarrollo: SQL Server via taxteclib.SqlServerClient,
probando múltiples drivers ODBC hasta encontrar uno disponible.
En tests (APP_ENV=testing): SQLite en memoria para velocidad y aislamiento.
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator
from taxteclib import SqlServerClient
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Drivers a intentar en orden de preferencia
_ODBC_DRIVERS = [
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "SQL Server",
]


def _try_drivers(server: str, database: str, user: str, password: str):
    """
    Intenta conectarse a SQL Server probando múltiples drivers ODBC.

    Itera sobre _ODBC_DRIVERS y devuelve el primer SqlServerClient
    que logre establecer conexión.

    Args:
        server:   Nombre o IP del servidor SQL Server.
        database: Nombre de la base de datos.
        user:     Usuario de la base de datos.
        password: Contraseña del usuario.

    Returns:
        SqlServerClient: Cliente conectado con el primer driver disponible.

    Raises:
        RuntimeError: Si ningún driver logra conectarse.
    """
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
            # Verificar que la conexión es real antes de aceptarla
            with client.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"✅ Conectado a SQL Server usando driver: {driver}")
            return client
        except Exception as e:
            logger.warning(f"Driver '{driver}' falló: {e}")
            last_error = e

    raise RuntimeError(
        f"No se pudo conectar a SQL Server con ningún driver disponible. "
        f"Último error: {last_error}"
    )


def _build_engine():
    """Construye el engine según el entorno."""
    if settings.APP_ENV == "testing":
        from sqlalchemy.pool import StaticPool
        # StaticPool: todas las sesiones comparten UNA sola conexión,
        # esencial para que SQLite in-memory sea visible entre threads.
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    # Producción / desarrollo: SQL Server via taxteclib con retry de drivers
    client = _try_drivers(
        server=settings.DB_SERVER,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )
    return client.engine


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
