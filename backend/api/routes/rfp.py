"""
Endpoints para gestión de RFPs.
Usa almacenamiento híbrido (GCS con fallback local).
"""
import json
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.dependencies import get_current_user
from core.storage import get_storage_service
from core.services.analyzer import get_analyzer_service
from core.services.mcp_client import get_mcp_client, convert_team_estimation_to_mcp_roles
from models.rfp import RFPSubmission, RFPQuestion, RFPStatus
from models.user import User
from models.schemas import (
    RFPSummary,
    RFPDetail,
    RFPDecision,
    RFPUpdate,
    UploadResponse,
    RFPListResponse,
    RFPQuestion as RFPQuestionSchema,
    TeamSuggestionRequest,
    TeamSuggestionResponse,
)
from schemas.chat import RFPChatRequest, RFPChatResponse
from core.gcp import get_gemini_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rfp", tags=["RFP"])


# ============ UPLOAD ============

@router.post("/upload", response_model=UploadResponse)
async def upload_rfp(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Sube un archivo RFP y realiza el análisis con Gemini.
    
    - Acepta PDF y DOCX
    - Guarda localmente (o GCS si está disponible)
    - Realiza análisis SÍNCRONO (espera a que termine)
    - Retorna cuando el análisis está completo
    """
    # Validar tipo de archivo
    allowed_types = [
        "application/pdf", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no soportado. Permitidos: PDF, DOCX"
        )
    
    # Leer contenido
    content = await file.read()
    file_size = len(content)
    
    # Obtener nombre de archivo
    filename = file.filename or "documento_sin_nombre.pdf"
    content_type = file.content_type or "application/pdf"
    
    # Guardar en storage (híbrido: GCS o local)
    storage = get_storage_service()
    file_uri = storage.upload_file(
        file_content=content,
        file_name=filename,
        content_type=content_type,
    )
    
    # Crear registro en BD
    rfp = RFPSubmission(
        file_name=filename,
        file_gcs_path=file_uri,
        file_size_bytes=file_size,
        status=RFPStatus.ANALYZING.value,  # Directamente analyzing
    )
    db.add(rfp)
    await db.commit()
    await db.refresh(rfp)
    
    # Obtener modo de análisis de las preferencias del usuario
    user_prefs = current_user.preferences or {}
    analysis_mode = user_prefs.get("analysis_mode", "balanced")
    logger.info(f"Using analysis mode: {analysis_mode} (from user preferences)")
    
    # Realizar análisis SÍNCRONO
    try:
        analyzer = get_analyzer_service()
        extracted_data = await analyzer.analyze_rfp_from_content(
            content, 
            filename,
            analysis_mode=analysis_mode,
            db=db,
        )
        
        # Extraer campos indexados
        indexed_fields = analyzer.extract_indexed_fields(extracted_data)
        
        # Actualizar RFP con resultados
        rfp.extracted_data = extracted_data
        rfp.status = RFPStatus.ANALYZED.value
        rfp.analyzed_at = datetime.utcnow()
        
        for field, value in indexed_fields.items():
            setattr(rfp, field, value)
        
        # Guardar recommended_isos en su columna específica
        if "recommended_isos" in extracted_data:
            rfp.recommended_isos = extracted_data["recommended_isos"]
        
        await db.commit()
        await db.refresh(rfp)
        
        logger.info(f"RFP analysis completed: {rfp.id}")
        
        return UploadResponse(
            id=rfp.id,
            file_name=filename,
            status=RFPStatus.ANALYZED.value,
            message="RFP subido y analizado exitosamente.",
        )
        
    except Exception as e:
        logger.error(f"Error analyzing RFP {rfp.id}: {e}")
        try:
            await db.rollback()
            # Re-fetch to avoid StaleDataError
            rfp = await db.get(RFPSubmission, rfp.id)
            if rfp:
                rfp.status = RFPStatus.ERROR.value
                await db.commit()
        except Exception as db_e:
            logger.error(f"Failed to update RFP status to ERROR: {db_e}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error al analizar el RFP: {str(e)}"
        )


async def analyze_rfp_task(rfp_id: str, file_uri: str, file_content: bytes):
    """Task en background para analizar el RFP."""
    from core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        rfp = None
        try:
            # Obtener RFP
            result = await db.execute(
                select(RFPSubmission).where(RFPSubmission.id == rfp_id)
            )
            rfp = result.scalar_one_or_none()
            
            if not rfp:
                logger.error(f"RFP not found: {rfp_id}")
                return
            
            # Actualizar status
            rfp.status = RFPStatus.ANALYZING.value
            await db.commit()
            
            # Analizar con Gemini
            analyzer = get_analyzer_service()
            extracted_data = await analyzer.analyze_rfp_from_content(file_content, rfp.file_name, db=db)
            
            # Extraer campos indexados
            indexed_fields = analyzer.extract_indexed_fields(extracted_data)
            
            # Actualizar RFP
            rfp.extracted_data = extracted_data
            rfp.status = RFPStatus.ANALYZED.value
            rfp.analyzed_at = datetime.utcnow()
            
            for field, value in indexed_fields.items():
                setattr(rfp, field, value)
            
            # Guardar recommended_isos en su columna específica
            if "recommended_isos" in extracted_data:
                rfp.recommended_isos = extracted_data["recommended_isos"]
            
            await db.commit()
            logger.info(f"RFP analysis completed: {rfp_id}")
            
        except Exception as e:
            logger.error(f"Error analyzing RFP {rfp_id}: {e}")
            if rfp:
                rfp.status = RFPStatus.ERROR.value
                await db.commit()


# ============ DOWNLOAD ============

@router.get("/{rfp_id}/download")
async def download_rfp(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Descarga el archivo original del RFP.
    """
    result = await db.execute(
        select(RFPSubmission).where(RFPSubmission.id == rfp_id)
    )
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP no encontrado")
    
    storage = get_storage_service()
    file_path = storage.get_file_path(rfp.file_gcs_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Determinar media type
    media_type = "application/pdf"
    if rfp.file_name.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    return FileResponse(
        path=str(file_path),
        filename=rfp.file_name,
        media_type=media_type,
    )


# ============ LIST & DETAIL ============

@router.get("", response_model=RFPListResponse)
async def list_rfps(
    current_user: User = Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    category: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Lista todos los RFPs con paginación y filtros.
    """
    # Query base
    query = select(RFPSubmission).order_by(RFPSubmission.created_at.desc())
    count_query = select(func.count(RFPSubmission.id))
    
    # Filtros
    if status:
        query = query.where(RFPSubmission.status == status)
        count_query = count_query.where(RFPSubmission.status == status)
    
    if category:
        query = query.where(RFPSubmission.category == category)
        count_query = count_query.where(RFPSubmission.category == category)
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            RFPSubmission.client_name.ilike(search_filter) |
            RFPSubmission.summary.ilike(search_filter)
        )
        count_query = count_query.where(
            RFPSubmission.client_name.ilike(search_filter) |
            RFPSubmission.summary.ilike(search_filter)
        )
    
    # Paginación
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Ejecutar queries
    result = await db.execute(query)
    rfps = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return RFPListResponse(
        items=[RFPSummary.model_validate(rfp) for rfp in rfps],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{rfp_id}", response_model=RFPDetail)
async def get_rfp(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene el detalle de un RFP incluyendo el análisis y preguntas.
    """
    result = await db.execute(
        select(RFPSubmission)
        .options(selectinload(RFPSubmission.questions))
        .where(RFPSubmission.id == rfp_id)
    )
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP no encontrado")
    
    return RFPDetail.model_validate(rfp)


# ============ UPDATE ============

@router.patch("/{rfp_id}", response_model=RFPDetail)
async def update_rfp(
    rfp_id: UUID,
    update_data: RFPUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza campos editables de un RFP.
    Campos actualizables: client_name, country, category, tvt, budget_min, budget_max, 
    currency, proposal_deadline, project_duration.
    NO se puede actualizar: summary (generado por IA).
    """
    result = await db.execute(
        select(RFPSubmission)
        .options(selectinload(RFPSubmission.questions))
        .where(RFPSubmission.id == rfp_id)
    )
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP no encontrado")
    
    # Validar TVT: solo números
    if update_data.tvt is not None:
        if update_data.tvt != "" and not update_data.tvt.isdigit():
            raise HTTPException(
                status_code=400, 
                detail="El campo TVT solo puede contener números"
            )
    
    # Actualizar solo los campos que vienen en el request
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        setattr(rfp, field, value)
    
    rfp.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(rfp)
    
    logger.info(f"RFP {rfp_id} updated: {list(update_dict.keys())}")
    
    return RFPDetail.model_validate(rfp)


# ============ DECISION ============

@router.post("/{rfp_id}/decision", response_model=RFPDetail)
async def make_decision(
    rfp_id: UUID,
    decision: RFPDecision,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    """
    Registra la decisión GO/NO GO para un RFP.
    
    - Si es GO, genera preguntas para el cliente
    - Si es NO GO, archiva el RFP
    """
    result = await db.execute(
        select(RFPSubmission)
        .options(selectinload(RFPSubmission.questions))
        .where(RFPSubmission.id == rfp_id)
    )
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP no encontrado")
    
    if rfp.status not in [RFPStatus.ANALYZED.value, RFPStatus.GO.value, RFPStatus.NO_GO.value]:
        raise HTTPException(
            status_code=400,
            detail="El RFP debe estar analizado antes de tomar una decisión"
        )
    
    # Actualizar decisión
    rfp.decision = decision.decision
    rfp.decision_reason = decision.reason
    rfp.decided_at = datetime.utcnow()
    rfp.status = RFPStatus.GO.value if decision.decision == "go" else RFPStatus.NO_GO.value
    
    # Si es GO, generar preguntas en background
    if decision.decision == "go" and rfp.extracted_data:
        background_tasks.add_task(
            generate_questions_task, 
            str(rfp.id), 
            rfp.extracted_data
        )
    
    await db.commit()
    await db.refresh(rfp)
    
    return RFPDetail.model_validate(rfp)


async def generate_questions_task(rfp_id: str, extracted_data: dict):
    """Task en background para generar preguntas."""
    from core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            analyzer = get_analyzer_service()
            questions = await analyzer.generate_questions(extracted_data)
            
            # Obtener RFP
            result = await db.execute(
                select(RFPSubmission).where(RFPSubmission.id == rfp_id)
            )
            rfp = result.scalar_one_or_none()
            
            if not rfp:
                return
            
            # Crear preguntas en BD
            for q in questions:
                question = RFPQuestion(
                    rfp_id=rfp.id,
                    question=q.get("question", ""),
                    category=q.get("category"),
                    priority=q.get("priority"),
                    context=q.get("context"),
                    why_important=q.get("why_important"),
                )
                db.add(question)
            
            await db.commit()
            logger.info(f"Generated {len(questions)} questions for RFP {rfp_id}")
            
        except Exception as e:
            logger.error(f"Error generating questions for RFP {rfp_id}: {e}")


# ============ QUESTIONS ============

@router.get("/{rfp_id}/questions", response_model=list[RFPQuestionSchema])
async def get_questions(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene las preguntas generadas para un RFP.
    """
    result = await db.execute(
        select(RFPQuestion)
        .where(RFPQuestion.rfp_id == rfp_id)
        .order_by(RFPQuestion.priority.desc(), RFPQuestion.created_at)
    )
    questions = result.scalars().all()
    
    return [RFPQuestionSchema.model_validate(q) for q in questions]


@router.post("/{rfp_id}/questions/regenerate", response_model=list[RFPQuestionSchema])
async def regenerate_questions(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Regenera las preguntas para un RFP.
    """
    result = await db.execute(
        select(RFPSubmission)
        .options(selectinload(RFPSubmission.questions))
        .where(RFPSubmission.id == rfp_id)
    )
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP no encontrado")
    
    if not rfp.extracted_data:
        raise HTTPException(status_code=400, detail="RFP no tiene datos de análisis")
    
    # Eliminar preguntas existentes
    for q in rfp.questions:
        await db.delete(q)
    
    # Generar nuevas preguntas
    analyzer = get_analyzer_service()
    questions = await analyzer.generate_questions(rfp.extracted_data)
    
    # Crear en BD
    new_questions = []
    for q in questions:
        question = RFPQuestion(
            rfp_id=rfp.id,
            question=q.get("question", ""),
            category=q.get("category"),
            priority=q.get("priority"),
            context=q.get("context"),
            why_important=q.get("why_important"),
        )
        db.add(question)
        new_questions.append(question)
    
    await db.commit()
    
    return [RFPQuestionSchema.model_validate(q) for q in new_questions]


# ============ DELETE ============

@router.delete("/{rfp_id}")
async def delete_rfp(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Elimina un RFP y su archivo local.
    """
    result = await db.execute(
        select(RFPSubmission).where(RFPSubmission.id == rfp_id)
    )
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP no encontrado")
    
    # Eliminar archivo local
    try:
        storage = get_storage_service()
        storage.delete_file(rfp.file_gcs_path)
    except Exception as e:
        logger.warning(f"Failed to delete local file: {e}")
    
    # Eliminar de BD (cascade eliminará las preguntas)
    await db.delete(rfp)
    await db.commit()
    
    return {"message": "RFP eliminado exitosamente"}


# ============ STORAGE STATS ============

@router.get("/storage/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene estadísticas del almacenamiento local.
    """
    storage = get_storage_service()
    return storage.get_storage_stats()


# ============ TEAM SUGGESTION ============

@router.post("/{rfp_id}/suggest-team")
async def suggest_team(
    rfp_id: UUID,
    request: TeamSuggestionRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Sugiere equipo real basado en el análisis del RFP.
    Conecta con MCP Talent Search para traer candidatos de TIVIT.
    
    El análisis incluye:
    - team_estimation: Roles, skills, certificaciones requeridas
    - cost_estimation: Costos estimados con tarifas de mercado (grounding)
    - suggested_team: Candidatos reales de TIVIT
    
    Los 4 escenarios:
    - A: Cliente define equipo + presupuesto -> Validar viabilidad
    - B: Sin equipo + con presupuesto -> IA sugiere equipo
    - C: Con equipo + sin presupuesto -> Estimar presupuesto
    - D: Sin equipo + sin presupuesto -> IA sugiere todo
    """
    force_refresh = request.force_refresh if request else False
    
    # Obtener RFP
    result = await db.execute(
        select(RFPSubmission).where(RFPSubmission.id == rfp_id)
    )
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP no encontrado")
    
    if not rfp.extracted_data:
        raise HTTPException(
            status_code=400, 
            detail="RFP no tiene datos de análisis. Debe analizarse primero."
        )
    
    # Verificar si ya tiene team_estimation
    team_estimation = rfp.extracted_data.get("team_estimation")
    cost_estimation = rfp.extracted_data.get("cost_estimation")
    suggested_team = rfp.extracted_data.get("suggested_team")
    
    if not team_estimation:
        raise HTTPException(
            status_code=400,
            detail="RFP no tiene estimación de equipo. Vuelva a analizar el documento."
        )
    
    # Si ya tiene suggested_team y no se fuerza refresh, retornarlo
    if suggested_team and not force_refresh:
        logger.info(f"Returning cached suggested team for RFP {rfp_id}")
        return {
            "rfp_id": rfp_id,
            "scenario": team_estimation.get("scenario", "D"),
            "team_estimation": team_estimation,
            "cost_estimation": cost_estimation,
            "suggested_team": suggested_team,
            "message": "Equipo sugerido (cache)",
        }
    
    # Obtener país del RFP
    country = rfp.extracted_data.get("country") or rfp.country or "Chile"
    
    # Convertir team_estimation a formato MCP
    mcp_roles = convert_team_estimation_to_mcp_roles(team_estimation, country)
    
    if not mcp_roles:
        raise HTTPException(
            status_code=400,
            detail="No se encontraron roles en la estimación de equipo."
        )
    
    logger.info(f"Searching candidates for {len(mcp_roles)} roles in {country}")
    
    # Verificar disponibilidad de MCP
    mcp_client = get_mcp_client()
    mcp_available = await mcp_client.health_check()
    
    if not mcp_available:
        logger.warning("MCP server not available, returning estimation only")
        return {
            "rfp_id": rfp_id,
            "scenario": team_estimation.get("scenario", "D"),
            "team_estimation": team_estimation,
            "cost_estimation": cost_estimation,
            "suggested_team": {
                "mcp_available": False,
                "error": "MCP Talent Search no disponible",
                "resultados": {},
                "total_candidatos": 0,
            },
            "message": "MCP no disponible. Solo se muestra estimación.",
        }
    
    # Llamar a MCP
    try:
        mcp_results = await mcp_client.search_team(mcp_roles)
        
        # Agregar metadata
        mcp_results["generated_at"] = datetime.utcnow().isoformat()
        mcp_results["mcp_available"] = True
        
        # Calcular cobertura
        roles_with_candidates = sum(
            1 for r in mcp_results.get("resultados", {}).values() 
            if r.get("total", 0) > 0
        )
        total_roles = len(mcp_roles)
        mcp_results["coverage_percent"] = (
            (roles_with_candidates / total_roles * 100) if total_roles > 0 else 0
        )
        
        # Guardar en extracted_data
        rfp.extracted_data["suggested_team"] = mcp_results
        rfp.updated_at = datetime.utcnow()
        await db.commit()
        
        logger.info(
            f"Found {mcp_results.get('total_candidatos', 0)} candidates "
            f"for {total_roles} roles"
        )
        
        return {
            "rfp_id": rfp_id,
            "scenario": team_estimation.get("scenario", "D"),
            "team_estimation": team_estimation,
            "cost_estimation": cost_estimation,
            "suggested_team": mcp_results,
            "message": f"Equipo sugerido con {mcp_results.get('total_candidatos', 0)} candidatos",
        }
        
    except Exception as e:
        logger.error(f"Error calling MCP: {e}")
        return {
            "rfp_id": rfp_id,
            "scenario": team_estimation.get("scenario", "D"),
            "team_estimation": team_estimation,
            "cost_estimation": cost_estimation,
            "suggested_team": {
                "mcp_available": False,
                "error": str(e),
                "resultados": {},
                "total_candidatos": 0,
            },
            "message": f"Error al buscar candidatos: {str(e)}",
        }


@router.get("/{rfp_id}/team-estimation")
async def get_team_estimation(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene la estimación de equipo, costos y candidatos sugeridos de un RFP.
    No llama a MCP, solo retorna los datos guardados del análisis.
    """
    result = await db.execute(
        select(RFPSubmission).where(RFPSubmission.id == rfp_id)
    )
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP no encontrado")
    
    if not rfp.extracted_data:
        raise HTTPException(status_code=400, detail="RFP no tiene datos de análisis")
    
    return {
        "rfp_id": rfp_id,
        "team_estimation": rfp.extracted_data.get("team_estimation"),
        "cost_estimation": rfp.extracted_data.get("cost_estimation"),
        "suggested_team": rfp.extracted_data.get("suggested_team"),
    }


# ============ CONTEXTUAL CHAT ============

@router.post("/{rfp_id}/chat", response_model=RFPChatResponse)
async def chat_with_rfp(
    rfp_id: UUID,
    request: RFPChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Chat contextual con un RFP.
    
    Responde preguntas basándose únicamente en los datos extraídos del RFP.
    Usa el contexto compacto (extracted_data) para optimizar el consumo de tokens.
    """
    # Obtener RFP
    result = await db.execute(
        select(RFPSubmission).where(RFPSubmission.id == rfp_id)
    )
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP no encontrado")
    
    if not rfp.extracted_data:
        raise HTTPException(
            status_code=400, 
            detail="RFP no tiene datos de análisis. Debe analizarse primero."
        )
    
    # Construir contexto compacto desde extracted_data
    extracted = rfp.extracted_data
    context_parts = [
        f"# Contexto del RFP: {rfp.file_name}",
        f"Cliente: {rfp.client_name or 'No especificado'}",
        f"País: {rfp.country or 'No especificado'}",
        f"Categoría: {rfp.category or 'No especificada'}",
        f"Resumen: {rfp.summary or 'No disponible'}",
    ]
    
    # Agregar presupuesto si existe
    budget = extracted.get("budget", {})
    if budget:
        budget_str = f"{budget.get('currency', 'USD')} {budget.get('amount_min', '?')} - {budget.get('amount_max', '?')}"
        context_parts.append(f"Presupuesto: {budget_str}")
        if budget.get("notes"):
            context_parts.append(f"Notas de presupuesto: {budget.get('notes')}")
    
    # Agregar duración y fechas
    if rfp.project_duration:
        context_parts.append(f"Duración del proyecto: {rfp.project_duration}")
    if rfp.proposal_deadline:
        context_parts.append(f"Fecha límite de propuesta: {rfp.proposal_deadline}")
    
    # Agregar tecnologías
    tech_stack = extracted.get("tech_stack", [])
    if tech_stack:
        context_parts.append(f"Stack tecnológico: {', '.join(tech_stack)}")
    
    # Agregar riesgos (importante para preguntas del usuario)
    risks = extracted.get("risks", [])
    if risks:
        context_parts.append("\n## Riesgos identificados:")
        for i, risk in enumerate(risks[:10], 1):  # Limitar a 10 riesgos
            severity = risk.get('severity', 'N/A')
            context_parts.append(f"{i}. [{severity.upper()}] {risk.get('category', '')}: {risk.get('description', '')}")
    
    # Agregar multas/penalidades
    penalties = extracted.get("penalties", [])
    if penalties:
        context_parts.append("\n## Multas y penalidades:")
        for i, penalty in enumerate(penalties[:10], 1):
            amount = f" ({penalty.get('amount')})" if penalty.get('amount') else ""
            high_tag = " [ALTA]" if penalty.get('is_high') else ""
            context_parts.append(f"{i}. {penalty.get('description', '')}{amount}{high_tag}")
    
    # Agregar SLAs
    slas = extracted.get("sla", [])
    if slas:
        context_parts.append("\n## SLAs:")
        for i, sla in enumerate(slas[:10], 1):
            metric = f" (Métrica: {sla.get('metric')})" if sla.get('metric') else ""
            aggressive_tag = " [AGRESIVO]" if sla.get('is_aggressive') else ""
            context_parts.append(f"{i}. {sla.get('description', '')}{metric}{aggressive_tag}")
    
    # Agregar experiencia requerida
    exp_req = extracted.get("experience_required", {})
    if exp_req and exp_req.get("required"):
        mandatory = " (OBLIGATORIO)" if exp_req.get('is_mandatory') else ""
        context_parts.append(f"\n## Experiencia requerida{mandatory}: {exp_req.get('details', 'Ver documento')}")
    
    # Agregar recomendación y razones
    if extracted.get("recommendation"):
        context_parts.append(f"\n## Recomendación: {extracted.get('recommendation')}")
        reasons = extracted.get("recommendation_reasons", [])
        if reasons:
            context_parts.append("Razones: " + "; ".join(reasons[:5]))
    
    # Agregar equipo sugerido (team_estimation)
    if extracted.get("team_estimation"):
        team = extracted.get("team_estimation")
        context_parts.append("\n## Equipo Sugerido por IA:")
        context_parts.append(f"Tipo de estimación: {team.get('estimation_type', 'N/A')}")
        context_parts.append(f"Confianza IA: {team.get('ai_confidence', 'N/A')}%")
        
        roles = team.get("roles", [])
        if roles:
            context_parts.append("Roles del equipo:")
            for role in roles[:15]:  # Limitar a 15 roles
                seniority = role.get('seniority', 'N/A')
                count = role.get('count', 1)
                dedication = role.get('dedication', 'Full Time')
                rate = role.get('monthly_rate', 0)
                context_parts.append(f"  - {role.get('role', 'Rol')}: {count}x {seniority} ({dedication}) - ${rate}/mes")
        
        if team.get("justification"):
            context_parts.append(f"Justificación: {team.get('justification')[:300]}")
    
    # Agregar estimación de costos si existe
    if extracted.get("cost_estimation"):
        cost = extracted.get("cost_estimation")
        context_parts.append("\n## Estimación de Costos:")
        context_parts.append(f"Costo mensual equipo: ${cost.get('monthly_team_cost', 0):,.0f}")
        context_parts.append(f"Duración estimada: {cost.get('duration_months', 0)} meses")
        context_parts.append(f"Costo total estimado: ${cost.get('total_cost', 0):,.0f}")
    
    context = "\n".join(context_parts)
    
    # System prompt con instrucciones
    system_prompt = f"""
Eres un asistente experto en análisis de RFPs (Request for Proposals).
Responde las preguntas del usuario ÚNICAMENTE basándote en el contexto del RFP proporcionado.

Reglas:
1. Sé conciso y directo en tus respuestas.
2. Si la información solicitada NO está en el contexto, indícalo claramente.
3. Cita secciones específicas cuando sea posible.
4. Para preguntas sobre riesgos, multas o SLAs, destaca los elementos más críticos.
5. Si el usuario pregunta sobre algo que podría afectar la propuesta comercial, advierte los riesgos potenciales.
6. Mantén coherencia con el historial de la conversación.

IMPORTANTE - Búsqueda de Candidatos:
- Si el usuario pregunta por candidatos, equipo de TIVIT, o personas para el proyecto, usa la herramienta search_candidates.
- El país por defecto del RFP es: {rfp.country or 'No especificado'}
- Si el usuario NO menciona un país específico, usa el país del RFP.
- Si el usuario menciona otro país (ej: "de Perú", "en México"), usa ese país en su lugar.
"""
    
    # Construir prompt con historial de conversación
    conversation_parts = [system_prompt, "\n", context, "\n"]
    
    # Agregar historial de conversación (últimos 20 mensajes)
    if request.history:
        conversation_parts.append("\n## Conversación previa:")
        for msg in request.history[-20:]:
            role_label = "Usuario" if msg.role == "user" else "Asistente"
            conversation_parts.append(f"{role_label}: {msg.content}")
        conversation_parts.append("")
    
    # Agregar mensaje actual
    conversation_parts.append(f"Usuario: {request.message}")
    conversation_parts.append("\nAsistente:")
    
    full_prompt = "\n".join(conversation_parts)
    
    # Definir herramienta de búsqueda de candidatos
    search_candidates_tool = {
        "name": "search_candidates",
        "description": "Busca candidatos de TIVIT que coincidan con un rol o skill específico. Usa esta herramienta cuando el usuario pregunte por equipo, candidatos, ingenieros, desarrolladores, o personal de TIVIT para el proyecto.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Rol o skills a buscar (ej: 'Desarrollador Java Senior', 'QA Tester con Selenium', 'Project Manager')"
                },
                "country": {
                    "type": "string", 
                    "description": f"País para filtrar candidatos. Usa '{rfp.country}' si el usuario no especifica otro."
                },
                "limit": {
                    "type": "integer",
                    "description": "Cantidad máxima de candidatos a retornar (default: 5)"
                }
            },
            "required": ["query"]
        }
    }
    
    # Llamar a Gemini con function calling
    try:
        import asyncio
        from google.genai.types import Tool, FunctionDeclaration
        
        gemini = get_gemini_client()
        
        # Primera llamada: verificar si necesita usar herramienta
        response = await asyncio.to_thread(
            gemini.client.models.generate_content,
            model="gemini-3-flash-preview",
            contents=full_prompt,
            config={
                "temperature": 0.3,
                "max_output_tokens": 8192,
                "tools": [{
                    "function_declarations": [search_candidates_tool]
                }],
            },
        )
        
        # Verificar si hay function call
        function_call = None
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    break
        
        final_response = ""
        
        if function_call and function_call.name == "search_candidates":
            # Ejecutar búsqueda en MCP
            args = dict(function_call.args) if function_call.args else {}
            query = args.get("query", "")
            country = args.get("country", rfp.country or None)
            limit = args.get("limit", 5)
            
            logger.info(f"MCP search triggered: query='{query}', country='{country}', limit={limit}")
            
            # Llamar a MCP
            mcp_client = get_mcp_client()
            mcp_result = await mcp_client.search_single(
                query=query,
                limit=limit,
                country=country
            )
            
            # Formatear resultados para Gemini
            candidates = mcp_result.get("candidatos", [])
            
            # Fallback: Si no hay resultados en el país específico, buscar globalmente
            search_context_msg = ""
            if not candidates and country:
                logger.info(f"No candidates found in {country}, trying global search")
                mcp_result_global = await mcp_client.search_single(
                    query=query,
                    limit=limit,
                    country=None
                )
                candidates = mcp_result_global.get("candidatos", [])
                if candidates:
                    search_context_msg = f"⚠️ No se encontraron candidatos en {country}. Aquí hay sugerencias de otros países:"
            
            if candidates:
                header = search_context_msg if search_context_msg else f"\n\n## Candidatos encontrados ({len(candidates)}):\n"
                candidates_text = header
                for i, c in enumerate(candidates[:limit], 1):
                    certs = ", ".join([cert.get("nombre", "") for cert in c.get("certificaciones", [])[:3]])
                    skills = ", ".join([s.get("nombre", "") for s in c.get("skills", [])[:5]])
                    lider = c.get("lider", {}) or {}
                    lider_info = f"{lider.get('nombre', 'N/A')} ({lider.get('email', 'N/A')})"
                    
                    candidates_text += f"""
{i}. **{c.get('nombre', 'N/A')}** - {c.get('cargo', 'N/A')}
   - País: {c.get('pais', 'N/A')}
   - Email: {c.get('email', 'N/A')}
   - Jefe Directo: {lider_info}
   - Certificaciones: {certs or 'Ninguna'}
   - Skills: {skills or 'No especificados'}
"""
            else:
                candidates_text = "\n\nNo se encontraron candidatos que coincidan con la búsqueda."
            
            # Segunda llamada a Gemini con los resultados
            followup_prompt = f"""{full_prompt}

[Se ejecutó búsqueda de candidatos en TIVIT]
Búsqueda: "{query}" en {country or 'todos los países'}
{candidates_text}

Basándote en estos resultados, responde al usuario de forma clara y útil. Si hay candidatos, preséntelos de forma organizada."""

            response2 = await asyncio.to_thread(
                gemini.client.models.generate_content,
                model="gemini-3-flash-preview",
                contents=followup_prompt,
                config={
                    "temperature": 0.3,
                    "max_output_tokens": 8192,
                },
            )
            final_response = response2.text if response2.text else "No pude generar una respuesta."
        else:
            # Sin function call, usar respuesta directa
            final_response = response.text if response.text else "No pude generar una respuesta."
        
        return RFPChatResponse(
            response=final_response,
            rfp_id=str(rfp_id),
        )
        
    except Exception as e:
        logger.error(f"Error in RFP chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la consulta: {str(e)}"
        )

