# Gestor de Horas — Backend API

> Sistema interno de registro y gestión de horas del equipo de Tecnología.  
> Reemplaza el proceso manual en Excel por un flujo automatizado con integración a Azure DevOps, exportación Excel y notificaciones a Microsoft Teams.

---

## Tabla de contenidos

1. [Descripción general](#descripción-general)
2. [Stack tecnológico](#stack-tecnológico)
3. [Arquitectura](#arquitectura)
4. [Estructura del proyecto](#estructura-del-proyecto)
5. [Modelos de datos](#modelos-de-datos)
6. [API Reference](#api-reference)
7. [Sistema de permisos (RBAC)](#sistema-de-permisos-rbac)
8. [Instalación y configuración](#instalación-y-configuración)
9. [Variables de entorno](#variables-de-entorno)
10. [Ejecución](#ejecución)
11. [Tests](#tests)
12. [Integración con Azure DevOps](#integración-con-azure-devops)
13. [Export Excel](#export-excel)
14. [Notificaciones Teams](#notificaciones-teams)
15. [Flujo de aprobación de horas](#flujo-de-aprobación-de-horas)
16. [Roadmap](#roadmap)

---

## Descripción general

El Gestor de Horas es una API REST construida con **FastAPI** que centraliza el registro de horas del equipo de tecnología. Cada profesional carga sus horas diarias contra proyectos y tareas de Azure DevOps; los Tech Leads las aprueban o rechazan; y al cierre de cada semana se genera automáticamente el Excel oficial que antes se completaba a mano.

### Problemas que resuelve

| Antes | Ahora |
|---|---|
| Excel compartido propenso a errores | API REST con validaciones automáticas |
| Horas cargadas sin vinculación a tareas ADO | Sincronización automática Epic→Feature→US→Task |
| Proceso de aprobación por email/Teams manual | Flujo Borrador→Enviado→Aprobado/Rechazado |
| Excel generado manualmente cada semana | Generación automática con un solo endpoint |
| Sin auditoría ni trazabilidad | Audit log completo de todas las acciones |

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| **API** | FastAPI 0.111 + Uvicorn |
| **ORM** | SQLAlchemy 2.0 (async-ready) |
| **Base de datos** | SQL Server (producción) / SQLite (tests) |
| **Validación** | Pydantic v2 |
| **Autenticación** | JWT (python-jose) + bcrypt |
| **Migraciones** | Alembic |
| **Azure DevOps** | azure-devops SDK (PAT readonly) |
| **Excel** | openpyxl |
| **Notificaciones** | Microsoft Teams Webhook (Adaptive Cards) |
| **HTTP client** | httpx |
| **Testing** | pytest + pytest-cov + Faker + Robot Framework |
| **DB interna** | taxteclib (cliente SQL Server corporativo) |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI App                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Routers    │  │    Deps      │  │    Middleware     │  │
│  │  /api/v1/    │  │  JWT + RBAC  │  │  CORS / Logging  │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────┘  │
│         │                                                   │
│  ┌──────▼───────────────────────────────────────────────┐   │
│  │                    Services                          │   │
│  │  hora_service │ ado_service │ export_service         │   │
│  └──────┬───────────────────────────────────────────────┘   │
│         │                                                   │
│  ┌──────▼───────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │    Models    │  │   Schemas    │  │      Core        │  │
│  │  SQLAlchemy  │  │   Pydantic   │  │ config/security  │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────┘  │
└─────────┼───────────────────────────────────────────────────┘
          │
    ┌─────▼──────┐     ┌──────────────┐     ┌─────────────┐
    │ SQL Server │     │ Azure DevOps │     │    Teams    │
    │ (taxteclib)│     │   REST API   │     │  Webhook    │
    └────────────┘     └──────────────┘     └─────────────┘
```

### Decisiones de diseño

- **`src/` layout**: el código fuente vive en `src/app/` para evitar imports accidentales desde la raíz y poder instalar el paquete limpiamente.
- **`StaticPool` en tests**: SQLite en memoria con `StaticPool` garantiza que todas las sesiones de la misma ejecución de pytest compartan la misma base de datos.
- **RBAC dinámico**: los permisos no están hardcodeados en el código sino almacenados en la tabla `permisos` y asignados a roles. Agregar un nuevo permiso es solo un INSERT.
- **Soft delete**: los usuarios y proyectos se desactivan (`activo=False`) en lugar de eliminarse, preservando la integridad referencial del historial de horas.

---

## Estructura del proyecto

```
gestor-horas-final/
│
├── src/
│   └── app/
│       ├── main.py                  # Entrada: app FastAPI, routers, lifespan
│       ├── api/
│       │   └── v1/
│       │       ├── deps.py          # Dependencias: get_current_user, require_permiso
│       │       └── routers/
│       │           ├── auth.py          # POST /login, GET /me
│       │           ├── usuarios.py      # CRUD usuarios + cambiar password
│       │           ├── proyectos.py     # CRUD proyectos + sync ADO + items
│       │           ├── sprints.py       # CRUD sprints + activar/cerrar
│       │           ├── ceremonias.py    # CRUD ceremonias Scrum por sprint
│       │           ├── horas.py         # CRUD horas + timer + enviar + aprobar
│       │           ├── feriados.py      # CRUD feriados
│       │           └── export.py        # Semanas + descarga Excel + Teams test
│       ├── core/
│       │   ├── config.py            # Settings via pydantic-settings + .env
│       │   ├── database.py          # Engine SQLAlchemy + get_db + StaticPool test
│       │   └── security.py          # JWT encode/decode, hash/verify password
│       ├── models/                  # Modelos SQLAlchemy (15 tablas)
│       │   ├── usuario.py
│       │   ├── rol.py
│       │   ├── permiso.py           # Permiso + RolPermiso (M:M)
│       │   ├── proyecto.py
│       │   ├── sprint.py
│       │   ├── ado_item.py          # Epic/Feature/UserStory/Task (autorreferencial)
│       │   ├── registro_hora.py     # Tabla central del sistema
│       │   ├── hora_planificada.py  # Planificado vs ejecutado por sprint
│       │   ├── ceremonia_scrum.py
│       │   ├── feriado.py
│       │   ├── semana.py
│       │   └── aprobacion.py        # Aprobacion + TareaFavorita + AuditLog
│       ├── schemas/                 # Schemas Pydantic (request/response)
│       │   ├── auth.py, usuario.py, proyecto.py, sprint.py
│       │   ├── ado_item.py, hora.py, feriado.py, semana.py, ceremonia.py
│       └── services/
│           ├── ado_service.py       # Sync Epic→Feature→US→Task desde ADO
│           ├── hora_service.py      # Validaciones + timer + flujo aprobación
│           └── export_service.py    # Generación Excel + cierre semana + Teams
│
├── tests/
│   ├── conftest.py                  # Fixtures unitarios (engine_test, db, mocks)
│   ├── unit/
│   │   └── models/
│   │       ├── test_usuario.py      # 16 tests
│   │       ├── test_security.py     # 9 tests
│   │       └── test_registro_hora.py # 12 tests
│   └── integration/
│       ├── conftest.py              # Engine SQLite StaticPool + seed + fixtures session
│       ├── test_auth.py             # 11 tests
│       ├── test_usuarios.py         # 18 tests
│       ├── test_horas.py            # 14 tests
│       ├── test_proyectos.py        # 13 tests
│       ├── test_sprints.py          # 9 tests
│       ├── test_feriados.py         # 6 tests
│       └── test_export.py           # 9 tests
│
├── alembic/                         # Migraciones de base de datos
├── .env.example                     # Plantilla de variables de entorno
├── pytest.ini                       # Configuración pytest + markers + coverage
├── requirements.txt                 # Dependencias del proyecto
└── README.md
```

---

## Modelos de datos

### Diagrama de relaciones

```
Rol ──< RolPermiso >── Permiso
 │
 └──< Usuario
          │
          ├──< RegistroHora >── Proyecto ──< Sprint ──< CeremoniaSprint
          │         │                │
          │         └── AdoItem ◄────┘ (autorreferencial: Epic→Feature→US→Task)
          │
          ├──< Aprobacion (1:1 con RegistroHora)
          ├──< TareaFavorita >── AdoItem
          └──< AuditLog

Semana ──► Sprint (opcional)
```

### Tablas principales

| Tabla | Descripción |
|---|---|
| `usuarios` | Profesionales del equipo. `activo`, `primer_login`, `password_hash` |
| `roles` | Admin, TechLead, Profesional, etc. Configurables |
| `permisos` | Claves de permiso (ej: `ver_horas_equipo`). RBAC dinámico |
| `proyectos` | Centro de costos. `tipo`: Proyecto u Oficina. `id_proyecto_excel` |
| `sprints` | Iteraciones de 2 semanas. Estados: Planificado→Activo→Cerrado |
| `ado_items` | Work Items de ADO. Jerarquía autorreferencial por `parent_id` |
| `registros_horas` | **Tabla central**. Una fila = un profesional, un día, N horas |
| `semanas` | Semanas laborales. Cierre bloquea nuevas imputaciones |
| `aprobaciones` | Decisión del Tech Lead sobre cada registro |
| `audit_log` | Trazabilidad completa de todas las acciones |

---

## API Reference

### Auth

| Método | Endpoint | Descripción | Permiso |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Login con usuario/password → JWT | — |
| `GET` | `/api/v1/auth/me` | Datos del usuario autenticado | Autenticado |

### Usuarios

| Método | Endpoint | Descripción | Permiso |
|---|---|---|---|
| `GET` | `/api/v1/usuarios/` | Listar usuarios | `admin_usuarios` |
| `POST` | `/api/v1/usuarios/` | Crear usuario | `admin_usuarios` |
| `GET` | `/api/v1/usuarios/{id}` | Obtener por ID | `admin_usuarios` |
| `PUT` | `/api/v1/usuarios/{id}` | Actualizar | `admin_usuarios` |
| `DELETE` | `/api/v1/usuarios/{id}` | Desactivar (soft delete) | `admin_usuarios` |
| `POST` | `/api/v1/usuarios/me/password` | Cambiar propia contraseña | Autenticado |

### Proyectos

| Método | Endpoint | Descripción | Permiso |
|---|---|---|---|
| `GET` | `/api/v1/proyectos/` | Listar proyectos | Autenticado |
| `POST` | `/api/v1/proyectos/` | Crear proyecto | `admin_proyectos` |
| `GET` | `/api/v1/proyectos/{id}` | Obtener por ID | Autenticado |
| `PUT` | `/api/v1/proyectos/{id}` | Actualizar | `admin_proyectos` |
| `DELETE` | `/api/v1/proyectos/{id}` | Desactivar | `admin_proyectos` |
| `POST` | `/api/v1/proyectos/{id}/sync-ado` | Sincronizar con ADO | `admin_proyectos` |
| `GET` | `/api/v1/proyectos/{id}/items` | Work Items del proyecto | Autenticado |
| `GET` | `/api/v1/proyectos/{id}/items/arbol` | Jerarquía anidada (Epics→Tasks) | Autenticado |

### Sprints

| Método | Endpoint | Descripción | Permiso |
|---|---|---|---|
| `GET` | `/api/v1/sprints/` | Listar sprints | Autenticado |
| `POST` | `/api/v1/sprints/` | Crear sprint | `admin_proyectos` |
| `GET` | `/api/v1/sprints/{id}` | Obtener por ID | Autenticado |
| `PUT` | `/api/v1/sprints/{id}` | Actualizar | `admin_proyectos` |
| `POST` | `/api/v1/sprints/{id}/activar` | Planificado → Activo | `admin_proyectos` |
| `POST` | `/api/v1/sprints/{id}/cerrar` | Activo → Cerrado | `cerrar_sprint` |
| `GET` | `/api/v1/sprints/{id}/ceremonias/` | Listar ceremonias | Autenticado |
| `POST` | `/api/v1/sprints/{id}/ceremonias/` | Registrar ceremonia | Autenticado |
| `PUT` | `/api/v1/sprints/{id}/ceremonias/{cid}` | Actualizar ceremonia | Autenticado |
| `DELETE` | `/api/v1/sprints/{id}/ceremonias/{cid}` | Eliminar ceremonia | Autenticado |

### Horas

| Método | Endpoint | Descripción | Permiso |
|---|---|---|---|
| `GET` | `/api/v1/horas/` | Mis registros (con filtros) | Autenticado |
| `POST` | `/api/v1/horas/` | Crear registro | Autenticado |
| `GET` | `/api/v1/horas/semana` | Resumen semana actual (5 días) | Autenticado |
| `GET` | `/api/v1/horas/equipo` | Horas de todo el equipo | `ver_horas_equipo` |
| `GET` | `/api/v1/horas/{id}` | Obtener registro | Autenticado |
| `PUT` | `/api/v1/horas/{id}` | Editar (solo Borrador) | Propietario |
| `DELETE` | `/api/v1/horas/{id}` | Eliminar (solo Borrador) | Propietario |
| `POST` | `/api/v1/horas/enviar` | Enviar semana a aprobación | Autenticado |
| `POST` | `/api/v1/horas/{id}/aprobar` | Aprobar o rechazar | `aprobar_horas` |
| `POST` | `/api/v1/horas/timer/iniciar` | Iniciar timer | Autenticado |
| `POST` | `/api/v1/horas/{id}/timer/detener` | Detener timer y calcular horas | Propietario |

### Feriados

| Método | Endpoint | Descripción | Permiso |
|---|---|---|---|
| `GET` | `/api/v1/feriados/` | Listar feriados | Autenticado |
| `POST` | `/api/v1/feriados/` | Crear feriado | `admin_feriados` |
| `PUT` | `/api/v1/feriados/{id}` | Actualizar | `admin_feriados` |
| `DELETE` | `/api/v1/feriados/{id}` | Eliminar | `admin_feriados` |

### Export y Semanas

| Método | Endpoint | Descripción | Permiso |
|---|---|---|---|
| `GET` | `/api/v1/export/semanas/` | Listar semanas | Autenticado |
| `POST` | `/api/v1/export/semanas/` | Crear semana | `admin_proyectos` |
| `POST` | `/api/v1/export/semanas/{id}/cerrar` | Cerrar semana | `cerrar_sprint` |
| `GET` | `/api/v1/export/semanas/{id}/excel` | Descargar Excel `.xlsx` | `exportar_excel` |
| `POST` | `/api/v1/export/teams/test` | Probar webhook Teams | `admin_proyectos` |

---

## Sistema de permisos (RBAC)

Los permisos son **dinámicos**: se almacenan en la tabla `permisos` y se asignan a roles mediante `rol_permisos`. No es necesario modificar código para agregar nuevos permisos.

### Permisos del sistema

| Clave | Módulo | Descripción |
|---|---|---|
| `admin_usuarios` | usuarios | Crear, editar y desactivar usuarios |
| `admin_proyectos` | proyectos | Crear/editar proyectos, sprints y semanas |
| `ver_horas_equipo` | horas | Ver registros de cualquier usuario |
| `aprobar_horas` | horas | Aprobar o rechazar registros enviados |
| `cerrar_sprint` | sprints | Cerrar sprints y semanas |
| `exportar_excel` | export | Descargar el Excel semanal |
| `admin_feriados` | feriados | Gestionar feriados |

### Roles sugeridos

| Rol | Permisos recomendados |
|---|---|
| **Admin** | Todos |
| **Tech Lead** | `ver_horas_equipo`, `aprobar_horas`, `cerrar_sprint`, `exportar_excel` |
| **Profesional** | — (solo sus propias horas) |

---

## Instalación y configuración

### Requisitos previos

- Python **3.11** o superior
- **ODBC Driver 17 for SQL Server** instalado
- Acceso a una instancia de SQL Server
- Git

### Pasos

```bash
# 1. Descomprimir o clonar el proyecto
cd gestor-horas-final

# 2. Crear entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar y completar el .env
copy .env.example .env      # Windows
cp .env.example .env        # Linux/Mac
# → Editar .env con los datos reales (ver sección Variables de entorno)

# 5. Crear tablas en la BD
set PYTHONPATH=src           # Windows
export PYTHONPATH=src        # Linux/Mac
alembic upgrade head

# 6. Levantar el servidor
uvicorn app.main:app --reload
```

---

## Variables de entorno

Todas las variables se leen desde el archivo `.env` en la raíz del proyecto.

### Obligatorias

| Variable | Ejemplo | Descripción |
|---|---|---|
| `APP_ENV` | `development` | Entorno: `development`, `production` o `testing` |
| `DB_SERVER` | `LAPTOP-XYZ\SQLEXPRESS` | Servidor SQL Server (nombre o IP) |
| `DB_DATABASE` | `gestor_horas` | Nombre de la base de datos |
| `DB_USER` | `sa` | Usuario de la BD |
| `DB_PASSWORD` | `MiPassword123` | Contraseña de la BD |
| `SECRET_KEY` | `abc123...` | Clave JWT — mínimo 32 caracteres aleatorios |

### Opcionales

| Variable | Default | Descripción |
|---|---|---|
| `DB_PORT` | `1433` | Puerto SQL Server |
| `APP_VERSION` | `1.0.0` | Versión mostrada en `/health` y Swagger |
| `CORS_ORIGINS` | `http://localhost:5173` | Orígenes CORS permitidos (separados por coma) |
| `ALGORITHM` | `HS256` | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Expiración del token (8 horas por defecto) |
| `ADO_ORGANIZATION_URL` | — | URL de la organización ADO (ej: `https://dev.azure.com/mi-org`) |
| `ADO_PROJECT` | — | Nombre del proyecto en ADO |
| `ADO_PAT` | — | Personal Access Token de ADO (solo lectura) |
| `TEAMS_WEBHOOK_URL` | — | URL del webhook del canal de Teams |

> **Nota:** Si `APP_ENV=testing`, la app ignora la configuración de SQL Server y usa SQLite en memoria automáticamente.

### Generar SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Ejecución

### Servidor de desarrollo

```bash
# Con recarga automática ante cambios de código
set PYTHONPATH=src && uvicorn app.main:app --reload --port 8000
```

Accedé a la documentación interactiva en:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

### Producción

```bash
set PYTHONPATH=src && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

> En producción, Swagger y ReDoc se deshabilitan automáticamente (`APP_ENV != development`).

---

## Tests

### Estructura

Los tests están divididos en tres niveles:

| Nivel | Ubicación | BD | Tests |
|---|---|---|---|
| **Unitarios** | `tests/unit/` | Sin BD | 37 tests |
| **Integración** | `tests/integration/` | SQLite en memoria | 80 tests |
| **E2E** | `tests/e2e/` | BD de homologación | Robot Framework |

**Total: 117 tests — 100% pasando.**

### Comandos

```bash
# Todos los tests (sin coverage)
APP_ENV=testing pytest tests/unit/ tests/integration/ --no-cov

# Con reporte de coverage
APP_ENV=testing pytest tests/unit/ tests/integration/

# Solo unitarios
APP_ENV=testing pytest tests/unit/ --no-cov

# Solo integración
APP_ENV=testing pytest tests/integration/ --no-cov

# Un módulo específico
APP_ENV=testing pytest tests/integration/test_horas.py --no-cov -v

# Por marker
APP_ENV=testing pytest -m integration --no-cov
APP_ENV=testing pytest -m unit --no-cov
```

### Markers disponibles

| Marker | Descripción |
|---|---|
| `unit` | Tests sin dependencias externas |
| `integration` | Tests con BD SQLite en memoria |
| `e2e` | Tests contra entorno de homologación |
| `smoke` | Suite de smoke tests pre-release |
| `slow` | Tests lentos (excluir con `-m "not slow"`) |

---

## Integración con Azure DevOps

La sincronización descarga la jerarquía completa de Work Items de un proyecto ADO y la persiste localmente.

### Configuración

```env
ADO_ORGANIZATION_URL=https://dev.azure.com/mi-organizacion
ADO_PROJECT=NombreDelProyecto
ADO_PAT=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

El PAT necesita únicamente el permiso **Work Items — Read**.

### Proceso de sincronización

```
POST /api/v1/proyectos/{id}/sync-ado
```

1. Ejecuta consultas WIQL por tipo: Epic → Feature → User Story → Task
2. Descarga detalles en batches de 200 (límite de la API de ADO)
3. Hace upsert respetando la jerarquía (un Epic debe existir antes que su Feature)
4. Marca como `activo=False` los Work Items que ya no existen en ADO
5. Retorna conteos por tipo

> La sincronización es idempotente — se puede ejecutar múltiples veces sin duplicar datos.

---

## Export Excel

El Excel generado sigue el formato oficial del equipo:

| Columna | Contenido |
|---|---|
| Día | Nombre del día (Lunes, Martes…) |
| Mes | Nombre del mes (Enero, Febrero…) |
| Año | Número de año |
| Nombre | Nombre completo del profesional |
| Tipo | `Proyecto` u `Oficina` |
| ID Proyecto | Código del proyecto (`id_proyecto_excel`) |
| Descripción | Descripción del trabajo realizado |
| Tarea | `[ADO_ID] Título` o nombre manual |
| Horas | Horas con 2 decimales |

Incluye subtotales por usuario y total general. El archivo se descarga directamente como `.xlsx`:

```
GET /api/v1/export/semanas/{id}/excel
```

---

## Notificaciones Teams

Se envían Adaptive Cards al canal de Teams configurado en los siguientes eventos:

- Cierre de semana (`POST /export/semanas/{id}/cerrar`)
- Prueba manual (`POST /export/teams/test`)

Si `TEAMS_WEBHOOK_URL` no está configurado, las notificaciones se omiten silenciosamente sin afectar el flujo principal.

---

## Flujo de aprobación de horas

```
Profesional carga horas
        │
        ▼
   [BORRADOR] ──── editar / eliminar
        │
        │  POST /horas/enviar
        ▼
   [ENVIADO] ──── no se puede editar
        │
        │  POST /horas/{id}/aprobar
        ├──────────────────────────────────┐
        ▼                                  ▼
   [APROBADO]                        [RECHAZADO]
  incluido en Excel              vuelve a Borrador
                                  para corrección
```

### Validaciones en la carga

- ❌ No se puede cargar en **fines de semana**
- ❌ No se puede cargar en **feriados** (`aplica_a_todos=True`)
- ❌ No se puede cargar en **semanas cerradas**
- ❌ No se pueden superar **12 horas por día** por usuario
- ❌ No se puede tener **más de un timer activo** simultáneamente
- ❌ No se puede editar o eliminar un registro que no sea **Borrador**

---

## Roadmap

| Fase | Estado | Descripción |
|---|---|---|
| **Fase 1** | ✅ Completa | Modelos, config, database, security — 37 tests |
| **Fase 2** | ✅ Completa | Auth JWT, CRUD usuarios, RBAC |
| **Fase 3** | ✅ Completa | Proyectos, sprints, sync ADO |
| **Fase 4** | ✅ Completa | Carga de horas, timer, flujo aprobación |
| **Fase 5** | ✅ Completa | Ceremonias Scrum, cierre de semana, export Excel, Teams |
| **Fase 6** | 🔲 Pendiente | Frontend React + Vite + TailwindCSS |
| **Fase 7** | 🔲 Pendiente | Empaquetado como `.exe` con PyWebView + PyInstaller |
| **Fase 8** | 🔲 Pendiente | Dagster jobs (sync ADO nocturno, cierre automático) |
| **Fase 9** | 🔲 Pendiente | Dashboard Power BI |