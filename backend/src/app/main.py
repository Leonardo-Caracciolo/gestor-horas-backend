"""
main.py — Punto de entrada de la aplicación FastAPI.

Configura la app, middlewares, routers y eventos de startup/shutdown.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.database import check_connection

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.

    Startup:
        - Verifica conexión a SQL Server.
        - Log de inicio de la aplicación.

    Shutdown:
        - Cierre limpio de conexiones.
    """
    # ── Startup ────────────────────────────────────────────────
    print(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    if check_connection():
        print("✅ Conexión a SQL Server establecida")
    else:
        print("❌ ERROR: No se pudo conectar a SQL Server")

    yield

    # ── Shutdown ───────────────────────────────────────────────
    print(f"⛔ Cerrando {settings.APP_NAME}")


# ── App instance ───────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API del Gestor de Horas del equipo de Tecnología.",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
# Se importan aquí para evitar imports circulares
from app.api.v1.routers import auth, usuarios, proyectos, horas, sprints, feriados, export  # noqa: E402

app.include_router(auth.router,      prefix="/api/v1/auth",      tags=["Auth"])
app.include_router(usuarios.router,  prefix="/api/v1/usuarios",  tags=["Usuarios"])
app.include_router(proyectos.router, prefix="/api/v1/proyectos", tags=["Proyectos"])
app.include_router(horas.router,     prefix="/api/v1/horas",     tags=["Horas"])
app.include_router(sprints.router,   prefix="/api/v1/sprints",   tags=["Sprints"])
app.include_router(feriados.router,  prefix="/api/v1/feriados",  tags=["Feriados"])
app.include_router(export.router,    prefix="/api/v1/export",    tags=["Export"])


# ── Health check ───────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    """
    Endpoint de verificación de estado de la API.

    Returns:
        dict: Estado de la API y la conexión a BD.
    """
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "db": "connected" if check_connection() else "error",
    }
