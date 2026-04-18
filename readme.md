# Gestor de Horas

> Sistema interno para que el equipo de Tecnología registre, apruebe y exporte sus horas de trabajo, integrado con Azure DevOps.

Reemplaza el Excel compartido tradicional por una app web con backend en FastAPI y frontend en React.

---

## Tabla de contenidos

1. [Stack](#stack)
2. [Arranque rápido (TL;DR)](#arranque-rápido-tldr)
3. [Instalación detallada](#instalación-detallada)
   - [Requisitos previos](#requisitos-previos)
   - [Backend](#backend)
   - [Frontend](#frontend)
4. [Cómo correr la app día a día](#cómo-correr-la-app-día-a-día)
5. [Variables de entorno](#variables-de-entorno)
6. [Scripts de utilidad](#scripts-de-utilidad)
   - [`limpiar_horas.py` — borrar registros](#limpiar_horaspy--borrar-registros)
   - [`seed.py` y `seed_proyectos.py` — cargar datos iniciales](#seedpy-y-seed_proyectospy--cargar-datos-iniciales)
   - [`reset_pass.py` — resetear contraseña](#reset_passpy--resetear-contraseña)
7. [Estructura del proyecto](#estructura-del-proyecto)
8. [Flujo de trabajo en la app](#flujo-de-trabajo-en-la-app)
9. [Tests](#tests)
10. [Solución de problemas comunes](#solución-de-problemas-comunes)
11. [Roadmap](#roadmap)

---

## Stack

| Capa | Tecnología |
|---|---|
| **Backend** | FastAPI, SQLAlchemy 2, Pydantic v2, Alembic |
| **Auth** | JWT (python-jose) + bcrypt |
| **Base de datos** | SQL Server (Windows Auth en local; SQL Auth en QA/Prod) |
| **Frontend** | React 19, Vite 8, TailwindCSS v4, React Router, Axios |
| **Integración** | Azure DevOps SDK, Microsoft Teams Webhooks, openpyxl |
| **Tests** | pytest, pytest-cov, Faker |

---

## Arranque rápido (TL;DR)

Si ya hiciste todo esto antes y solo querés ver el comando completo:

```bash
# Backend (terminal 1)
cd gestor-horas-backend
.venv\Scripts\activate
set PYTHONPATH=src
set APP_ENV=development
uvicorn app.main:app --reload --reload-dir src

# Frontend (terminal 2)
cd gestor-horas-backend\frontend
npm run dev
```

Abrí http://localhost:5173 y logueate con el usuario admin del seed.

Si es la primera vez, seguí la sección de abajo.

---

## Instalación detallada

### Requisitos previos

| Herramienta | Versión | Verificación |
|---|---|---|
| **Python** | 3.11+ | `python --version` |
| **Node.js** | 20+ | `node --version` |
| **Git** | cualquiera | `git --version` |
| **SQL Server** | 2019+ Express o superior | desde SSMS |
| **ODBC Driver 17 for SQL Server** | — | [descargar de Microsoft](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) |

> **Si trabajás en una máquina Windows corporativa**, probablemente ya tengas todo menos Node. Verificá con los comandos de la columna derecha.

### Backend

```bash
# 1. Clonar el repo
git clone https://github.com/Leonardo-Caracciolo/gestor-horas-backend.git
cd gestor-horas-backend

# 2. Crear entorno virtual (una sola vez)
python -m venv .venv

# 3. Activar el venv (CADA VEZ que abras una terminal nueva)
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Copiar el archivo de configuración y editarlo
copy .env.example .env       # Windows
cp .env.example .env         # Linux/Mac
# → Abrir .env con un editor y completar los valores (ver más abajo)

# 6. Aplicar las migraciones (crea las tablas en la BD)
set PYTHONPATH=src           # Windows
export PYTHONPATH=src        # Linux/Mac
alembic upgrade head

# 7. Cargar datos iniciales (admin + proyectos OFICINA y BPS)
python seed.py
python seed_proyectos.py
```

Si todo salió bien, deberías poder levantar el backend con:

```bash
set APP_ENV=development
uvicorn app.main:app --reload --reload-dir src
```

Y entrar a http://localhost:8000/docs para ver la API.

### Frontend

```bash
# Desde la raíz del repo
cd frontend

# Instalar dependencias (una sola vez)
npm install --legacy-peer-deps

# Levantar el dev server
npm run dev
```

> El flag `--legacy-peer-deps` es necesario por un conflicto entre Vite 8 y TailwindCSS v4 al momento de escribir esto. Sin él, `npm install` falla.

Abrí http://localhost:5173 y logueate con las credenciales del admin (las definís vos en `seed.py` la primera vez que lo corrés).

---

## Cómo correr la app día a día

Necesitás **dos terminales abiertas**, una para el backend y otra para el frontend:

**Terminal 1 — Backend:**
```bash
cd gestor-horas-backend
.venv\Scripts\activate
set PYTHONPATH=src
set APP_ENV=development
uvicorn app.main:app --reload --reload-dir src
```

**Terminal 2 — Frontend:**
```bash
cd gestor-horas-backend\frontend
npm run dev
```

| URL | Para qué |
|---|---|
| http://localhost:5173 | App (lo que usás) |
| http://localhost:8000/docs | Swagger — probar endpoints sueltos |
| http://localhost:8000/health | Health check |

Para parar cualquiera de los dos: `Ctrl+C` en su terminal.

---

## Variables de entorno

Todas se leen de un archivo `.env` en la raíz. Hay un `.env.example` con los nombres y formato — copialo y completalo.

### Obligatorias

| Variable | Ejemplo | Notas |
|---|---|---|
| `APP_ENV` | `development` | `development`, `production` o `testing` |
| `DB_SERVER` | `LAPTOP\SQLEXPRESS01` | Nombre o IP del servidor SQL |
| `DB_DATABASE` | `Tecnologia` | Nombre de la BD |
| `DB_USER` | `sa` | Solo si usás SQL Auth. Si es Windows Auth, dejá vacío |
| `DB_PASSWORD` | `MiPass123` | Solo si usás SQL Auth |
| `SECRET_KEY` | `abc123...` (32+ chars) | JWT — generá con el comando de abajo |

```bash
# Generar una SECRET_KEY segura
python -c "import secrets; print(secrets.token_hex(32))"
```

### Opcionales

| Variable | Default | Notas |
|---|---|---|
| `DB_PORT` | `1433` | Puerto SQL Server |
| `CORS_ORIGINS` | `http://localhost:5173` | Separar con coma si hay varios |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Duración del JWT (8h por defecto) |
| `ADO_ORGANIZATION_URL` | — | Ej: `https://dev.azure.com/AR-Deloitte-BPS-Tax-Tech` |
| `ADO_PROJECT` | — | Nombre del proyecto en ADO |
| `ADO_PAT` | — | Personal Access Token, **solo lectura de Work Items** |
| `TEAMS_WEBHOOK_URL` | — | Webhook del canal de Teams para notificaciones |

> **Importante:** `APP_ENV=development` debe estar seteado para que CORS deje pasar al frontend desde `localhost:5173`. Si te aparecen errores de CORS en consola, este es el primer lugar a revisar.

---

## Scripts de utilidad

Todos se corren desde la raíz del repo, con el venv activado y `PYTHONPATH=src`.

### `limpiar_horas.py` — borrar registros

Borra registros de la tabla `registros_horas` y sus aprobaciones asociadas. Pensado para limpiar datos de prueba durante el desarrollo.

**No usar en producción sin saber lo que hacés.** Borra de verdad.

#### Uso

```bash
# Activar venv y configurar PYTHONPATH primero
.venv\Scripts\activate
set PYTHONPATH=src

# Ver cuánto se borraría sin borrar nada
python limpiar_horas.py --dry-run

# Borrar TODOS los registros de TODOS los usuarios (pide confirmación)
python limpiar_horas.py

# Borrar solo los registros de un usuario específico
python limpiar_horas.py --usuario 1

# Sin pedir confirmación (cuidado)
python limpiar_horas.py --yes
```

#### Qué hace

1. Cuenta cuántos registros y cuántas aprobaciones se borrarían.
2. Pide que escribas literalmente `borrar` para confirmar (a menos que pases `--yes`).
3. Borra primero las aprobaciones (por la FK), después los registros.
4. Hace commit de la transacción.

Los IDs de la tabla **no se reinician**. Si querés que `id` vuelva a empezar en 1 después del borrado, corré desde SSMS:

```sql
DBCC CHECKIDENT ('registros_horas', RESEED, 0);
DBCC CHECKIDENT ('aprobaciones', RESEED, 0);
```

### `seed.py` y `seed_proyectos.py` — cargar datos iniciales

Solo la primera vez que armás la BD desde cero (o después de un `alembic downgrade base`).

```bash
python seed.py            # crea roles, permisos, usuario admin
python seed_proyectos.py  # crea proyectos OFICINA (id=1) y BPS (id=2)
```

### `reset_pass.py` — resetear contraseña

Si te olvidaste tu contraseña en local:

```bash
python reset_pass.py
```

Te pide username y password nuevo. Solo funciona desde la máquina con acceso a la BD (no es un endpoint).

---

## Estructura del proyecto

```
gestor-horas-backend/
├── alembic/                    # Migraciones de BD
│   └── versions/
├── src/app/                    # Código del backend
│   ├── api/v1/                 # Routers de FastAPI
│   ├── core/                   # config, database, security
│   ├── models/                 # Modelos SQLAlchemy
│   ├── schemas/                # Pydantic
│   └── services/               # Lógica de negocio (hora_service, ado_service, ...)
├── frontend/                   # App React + Vite
│   ├── src/
│   │   ├── api/                # Wrappers axios
│   │   ├── components/         # FormularioHora, ...
│   │   ├── context/            # AuthContext
│   │   └── pages/              # MisHoras, HistorialHoras, Usuarios, Login, ...
│   └── package.json
├── tests/                      # pytest
├── seed.py                     # Carga de admin + permisos
├── seed_proyectos.py           # Carga de proyectos OFICINA y BPS
├── reset_pass.py               # Reset de contraseña local
├── limpiar_horas.py            # Borrado de registros de horas
├── requirements.txt
├── alembic.ini
└── .env.example
```

---

## Flujo de trabajo en la app

1. **Login**: usuario y contraseña, devuelve JWT.
2. **Mis Horas** (vista semanal): el usuario ve la semana actual día por día y puede cargar nuevas horas con el botón "+ Cargar horas".
3. **Cargar hora**: elige tipo (PROYECTO/OFICINA) → si es PROYECTO, selecciona Epic → Feature → Task/User Story (cascada de datos sincronizados de ADO) → completa fecha, descripción y horas. Las horas se auto-aprueban (no hay flujo de aprobación activo en v1).
4. **Historial**: vista tabla con filtros por fecha y estado, ordenamiento por columnas, total al pie.
5. **Usuarios** (solo admins): ABM de usuarios del equipo.

### Validaciones del backend (no son bugs, son reglas)

- No se pueden cargar horas en sábado o domingo (devuelve 400).
- No se pueden cargar horas en feriados (los gestiona la tabla `feriados`).
- Máximo 12 horas por día por usuario.
- Las semanas pueden cerrarse — una vez cerradas, no se pueden cargar más horas en ese rango.
- Solo se pueden editar/borrar registros en estado `Borrador`.

---

## Tests

```bash
# Activar venv + PYTHONPATH primero
set PYTHONPATH=src
set APP_ENV=testing

# Correr todo
pytest

# Con cobertura
pytest --cov=app --cov-report=html
# El reporte HTML queda en htmlcov/index.html
```

Los tests usan SQLite en memoria, no tocan tu SQL Server local.

---

## Solución de problemas comunes

### "Cannot connect to SQL Server"

- Confirmá que el servicio de SQL Server esté corriendo (Services → "SQL Server (SQLEXPRESS01)").
- Si usás Windows Auth, no pongas `DB_USER` ni `DB_PASSWORD` en `.env`.
- El nombre del server lleva backslash escapado en el `.env`: `LAPTOP\\SQLEXPRESS01` o entre comillas: `"LAPTOP\SQLEXPRESS01"`.

### Errores de CORS en la consola del navegador

- Asegurate de tener `APP_ENV=development` seteado **antes** de levantar uvicorn.
- Si cambiaste el puerto del frontend, agregalo a `CORS_ORIGINS`.

### "Objects are not valid as a React child" + pantalla en blanco

Significa que algún componente está renderizando un objeto donde se espera un string. Pasó con `u.rol` (que es `{id, nombre}`, no un string) y con `detail` de errores Pydantic. Si te aparece de nuevo, revisá el último cambio que hiciste al JSX y buscá un `{algoQueEsObjeto}`.

### El frontend no se actualiza después de cambiar código

- `Ctrl+Shift+R` en el navegador para forzar recarga sin caché.
- Si seguís viendo lo viejo, parar `npm run dev` y volver a levantarlo.

### Uvicorn tira `WatchFiles permission error` en Windows

Levantalo siempre con `--reload-dir src` para que solo vigile el código fuente y no la BD ni `.venv`.

### Caracteres raros (`├`, `─`, `→`) rompen un `.bat`

`cmd.exe` no maneja Unicode por default. En `.bat` usá solo ASCII.

---

## Roadmap

| Versión | Estado | Funcionalidad |
|---|---|---|
| **v1.0** | ✅ Liberada | Backend completo, frontend con Mis Horas / Historial / Usuarios, sync ADO, export Excel semanal |
| **v2.0** | 🔲 Planeada | Login con Microsoft Teams (Entra ID), gestión de roles desde la UI, migración a BD compartida `Tecnologia_QA`, vista admin de horas del equipo, export Excel filtrado |
| **v3.0** | 🔲 Idea | Embed de dashboards Power BI, notificaciones automáticas en Teams |

---

## Contacto

Mantenedor: **Leonardo Caracciolo**
Repo: https://github.com/Leonardo-Caracciolo/gestor-horas-backend