"""
services/ado_service.py — Sincronización con Azure DevOps.

Obtiene la jerarquía completa Epic → Feature → User Story → Task
de un proyecto ADO y la persiste/actualiza en la BD local.

Requiere en .env:
    ADO_ORGANIZATION_URL  = https://dev.azure.com/mi-org
    ADO_PROJECT           = NombreProyecto
    ADO_PAT               = xxxxxxxxxxxx (Personal Access Token, readonly)

Usa la librería azure-devops (pip install azure-devops).
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

from app.core.config import get_settings
from app.models.ado_item import AdoItem, TipoAdoItem
from app.models.proyecto import Proyecto
from app.schemas.proyecto import SyncAdoResponse

logger = logging.getLogger(__name__)

# Mapa de tipo ADO → enum local
_TIPO_MAP: dict[str, TipoAdoItem] = {
    "Epic":       TipoAdoItem.EPIC,
    "Feature":    TipoAdoItem.FEATURE,
    "User Story": TipoAdoItem.USER_STORY,
    "Task":       TipoAdoItem.TASK,
}


def _get_work_item_client():
    """Crea y retorna el cliente de Work Items de ADO."""
    settings = get_settings()
    credentials = BasicAuthentication("", settings.ADO_PAT)
    connection = Connection(
        base_url=settings.ADO_ORGANIZATION_URL,
        creds=credentials,
    )
    return connection.clients.get_work_item_tracking_client()


def _fetch_ids_by_type(client, ado_project: str, tipo: str) -> list[int]:
    """
    Ejecuta un WIQL para obtener todos los Work Item IDs de un tipo.

    Args:
        client: Cliente de Work Item Tracking de ADO.
        ado_project: Nombre del proyecto en ADO.
        tipo: Tipo de Work Item (Epic, Feature, User Story, Task).

    Returns:
        Lista de IDs de Work Items del tipo solicitado.
    """
    wiql = {
        "query": (
            f"SELECT [System.Id] FROM WorkItems "
            f"WHERE [System.TeamProject] = '{ado_project}' "
            f"AND [System.WorkItemType] = '{tipo}' "
            f"AND [System.State] <> 'Removed' "
            f"ORDER BY [System.Id]"
        )
    }
    result = client.query_by_wiql(wiql, project=ado_project)
    return [item.id for item in (result.work_items or [])]


def _fetch_work_items_batch(client, ids: list[int]) -> list[dict]:
    """
    Obtiene los detalles de Work Items en batches de 200 (límite de la API).

    Args:
        client: Cliente de Work Item Tracking de ADO.
        ids: Lista de IDs a obtener.

    Returns:
        Lista de diccionarios con los campos de cada Work Item.
    """
    if not ids:
        return []

    fields = [
        "System.Id",
        "System.Title",
        "System.WorkItemType",
        "System.State",
        "System.AssignedTo",
        "System.Parent",
        "System.IterationId",
    ]

    items = []
    # API de ADO tiene límite de 200 items por request
    for i in range(0, len(ids), 200):
        batch = ids[i:i + 200]
        work_items = client.get_work_items(
            ids=batch,
            fields=fields,
            error_policy="omit",
        )
        items.extend(work_items or [])

    return items


def _upsert_item(
    db: Session,
    wi: object,
    proyecto_id: int,
    ado_id_to_local_id: dict[int, int],
) -> AdoItem:
    """
    Inserta o actualiza un AdoItem en la BD.

    Args:
        db: Sesión de BD.
        wi: Work Item de ADO.
        proyecto_id: ID del proyecto local.
        ado_id_to_local_id: Mapa de ado_id → id local para resolver parent_id.

    Returns:
        El AdoItem persistido.
    """
    fields = wi.fields
    ado_id: int = fields["System.Id"]
    tipo_str: str = fields.get("System.WorkItemType", "")
    tipo = _TIPO_MAP.get(tipo_str)
    if tipo is None:
        logger.warning(f"Tipo desconocido '{tipo_str}' para ado_id={ado_id}, omitiendo")
        return None

    # Resolver parent
    parent_ado_id: int | None = fields.get("System.Parent")
    parent_local_id = ado_id_to_local_id.get(parent_ado_id) if parent_ado_id else None

    # Asignado
    assigned_to = fields.get("System.AssignedTo")
    if isinstance(assigned_to, dict):
        assigned_to = assigned_to.get("uniqueName") or assigned_to.get("displayName")

    existing = db.query(AdoItem).filter(AdoItem.ado_id == ado_id).first()

    if existing:
        existing.titulo = fields.get("System.Title", existing.titulo)
        existing.estado = fields.get("System.State")
        existing.asignado_a = assigned_to
        existing.parent_id = parent_local_id
        existing.activo = True
        existing.ultima_sync = datetime.now(timezone.utc)
        item = existing
    else:
        item = AdoItem(
            ado_id=ado_id,
            tipo=tipo,
            titulo=fields.get("System.Title", f"Work Item {ado_id}"),
            estado=fields.get("System.State"),
            asignado_a=assigned_to,
            proyecto_id=proyecto_id,
            parent_id=parent_local_id,
            activo=True,
            ultima_sync=datetime.now(timezone.utc),
        )
        db.add(item)

    return item


def sync_proyecto_ado(db: Session, proyecto: Proyecto) -> SyncAdoResponse:
    """
    Sincroniza todos los Work Items de ADO para un proyecto.

    Proceso:
        1. Obtiene IDs por tipo (Epic, Feature, US, Task) via WIQL.
        2. Descarga los detalles en batches de 200.
        3. Upsert en la BD respetando la jerarquía (padre resuelto por ado_id).
        4. Marca como inactivos los ítems que ya no existen en ADO.

    Args:
        db: Sesión de BD activa.
        proyecto: Proyecto local con ado_project_name configurado.

    Returns:
        SyncAdoResponse con conteos por tipo.

    Raises:
        ValueError: Si el proyecto no tiene ado_project_name configurado.
        Exception: Si la conexión a ADO falla.
    """
    if not proyecto.ado_project_name:
        raise ValueError(
            f"El proyecto '{proyecto.nombre}' no tiene ado_project_name configurado"
        )

    ado_project = proyecto.ado_project_name
    logger.info(f"Iniciando sync ADO para proyecto '{ado_project}'")

    client = _get_work_item_client()

    # Obtener IDs por tipo (en orden jerárquico para resolver parents)
    conteos: dict[str, int] = {}
    todos_ids: list[int] = []
    orden = ["Epic", "Feature", "User Story", "Task"]

    ids_por_tipo: dict[str, list[int]] = {}
    for tipo in orden:
        ids = _fetch_ids_by_type(client, ado_project, tipo)
        ids_por_tipo[tipo] = ids
        todos_ids.extend(ids)
        logger.info(f"  {tipo}: {len(ids)} items")

    # Descargar todos los detalles
    work_items = _fetch_work_items_batch(client, todos_ids)

    # Indexar por ado_id para acceso rápido
    wi_by_ado_id = {wi.fields["System.Id"]: wi for wi in work_items}

    # Mapa ado_id → local_id (para resolver parents)
    ado_id_to_local_id: dict[int, int] = {
        item.ado_id: item.id
        for item in db.query(AdoItem).filter(AdoItem.proyecto_id == proyecto.id).all()
    }

    # Upsert en orden jerárquico (primero Epics para que los Features puedan resolverlos)
    db.flush()  # Asegura que los IDs generados estén disponibles

    for tipo in orden:
        for ado_id in ids_por_tipo[tipo]:
            wi = wi_by_ado_id.get(ado_id)
            if not wi:
                continue
            item = _upsert_item(db, wi, proyecto.id, ado_id_to_local_id)
            if item:
                db.flush()
                # Actualizar mapa con el nuevo local_id
                if item.id:
                    ado_id_to_local_id[ado_id] = item.id

    # Marcar como inactivos los que ya no están en ADO
    ids_activos_ado = set(todos_ids)
    db.query(AdoItem).filter(
        AdoItem.proyecto_id == proyecto.id,
        AdoItem.ado_id.notin_(ids_activos_ado),
    ).update({"activo": False}, synchronize_session=False)

    db.commit()

    # Conteos finales
    from sqlalchemy import func as sqlfunc
    from app.models.ado_item import TipoAdoItem as T
    conteos_db = (
        db.query(AdoItem.tipo, sqlfunc.count(AdoItem.id))
        .filter(AdoItem.proyecto_id == proyecto.id, AdoItem.activo == True)
        .group_by(AdoItem.tipo)
        .all()
    )
    c = {str(t): n for t, n in conteos_db}

    return SyncAdoResponse(
        proyecto_id=proyecto.id,
        ado_project_name=ado_project,
        epicas=c.get("Epic", 0),
        features=c.get("Feature", 0),
        user_stories=c.get("User Story", 0),
        tasks=c.get("Task", 0),
        total=sum(c.values()),
        mensaje=f"Sincronización completada: {sum(c.values())} ítems activos",
    )
