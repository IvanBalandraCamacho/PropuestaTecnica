"""
Endpoints para la generación de propuestas.
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from core.services.proposal_generator import get_proposal_generator
from models.rfp import RFPSubmission
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposal", tags=["Proposal"])

@router.get("/generate/{rfp_id}")
async def generate_proposal(
    rfp_id: UUID, 
    db: AsyncSession = Depends(get_db)
    ):

    result = await db.execute(
        select(RFPSubmission).where(RFPSubmission.id == rfp_id)
    )
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP no encontrado")
    
    if not rfp.extracted_data:
        raise HTTPException(
            status_code=400, 
            detail="El RFP no ha sido analizado o no tiene datos extraídos."
        )
    
    try:
        generator = get_proposal_generator()
        
        rfp_data = {
            "extracted_data": rfp.extracted_data
        }
        
        # 1. Obtener el contexto (datos) en lugar de HTML string
        context_data = generator.prepare_context(rfp_data) 
        
        # 2. Generar el DOCX usando el contexto y la plantilla
        docx_stream = generator.generate_docx(context_data)
        
        filename = f"Propuesta_{rfp.client_name or 'TIVIT'}_{datetime.now().strftime('%Y%m%d')}.docx"
        
        return StreamingResponse(
            docx_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error creating proposal for RFP {rfp.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando la propuesta: {e}")


