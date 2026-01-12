"""API routes module."""
from .rfp import router as rfp_router
from .dashboard import router as dashboard_router
from .auth import router as auth_router

__all__ = ["rfp_router", "dashboard_router", "auth_router"]
