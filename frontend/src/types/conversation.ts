/**
 * API Types for Conversation Module
 */

export type SessionMode = 'MODERN' | 'AYUSH';

export type InterviewSection = 
  | 'IDENTIFICATION'
  | 'CHIEF_COMPLAINT'
  | 'HPI'
  | 'PAST_MEDICAL_HISTORY'
  | 'PAST_SURGICAL_HISTORY'
  | 'MEDICATIONS'
  | 'ALLERGIES'
  | 'FAMILY_HISTORY'
  | 'PERSONAL_HISTORY'
  | 'REVIEW_OF_SYSTEMS'
  | 'COMPLETED';

export type LifecycleStatus = 
  | 'CREATED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'SAFETY_ESCALATED';

export type SpeakerType = 'SYSTEM' | 'PATIENT';

export interface ConversationTurn {
  turn_index: number;
  speaker: SpeakerType;
  content: string;
  extracted_data?: Record<string, any>;
  safety_alerts?: Record<string, any>;
  section: InterviewSection;
  created_at: string;
}

export interface SessionStateResponse {
  session_id: string;
  patient_id: string;
  lifecycle_status: LifecycleStatus;
  mode: SessionMode;
  disclaimer_acknowledged: boolean;
  disclaimer_acknowledged_at?: string;
  current_section: InterviewSection;
  socrates_state?: string;
  latest_question: string;
  structured_history: Record<string, any>;
  safety: {
    flagged: boolean;
    alerts?: Record<string, any>;
  };
  created_at: string;
  updated_at: string;
}

export interface ProcessResponseResult {
  session_id: string;
  lifecycle_status: LifecycleStatus;
  current_section: InterviewSection;
  socrates_state?: string;
  next_question: string;
  structured_updates: Record<string, any>;
  safety: {
    flagged: boolean;
    alerts?: Record<string, any>;
  };
}

export interface CreateSessionRequest {
  patient_id: string;
  mode: SessionMode;
  disclaimer_acknowledged: boolean;
}

export interface SubmitResponseRequest {
  text: string;
}

export interface ApiError {
  error: string;
  code: string;
  status: number;
  request_id?: string;
  details?: Record<string, any>;
}
