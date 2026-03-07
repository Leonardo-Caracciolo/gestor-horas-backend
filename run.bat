@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  Gestor de Horas — Launcher
::  Ejecuta el servidor FastAPI en entorno de desarrollo.
::  Requiere: Python 3.11+, entorno virtual en .venv\
:: ============================================================

title Gestor de Horas — API

:: ── Colores ─────────────────────────────────────────────────
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set CYAN=[96m
set RESET=[0m

echo.
echo %CYAN%=====================================================
echo   Gestor de Horas ^| Backend API
echo =====================================================%RESET%
echo.

:: ── Verificar que estamos en la raiz del proyecto ───────────
if not exist "src\app\main.py" (
    echo %RED%[ERROR] Este script debe ejecutarse desde la raiz del proyecto.%RESET%
    echo        Ubicacion esperada: la carpeta que contiene src\, tests\, .env
    pause
    exit /b 1
)

:: ── Verificar Python ─────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%[ERROR] Python no esta instalado o no esta en el PATH.%RESET%
    echo        Descargalo en https://python.org
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo %GREEN%[OK]%RESET%    Python %PYVER% detectado

:: ── Verificar / activar entorno virtual ─────────────────────
if exist ".venv\Scripts\activate.bat" (
    echo %GREEN%[OK]%RESET%    Entorno virtual encontrado en .venv\
    call .venv\Scripts\activate.bat
) else (
    echo %YELLOW%[INFO]%RESET%  Entorno virtual no encontrado. Creando .venv ...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo %RED%[ERROR] No se pudo crear el entorno virtual.%RESET%
        pause
        exit /b 1
    )
    call .venv\Scripts\activate.bat
    echo %GREEN%[OK]%RESET%    Entorno virtual creado y activado

    echo %YELLOW%[INFO]%RESET%  Instalando dependencias (puede tardar unos minutos)...
    pip install -r requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo %RED%[ERROR] Fallo la instalacion de dependencias.%RESET%
        echo        Revisa requirements.txt y tu conexion a internet.
        pause
        exit /b 1
    )
    echo %GREEN%[OK]%RESET%    Dependencias instaladas
)

:: ── Verificar .env ───────────────────────────────────────────
if not exist ".env" (
    echo %YELLOW%[AVISO]%RESET% Archivo .env no encontrado.
    echo        Copiando .env.example como .env ...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo %YELLOW%[AVISO]%RESET% Edita .env con tus datos antes de continuar.
        echo.
        echo        Variables obligatorias:
        echo          DB_SERVER    ^= tu-servidor\INSTANCIA
        echo          DB_DATABASE  ^= nombre_base_de_datos
        echo          DB_USER      ^= usuario_bd
        echo          DB_PASSWORD  ^= password_bd
        echo          SECRET_KEY   ^= clave-jwt-min-32-caracteres
        echo.
        pause
    ) else (
        echo %RED%[ERROR] Tampoco existe .env.example. Revisa la instalacion.%RESET%
        pause
        exit /b 1
    )
)

:: ── Verificar uvicorn ────────────────────────────────────────
python -c "import uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%[INFO]%RESET%  Instalando dependencias faltantes...
    pip install -r requirements.txt --quiet
)

:: ── Menú de opciones ─────────────────────────────────────────
echo.
echo %CYAN%  ¿Que queres hacer?%RESET%
echo.
echo    [1] Iniciar servidor de desarrollo  (--reload, puerto 8000)
echo    [2] Iniciar servidor de produccion  (4 workers, puerto 8000)
echo    [3] Ejecutar tests unitarios
echo    [4] Ejecutar tests de integracion
echo    [5] Ejecutar TODOS los tests
echo    [6] Crear tablas en la BD (alembic upgrade head)
echo    [7] Salir
echo.

set /p OPCION="  Opcion (1-7): "

if "%OPCION%"=="1" goto :dev
if "%OPCION%"=="2" goto :prod
if "%OPCION%"=="3" goto :test_unit
if "%OPCION%"=="4" goto :test_integration
if "%OPCION%"=="5" goto :test_all
if "%OPCION%"=="6" goto :migrate
if "%OPCION%"=="7" goto :fin

echo %RED%[ERROR] Opcion invalida.%RESET%
pause
goto :fin

:: ── Servidor desarrollo ──────────────────────────────────────
:dev
echo.
echo %GREEN%[INICIO]%RESET% Servidor de desarrollo en http://localhost:8000
echo         Swagger UI: http://localhost:8000/docs
echo         Health:     http://localhost:8000/health
echo         Ctrl+C para detener
echo.
set PYTHONPATH=src
set APP_ENV=development
uvicorn app.main:app --reload --port 8000
goto :fin

:: ── Servidor produccion ──────────────────────────────────────
:prod
echo.
echo %GREEN%[INICIO]%RESET% Servidor de produccion en http://0.0.0.0:8000 (4 workers)
echo         Ctrl+C para detener
echo.
set PYTHONPATH=src
set APP_ENV=production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
goto :fin

:: ── Tests unitarios ──────────────────────────────────────────
:test_unit
echo.
echo %CYAN%[TEST]%RESET%   Ejecutando tests unitarios...
echo.
set PYTHONPATH=src
set APP_ENV=testing
pytest tests/unit/ --no-cov -v
echo.
if %errorlevel% equ 0 (
    echo %GREEN%[OK]%RESET%    Todos los tests unitarios pasaron.
) else (
    echo %RED%[FALLO]%RESET% Algunos tests fallaron. Revisa el output arriba.
)
pause
goto :fin

:: ── Tests integracion ─────────────────────────────────────────
:test_integration
echo.
echo %CYAN%[TEST]%RESET%   Ejecutando tests de integracion...
echo.
set PYTHONPATH=src
set APP_ENV=testing
pytest tests/integration/ --no-cov -v
echo.
if %errorlevel% equ 0 (
    echo %GREEN%[OK]%RESET%    Todos los tests de integracion pasaron.
) else (
    echo %RED%[FALLO]%RESET% Algunos tests fallaron. Revisa el output arriba.
)
pause
goto :fin

:: ── Todos los tests ───────────────────────────────────────────
:test_all
echo.
echo %CYAN%[TEST]%RESET%   Ejecutando suite completa de tests...
echo.
set PYTHONPATH=src
set APP_ENV=testing
pytest tests/unit/ tests/integration/ --no-cov -v
echo.
if %errorlevel% equ 0 (
    echo %GREEN%[OK]%RESET%    117/117 tests pasaron.
) else (
    echo %RED%[FALLO]%RESET% Algunos tests fallaron. Revisa el output arriba.
)
pause
goto :fin

:: ── Migraciones ───────────────────────────────────────────────
:migrate
echo.
echo %CYAN%[DB]%RESET%     Aplicando migraciones con Alembic...
echo.
set PYTHONPATH=src
alembic upgrade head
if %errorlevel% equ 0 (
    echo %GREEN%[OK]%RESET%    Base de datos actualizada correctamente.
) else (
    echo %RED%[ERROR]%RESET% Fallo la migracion. Verifica la conexion a SQL Server y el .env.
)
pause
goto :fin

:fin
echo.
echo %CYAN%Hasta luego.%RESET%
endlocal