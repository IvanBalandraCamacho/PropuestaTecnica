/**
 * Tipos para la aplicación RFP Analyzer
 */

// ============ USER & AUTH ============

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: User;
}

// ============ RFP ============

export type RFPStatus = 'pending' | 'analyzing' | 'analyzed' | 'go' | 'no_go' | 'error';

export type RFPCategory = 
  | 'mantencion_aplicaciones'
  | 'desarrollo_software'
  | 'analitica'
  | 'ia_chatbot'
  | 'ia_documentos'
  | 'ia_video'
  | 'otro';

export type Recommendation = 'strong_go' | 'go' | 'conditional_go' | 'no_go' | 'strong_no_go';

export interface RFPSummary {
  id: string;
  file_name: string;
  status: RFPStatus;
  client_name: string | null;
  country: string | null;
  category: RFPCategory | null;
  summary: string | null;
  budget_min: number | null;
  budget_max: number | null;
  currency: string;
  proposal_deadline: string | null;
  recommendation: Recommendation | null;
  decision: 'go' | 'no_go' | null;
  created_at: string;
  analyzed_at: string | null;
}

export interface RFPQuestion {
  id: string;
  question: string;
  category: string | null;
  priority: 'high' | 'medium' | 'low' | null;
  context: string | null;
  why_important: string | null;
  is_answered: boolean;
  answer: string | null;
  answered_at: string | null;
  created_at: string;
}

export interface RFPDetail extends RFPSummary {
  file_gcs_path: string;
  file_size_bytes: number | null;
  extracted_data: ExtractedRFPData | null;
  questions_deadline: string | null;
  project_duration: string | null;
  confidence_score: number | null;
  decision_reason: string | null;
  decided_at: string | null;
  updated_at: string;
  questions: RFPQuestion[];
}

export interface ExtractedRFPData {
  client_name: string | null;
  country: string | null;
  summary: string | null;
  category: string | null;
  budget: {
    amount_min: number | null;
    amount_max: number | null;
    currency: string;
    notes: string | null;
  } | null;
  project_duration: string | null;
  questions_deadline: string | null;
  proposal_deadline: string | null;
  tech_stack: string[];
  team_proposal: {
    suggested: boolean;
    details: string | null;
  } | null;
  experience_required: {
    required: boolean;
    details: string | null;
    is_mandatory: boolean;
  } | null;
  sla: Array<{
    description: string;
    metric: string | null;
    is_aggressive: boolean;
  }>;
  penalties: Array<{
    description: string;
    amount: string | null;
    is_high: boolean;
  }>;
  risks: Array<{
    category: string;
    description: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
  }>;
  recommendation: Recommendation | null;
  recommendation_reasons: string[];
  confidence_score: number | null;
}

// ============ DASHBOARD ============

export interface DashboardStats {
  total_rfps: number;
  go_count: number;
  no_go_count: number;
  pending_count: number;
  analyzing_count: number;
  go_rate: number;
}

export interface RFPListResponse {
  items: RFPSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============ API ============

export interface RFPDecision {
  decision: 'go' | 'no_go';
  reason?: string;
}

export interface UploadResponse {
  id: string;
  file_name: string;
  status: RFPStatus;
  message: string;
}
