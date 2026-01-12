"""GCP clients module."""
# Usar cliente con API Key en lugar de Vertex AI
from .gemini_client import GeminiClient, get_gemini_client, get_consumption_summary
from .storage import StorageClient, get_storage_client

__all__ = [
    "GeminiClient",
    "get_gemini_client",
    "get_consumption_summary",
    "StorageClient", 
    "get_storage_client",
]
