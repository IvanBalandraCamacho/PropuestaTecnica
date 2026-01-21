"""
Servicio para la gestión lógica del almacenamiento (Carpetas y Archivos en BD).
"""
import uuid
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.storage import Carpeta, UsuarioCarpeta
from models.user import User

logger = logging.getLogger(__name__)

async def create_folder(
    db: AsyncSession,
    name: str,
    codigo: Optional[str] = None,
    prefijo: Optional[str] = None,
    parent_id: Optional[uuid.UUID] = None,
    url: Optional[str] = None,
) -> Carpeta:
    """
    Crea una carpeta en la base de datos.
    """
    folder = Carpeta(
        nombre=name,
        codigo=codigo,
        prefijo=prefijo,
        url=url,
        parent_id=parent_id
    )
    db.add(folder)
    await db.flush() # Populate ID
    await db.refresh(folder)
    return folder

async def link_folder_to_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    folder_id: uuid.UUID,
    rfp_id: Optional[uuid.UUID] = None
) -> UsuarioCarpeta:
    """
    Asocia una carpeta a un usuario.
    """
    link = UsuarioCarpeta(
        usuario_id=user_id,
        carpeta_id=folder_id,
        rfp_submissions_id=rfp_id
    )
    db.add(link)
    return link

async def init_user_storage(db: AsyncSession, user_id: uuid.UUID):
    """
    Inicializa la estructura de carpetas para un nuevo usuario.
    Estructura:
    - /usuario_id (Root)
        - /go
        - /no_go
    """
    try:
        user_str_id = str(user_id)
        
        # 1. Crear Carpeta Root del Usuario
        root_folder_name = f"user_{user_str_id}"
        root_url = f"/{user_str_id}" 
        
        root_folder = await create_folder(
            db=db,
            name=root_folder_name,
            codigo=user_str_id,
            prefijo="root",
            url=root_url
        )
        
        # Enlazar root al usuario
        await link_folder_to_user(db, user_id, root_folder.carpeta_id)
        
        # 2. Crear Carpeta GO (Hija de Root)
        go_folder = await create_folder(
            db=db,
            name="Proyectos Aprobados (GO)",
            prefijo="go",
            url=f"{root_url}/go",
            parent_id=root_folder.carpeta_id
        )
        # Opcional: ¿Enlazar subcarpetas a usuario? 
        # Si la UI navega desde Root, no es estrictamente necesario, pero ayuda para acceso directo.
        # Por ahora solo enlazamos Root.
        # await link_folder_to_user(db, user_id, go_folder.carpeta_id)
        
        # 3. Crear Carpeta NO GO (Hija de Root)
        nogo_folder = await create_folder(
            db=db,
            name="Proyectos Rechazados (NO GO)",
            prefijo="no_go",
            url=f"{root_url}/no_go",
            parent_id=root_folder.carpeta_id
        )
        # await link_folder_to_user(db, user_id, nogo_folder.carpeta_id)
        
        # Commit se hará en la llamada principal (register)
        logger.info(f"Storage initiated for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error initializing user storage: {e}")
        raise e
