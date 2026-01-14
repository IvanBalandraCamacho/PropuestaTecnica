"""
Service to generate Technical Proposal documents.
Uses Jinja2 for templating and htmldocx for HTML -> DOCX conversion.
"""
import logging
from datetime import datetime
from pathlib import Path
from io import BytesIO

# Nueva librería recomendada
from docxtpl import DocxTemplate

logger = logging.getLogger(__name__)

# Asegúrate de que template.docx esté en esta ruta
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

class ProposalGeneratorService:
    """Service to generate proposal documents using Word Templates."""

    def __init__(self):
        self.template_path = TEMPLATES_DIR / "tivit_proposal_template.docx"
        # Optional: Check if template exists on init, or lazy check on generation

 

    def generate_docx(self, context: dict) -> BytesIO:
        """
        Fills the Word template with data.
        """
        try:
            if not self.template_path.exists():
                raise FileNotFoundError(f"No se encontró la plantilla en {self.template_path}")
                
            doc = DocxTemplate(self.template_path)
            
            doc.render(context)
            
            file_stream = BytesIO()
            doc.save(file_stream)
            file_stream.seek(0)
            
            return file_stream
        except Exception as e:
            logger.error(f"Error generating DOCX from template: {e}")
            raise

    def prepare_context(self, rfp_data: dict) -> dict:
        data = rfp_data.get("extracted_data", {}) or {}
        
        # Contexto plano para facilitar el uso en Word
        context = {
            "client_name": data.get("client_name", "Cliente"),
        }
        
        # Mezclar todo por si acaso
        context.update(data)
        
        return context


# Singleton instance
_proposal_service: ProposalGeneratorService | None = None


def get_proposal_generator() -> ProposalGeneratorService:
    """Get or create proposal generator singleton."""
    global _proposal_service
    if _proposal_service is None:
        _proposal_service = ProposalGeneratorService()
    return _proposal_service
