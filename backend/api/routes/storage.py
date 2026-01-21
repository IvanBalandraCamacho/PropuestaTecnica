"""
Endpoints para la gestión de Storage (Carpetas y Archivos estructurados).
"""
import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.dependencies import get_current_user
from core.storage import get_storage_service
from models.user import User
from models.storage import Carpeta, Archivo, UsuarioCarpeta
from models.schemas.storage_schemas import CarpetaSchema, CarpetaDetailSchema, ArchivoSchema, FolderContentSchema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/storage", tags=["Storage"])

@router.get("/files/{file_id}/download")
async def download_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Descarga un archivo.
    """
    result = await db.execute(select(Archivo).where(Archivo.archivo_id == file_id))
    archivo = result.scalar_one_or_none()
    
    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
    storage = get_storage_service()
    
    # Check if URL is valid
    if not archivo.url:
        raise HTTPException(status_code=400, detail="El archivo no tiene URL válida")

    # Strategy: Redirect if GCS signed URL available, or FileResponse if local
    signed_url = storage.get_signed_url(archivo.url)
    if signed_url:
        return RedirectResponse(url=signed_url)
        
    # Check for local file
    local_path = storage.get_file_path(archivo.url)
    if local_path and local_path.exists():
         return FileResponse(
            path=str(local_path),
            filename=archivo.nombre or "downloaded_file",
            media_type="application/octet-stream" # Or mimetype guess
        )

    # Fallback/Error
    raise HTTPException(status_code=404, detail="Archivo físico no encontrado")

@router.get("/folders", response_model=List[CarpetaSchema])
async def list_folders(
    parent_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista las carpetas.
    - Si parent_id es None: Retorna las carpetas raíz del usuario.
    - Si parent_id existe: Retorna las subcarpetas de esa carpeta.
    """
    if parent_id is None:
        # Obtener carpetas raíz asociadas al usuario
        query = (
            select(Carpeta)
            .join(UsuarioCarpeta)
            .where(
                UsuarioCarpeta.usuario_id == current_user.id,
                Carpeta.habilitado == True
            )
        )
    else:
        # Obtener subcarpetas
        query = (
            select(Carpeta)
            .where(
                Carpeta.parent_id == parent_id,
                Carpeta.habilitado == True
            )
        )
    
    result = await db.execute(query)
    folders = result.scalars().all()
    return folders

@router.get("/folders/{folder_id}", response_model=FolderContentSchema)
async def get_folder_content(
    folder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene el contenido de una carpeta (info, subcarpetas, archivos).
    """
    # 1. Obtener la carpeta
    result = await db.execute(select(Carpeta).where(Carpeta.carpeta_id == folder_id))
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    # 2. Obtener subcarpetas
    sub_result = await db.execute(
        select(Carpeta).where(
            Carpeta.parent_id == folder_id,
            Carpeta.habilitado == True
        )
    )
    subfolders = sub_result.scalars().all()
    
    # 3. Obtener archivos
    files_result = await db.execute(
        select(Archivo).where(
            Archivo.carpeta_id == folder_id,
            Archivo.habilitado == True
        )
    )
    files = files_result.scalars().all()
    
    # 4. Construir breadcrumbs (simpificado, solo parent por ahora)
    path = []
    current = folder
    # TODO: Implementar recursión real para path completo si es necesario
    # Por ahora retornamos el folder actual
    path.append(folder)
    
    return {
        "carpeta": folder,
        "subcarpetas": subfolders,
        "archivos": files,
        "path": path 
    }
