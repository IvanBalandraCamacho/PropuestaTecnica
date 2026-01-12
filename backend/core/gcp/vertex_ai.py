"""
Cliente para Gemini via Vertex AI.
Usa el SDK de google-cloud-aiplatform con credenciales de servicio.
"""
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class APIConsumptionLog:
    """Registro de consumo de API."""
    timestamp: datetime
    model: str
    operation: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    thinking_tokens: int = 0
    latency_ms: float = 0
    success: bool = True
    error: str | None = None
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "operation": self.operation,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "thinking_tokens": self.thinking_tokens,
            "latency_ms": round(self.latency_ms, 2),
            "success": self.success,
            "error": self.error,
        }


@dataclass
class ConsumptionTracker:
    """Tracker para monitorear consumo total de API."""
    logs: list[APIConsumptionLog] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_thinking_tokens: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    
    def add_log(self, log: APIConsumptionLog):
        """Agrega un log y actualiza totales."""
        self.logs.append(log)
        self.total_requests += 1
        
        if log.success:
            self.total_input_tokens += log.input_tokens
            self.total_output_tokens += log.output_tokens
            self.total_thinking_tokens += log.thinking_tokens
        else:
            self.failed_requests += 1
        
        # Log to console
        self._log_to_console(log)
    
    def _log_to_console(self, log: APIConsumptionLog):
        """Imprime log formateado en consola."""
        status = "SUCCESS" if log.success else "FAILED"
        logger.info(
            f"\n{'='*60}\n"
            f"VERTEX AI GEMINI CONSUMPTION LOG\n"
            f"{'='*60}\n"
            f"Timestamp: {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Operation: {log.operation}\n"
            f"Model: {log.model}\n"
            f"Status: {status}\n"
            f"Latency: {log.latency_ms:.2f}ms\n"
            f"---\n"
            f"Input Tokens: {log.input_tokens:,}\n"
            f"Output Tokens: {log.output_tokens:,}\n"
            f"Total Tokens: {log.total_tokens:,}\n"
            f"---\n"
            f"Session Totals:\n"
            f"  Total Requests: {self.total_requests}\n"
            f"  Failed Requests: {self.failed_requests}\n"
            f"  Total Input: {self.total_input_tokens:,}\n"
            f"  Total Output: {self.total_output_tokens:,}\n"
            f"{'='*60}\n"
        )
    
    def get_summary(self) -> dict:
        """Retorna resumen de consumo."""
        return {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (
                (self.total_requests - self.failed_requests) / self.total_requests * 100
                if self.total_requests > 0 else 0
            ),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_thinking_tokens": self.total_thinking_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens + self.total_thinking_tokens,
            "recent_logs": [log.to_dict() for log in self.logs[-10:]],
        }


# Tracker global
consumption_tracker = ConsumptionTracker()


class GeminiClient:
    """Cliente para interactuar con Gemini via Vertex AI."""
    
    def __init__(self):
        """Inicializa el cliente de Vertex AI."""
        # Configurar credenciales
        credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        if credentials_path and os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            logger.info(f"Using GCP credentials from: {credentials_path}")
        else:
            logger.warning(f"Credentials file not found: {credentials_path}")
        
        # Obtener project ID
        project_id = settings.GCP_PROJECT_ID
        if not project_id:
            raise ValueError("GCP_PROJECT_ID no configurado")
        
        location = settings.GCP_LOCATION
        
        # Inicializar Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # Usar modelo Gemini
        self.model_id = settings.GEMINI_MODEL
        self.model = GenerativeModel(self.model_id)
        
        logger.info(f"Vertex AI initialized - Project: {project_id}, Location: {location}")
        logger.info(f"Gemini model: {self.model_id}")
    
    def _extract_token_counts(self, response) -> tuple[int, int, int]:
        """Extrae conteo de tokens de la respuesta."""
        input_tokens = 0
        output_tokens = 0
        thinking_tokens = 0
        
        try:
            if hasattr(response, 'usage_metadata'):
                metadata = response.usage_metadata
                input_tokens = getattr(metadata, 'prompt_token_count', 0) or 0
                output_tokens = getattr(metadata, 'candidates_token_count', 0) or 0
        except Exception as e:
            logger.warning(f"Could not extract token counts: {e}")
        
        return input_tokens, output_tokens, thinking_tokens
    
    async def analyze_document(
        self, 
        document_content: str,
        prompt: str,
        temperature: float = 0.1,
        max_output_tokens: int = 8192,
    ) -> dict[str, Any]:
        """
        Analiza un documento con Gemini via Vertex AI.
        
        Args:
            document_content: Contenido del documento (texto extraído)
            prompt: Prompt para el análisis
            temperature: Temperatura para generación (0.0-2.0)
            max_output_tokens: Máximo de tokens de salida
            
        Returns:
            Dict con el resultado del análisis parseado desde JSON
        """
        start_time = time.time()
        log = APIConsumptionLog(
            timestamp=datetime.now(),
            model=self.model_id,
            operation="analyze_document",
        )
        
        try:
            # Configuración de generación
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",
            )
            
            # Construir prompt completo
            full_prompt = f"""
{prompt}

DOCUMENTO A ANALIZAR:
---
{document_content}
---

Responde ÚNICAMENTE con JSON válido siguiendo el schema indicado.
"""
            
            logger.info(f"Analyzing document with Vertex AI ({self.model_id})")
            
            # Generar contenido
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )
            
            # Extraer tokens
            input_tokens, output_tokens, thinking_tokens = self._extract_token_counts(response)
            log.input_tokens = input_tokens
            log.output_tokens = output_tokens
            log.thinking_tokens = thinking_tokens
            log.total_tokens = input_tokens + output_tokens + thinking_tokens
            
            # Parsear respuesta JSON
            result = json.loads(response.text)
            
            log.latency_ms = (time.time() - start_time) * 1000
            log.success = True
            consumption_tracker.add_log(log)
            
            logger.info("Document analysis completed successfully")
            return result
            
        except json.JSONDecodeError as e:
            log.latency_ms = (time.time() - start_time) * 1000
            log.success = False
            log.error = f"Invalid JSON: {str(e)}"
            consumption_tracker.add_log(log)
            
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            return {"raw_response": response.text if 'response' in dir() else "", "error": "Invalid JSON response"}
            
        except Exception as e:
            log.latency_ms = (time.time() - start_time) * 1000
            log.success = False
            log.error = str(e)
            consumption_tracker.add_log(log)
            
            logger.error(f"Error analyzing document: {e}")
            raise
    
    async def analyze_pdf_from_gcs(
        self,
        gcs_uri: str,
        prompt: str,
        temperature: float = 0.1,
        max_output_tokens: int = 8192,
    ) -> dict[str, Any]:
        """
        Analiza un PDF directamente desde GCS con Gemini via Vertex AI.
        
        Args:
            gcs_uri: URI del archivo en GCS (gs://bucket/path/file.pdf)
            prompt: Prompt para el análisis
            temperature: Temperatura para generación
            max_output_tokens: Máximo de tokens de salida
            
        Returns:
            Dict con el resultado del análisis
        """
        start_time = time.time()
        log = APIConsumptionLog(
            timestamp=datetime.now(),
            model=self.model_id,
            operation="analyze_pdf_gcs",
        )
        
        try:
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",
            )
            
            # Crear referencia al archivo PDF desde GCS
            pdf_part = Part.from_uri(gcs_uri, mime_type="application/pdf")
            
            logger.info(f"Analyzing PDF from GCS: {gcs_uri}")
            
            response = self.model.generate_content(
                [pdf_part, prompt],
                generation_config=generation_config,
            )
            
            input_tokens, output_tokens, thinking_tokens = self._extract_token_counts(response)
            log.input_tokens = input_tokens
            log.output_tokens = output_tokens
            log.thinking_tokens = thinking_tokens
            log.total_tokens = input_tokens + output_tokens + thinking_tokens
            
            result = json.loads(response.text)
            
            log.latency_ms = (time.time() - start_time) * 1000
            log.success = True
            consumption_tracker.add_log(log)
            
            return result
            
        except Exception as e:
            log.latency_ms = (time.time() - start_time) * 1000
            log.success = False
            log.error = str(e)
            consumption_tracker.add_log(log)
            
            logger.error(f"Error analyzing PDF from GCS: {e}")
            raise
    
    async def generate_questions(
        self,
        rfp_data: dict[str, Any],
        prompt: str,
        temperature: float = 0.3,
    ) -> list[dict[str, Any]]:
        """
        Genera preguntas basadas en el análisis del RFP.
        
        Args:
            rfp_data: Datos extraídos del RFP
            prompt: Prompt para generación de preguntas
            temperature: Temperatura para generación
            
        Returns:
            Lista de preguntas generadas
        """
        start_time = time.time()
        log = APIConsumptionLog(
            timestamp=datetime.now(),
            model=self.model_id,
            operation="generate_questions",
        )
        
        try:
            full_prompt = f"""
{prompt}

DATOS DEL RFP ANALIZADO:
```json
{json.dumps(rfp_data, ensure_ascii=False, indent=2)}
```

Genera las preguntas en formato JSON como un array de objetos.
"""
            
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=4096,
                response_mime_type="application/json",
            )
            
            logger.info("Generating questions with Vertex AI")
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )
            
            input_tokens, output_tokens, thinking_tokens = self._extract_token_counts(response)
            log.input_tokens = input_tokens
            log.output_tokens = output_tokens
            log.thinking_tokens = thinking_tokens
            log.total_tokens = input_tokens + output_tokens + thinking_tokens
            
            result = json.loads(response.text)
            
            log.latency_ms = (time.time() - start_time) * 1000
            log.success = True
            consumption_tracker.add_log(log)
            
            # Extraer lista de preguntas
            if isinstance(result, dict) and "questions" in result:
                return result["questions"]
            elif isinstance(result, list):
                return result
            else:
                return []
                
        except Exception as e:
            log.latency_ms = (time.time() - start_time) * 1000
            log.success = False
            log.error = str(e)
            consumption_tracker.add_log(log)
            
            logger.error(f"Error generating questions: {e}")
            raise
    
    async def chat(
        self,
        message: str,
        context: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Chat simple con Gemini via Vertex AI.
        
        Args:
            message: Mensaje del usuario
            context: Contexto adicional (opcional)
            temperature: Temperatura para generación
            
        Returns:
            Respuesta del modelo
        """
        start_time = time.time()
        log = APIConsumptionLog(
            timestamp=datetime.now(),
            model=self.model_id,
            operation="chat",
        )
        
        try:
            prompt = message
            if context:
                prompt = f"Contexto:\n{context}\n\nPregunta: {message}"
            
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=2048,
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
            )
            
            input_tokens, output_tokens, thinking_tokens = self._extract_token_counts(response)
            log.input_tokens = input_tokens
            log.output_tokens = output_tokens
            log.thinking_tokens = thinking_tokens
            log.total_tokens = input_tokens + output_tokens + thinking_tokens
            
            log.latency_ms = (time.time() - start_time) * 1000
            log.success = True
            consumption_tracker.add_log(log)
            
            return response.text
            
        except Exception as e:
            log.latency_ms = (time.time() - start_time) * 1000
            log.success = False
            log.error = str(e)
            consumption_tracker.add_log(log)
            
            logger.error(f"Error in chat: {e}")
            raise


# Singleton instance
_gemini_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    """Get or create Gemini client singleton."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


def get_consumption_summary() -> dict:
    """Obtiene resumen de consumo de API."""
    return consumption_tracker.get_summary()
