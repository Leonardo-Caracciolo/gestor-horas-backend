"""
config.py — Configuración centralizada de la aplicación.

Usa pydantic-settings para leer variables de entorno desde .env
o variables del sistema operativo.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Configuración global de la aplicación.

    Todos los valores se leen desde variables de entorno o archivo .env.
    Los valores con default son opcionales.

    Raises:
        ValidationError: Si una variable requerida no está definida.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_NAME: str = "Gestor de Horas"
    APP_VERSION: str = "1.0.0"
    CORS_ORIGINS: str = "http://localhost:5173"

    # ── Database ───────────────────────────────────────────
    DB_SERVER: str
    DB_PORT: int = 1433
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"

    # ── Auth ───────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # ── Azure DevOps ───────────────────────────────────────
    ADO_ORGANIZATION_URL: str = ""
    ADO_PROJECT: str = ""
    ADO_PAT: str = ""

    # ── Teams ──────────────────────────────────────────────
    TEAMS_WEBHOOK_URL: str = ""

    @property
    def DATABASE_URL(self) -> str:
        """Construye la cadena de conexión para SQL Server via pyodbc."""
        return (
            f"mssql+pyodbc://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"
            f"?driver={self.DB_DRIVER.replace(' ', '+')}"
        )

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        """Retorna los orígenes CORS como lista."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna la instancia singleton de Settings.

    El decorador lru_cache garantiza que solo se instancia una vez
    durante el ciclo de vida de la aplicación.

    Returns:
        Settings: Instancia de configuración.
    """
    return Settings()
