@echo off
setlocal EnableDelayedExpansion

title Gestor de Horas - API

echo.
echo =====================================================
echo   Gestor de Horas ^| Backend API
echo =====================================================
echo.

:: Verificar que estamos en la raiz del proyecto
if not exist "src\app\main.py" (
    echo [ERROR] Ejecuta este script desde la raiz del proyecto.
    echo         La carpeta debe contener src\, tests\, .env
    pause
    exit /b 1
)

:: Verificar Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo         Descargalo en https://python.org
    pause
    exit /b 1
)

python --version
echo [OK] Python detectado

:: Verificar / activar entorno virtual
if exist ".venv\Scripts\activate.bat" (
    echo [OK] Entorno virtual encontrado en .venv\
    call .venv\Scripts\activate.bat
) else (
    echo [INFO] Entorno virtual no encontrado. Creando .venv ...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    call .venv\Scripts\activate.bat
    echo [OK] Entorno virtual creado y activado
    echo [INFO] Instalando dependencias, espera un momento...
    pip install -r requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] Fallo la instalacion de dependencias.
        pause
        exit /b 1
    )
    echo [OK] Dependencias instaladas
)

:: Verificar .env
if not exist ".env" (
    echo.
    echo [AVISO] Archivo .env no encontrado.
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [AVISO] Se copio .env.example como .env
        echo         Edita .env con tus datos antes de continuar.
        pause
    ) else (
        echo [ERROR] Tampoco existe .env.example.
        pause
        exit /b 1
    )
)

:: Menu
echo.
echo   Que queres hacer?
echo.
echo   [1] Servidor de desarrollo  (reload, puerto 8000)
echo   [2] Servidor de produccion  (4 workers, puerto 8000)
echo   [3] Tests unitarios
echo   [4] Tests de integracion
echo   [5] Todos los tests
echo   [6] Migraciones (alembic upgrade head)
echo   [7] Salir
echo.

set /p OPCION="  Opcion (1-7): "

if "%OPCION%"=="1" goto :dev
if "%OPCION%"=="2" goto :prod
if "%OPCION%"=="3" goto :test_unit
if "%OPCION%"=="4" goto :test_integration
if "%OPCION%"=="5" goto :test_all
if "%OPCION%"=="6" goto :migrate
if "%OPCION%"=="7" goto :fin

echo [ERROR] Opcion invalida.
pause
goto :fin

:dev
echo.
echo [INICIO] http://localhost:8000
echo          Swagger: http://localhost:8000/docs
echo          Ctrl+C para detener
echo.
set PYTHONPATH=src
set APP_ENV=development
uvicorn app.main:app --reload --port 8000
goto :fin

:prod
echo.
echo [INICIO] http://0.0.0.0:8000 - 4 workers
echo.
set PYTHONPATH=src
set APP_ENV=production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
goto :fin

:test_unit
echo.
set PYTHONPATH=src
set APP_ENV=testing
pytest tests/unit/ --no-cov -v
if %errorlevel% equ 0 (echo [OK] Tests unitarios OK) else (echo [FALLO] Revisa el output)
pause
goto :fin

:test_integration
echo.
set PYTHONPATH=src
set APP_ENV=testing
pytest tests/integration/ --no-cov -v
if %errorlevel% equ 0 (echo [OK] Tests integracion OK) else (echo [FALLO] Revisa el output)
pause
goto :fin

:test_all
echo.
set PYTHONPATH=src
set APP_ENV=testing
pytest tests/unit/ tests/integration/ --no-cov -v
if %errorlevel% equ 0 (echo [OK] 117/117 tests OK) else (echo [FALLO] Revisa el output)
pause
goto :fin

:migrate
echo.
set PYTHONPATH=src
alembic upgrade head
if %errorlevel% equ 0 (echo [OK] BD actualizada) else (echo [ERROR] Verifica el .env y SQL Server)
pause
goto :fin

:fin
echo.
echo Hasta luego.
endlocal