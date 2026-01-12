"""
Pydantic schemas para RFP Analyzer.
"""
from datetime import datetime, date
from typing import Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


# ============ ENUMS ============

class RFPStatusEnum(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    GO = "go"
    NO_GO = "no_go"
    ERROR = "error"


class RFPCategoryEnum(str, Enum):
    MANTENCION_APLICACIONES = "mantencion_aplicaciones"
    DESARROLLO_SOFTWARE = "desarrollo_software"
    ANALITICA = "analitica"
    IA_CHATBOT = "ia_chatbot"
    IA_DOCUMENTOS = "ia_documentos"
    IA_VIDEO = "ia_video"
    OTRO = "otro"


class RecommendationEnum(str, Enum):
    STRONG_GO = "strong_go"
    GO = "go"
    CONDITIONAL_GO = "conditional_go"
    NO_GO = "no_go"
    STRONG_NO_GO = "strong_no_go"


class QuestionCategoryEnum(str, Enum):
    SCOPE = "scope"
    TECHNICAL = "technical"
    COMMERCIAL = "commercial"
    TIMELINE = "timeline"
    TEAM = "team"
    SLA = "sla"
    LEGAL = "legal"


class QuestionPriorityEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============ RFP SCHEMAS ============

class RFPBase(BaseModel):
    """Base schema for RFP."""
    file_name: str


class RFPCreate(RFPBase):
    """Schema for creating an RFP (upload)."""
    pass


class RFPDecision(BaseModel):
    """Schema for GO/NO GO decision."""
    decision: str = Field(..., pattern="^(go|no_go)$", description="Decision: 'go' or 'no_go'")
    reason: str | None = Field(None, description="Reason for the decision")


class RFPQuestion(BaseModel):
    """Schema for a question."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    question: str
    category: str | None = None
    priority: str | None = None
    context: str | None = None
    why_important: str | None = None
    is_answered: bool = False
    answer: str | None = None
    answered_at: datetime | None = None
    created_at: datetime


class RFPSummary(BaseModel):
    """Schema for RFP in list/table view."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    file_name: str
    status: RFPStatusEnum
    client_name: str | None = None
    country: str | None = None
    category: str | None = None
    summary: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    currency: str = "USD"
    proposal_deadline: date | None = None
    recommendation: str | None = None
    decision: str | None = None
    created_at: datetime
    analyzed_at: datetime | None = None


class RFPDetail(RFPSummary):
    """Schema for RFP detail view with all extracted data."""
    model_config = ConfigDict(from_attributes=True)
    
    file_gcs_path: str
    file_size_bytes: int | None = None
    extracted_data: dict[str, Any] | None = None
    questions_deadline: date | None = None
    project_duration: str | None = None
    confidence_score: int | None = None
    decision_reason: str | None = None
    decided_at: datetime | None = None
    updated_at: datetime
    questions: list[RFPQuestion] = []


# ============ DASHBOARD SCHEMAS ============

class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    total_rfps: int = 0
    go_count: int = 0
    no_go_count: int = 0
    pending_count: int = 0
    analyzing_count: int = 0
    go_rate: float = 0.0  # Percentage


class RFPListResponse(BaseModel):
    """Schema for paginated RFP list."""
    items: list[RFPSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============ ANALYSIS SCHEMAS ============

class BudgetInfo(BaseModel):
    """Budget information extracted from RFP."""
    amount_min: float | None = None
    amount_max: float | None = None
    currency: str = "USD"
    notes: str | None = None


class TeamProposal(BaseModel):
    """Team proposal from client."""
    suggested: bool = False
    details: str | None = None


class ExperienceRequired(BaseModel):
    """Experience requirements."""
    required: bool = False
    details: str | None = None
    is_mandatory: bool = False


class SLAItem(BaseModel):
    """Single SLA item."""
    description: str
    metric: str | None = None
    is_aggressive: bool = False


class PenaltyItem(BaseModel):
    """Single penalty item."""
    description: str
    amount: str | None = None
    is_high: bool = False


class RiskItem(BaseModel):
    """Single risk item."""
    category: str
    description: str
    severity: str = "medium"  # low, medium, high, critical


class ExtractedRFPData(BaseModel):
    """Complete extracted data from RFP analysis."""
    # Basic info
    client_name: str | None = None
    country: str | None = None
    summary: str | None = None
    category: str | None = None
    
    # Commercial
    budget: BudgetInfo | None = None
    project_duration: str | None = None
    questions_deadline: str | None = None  # ISO date string
    proposal_deadline: str | None = None   # ISO date string
    
    # Technical
    tech_stack: list[str] = []
    team_proposal: TeamProposal | None = None
    
    # Requirements
    experience_required: ExperienceRequired | None = None
    
    # SLA and Penalties
    sla: list[SLAItem] = []
    penalties: list[PenaltyItem] = []
    
    # Analysis
    risks: list[RiskItem] = []
    recommendation: str | None = None
    recommendation_reasons: list[str] = []
    confidence_score: int | None = None


# ============ UPLOAD RESPONSE ============

class UploadResponse(BaseModel):
    """Response after uploading an RFP."""
    id: UUID
    file_name: str
    status: RFPStatusEnum
    message: str = "RFP uploaded successfully. Analysis in progress."
