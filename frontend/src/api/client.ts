/// <reference types="vite/client" />
import { HealthResponse } from '../types';

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api/v1';

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Request-ID': crypto.randomUUID(),
    ...(options.headers || {}),
  };

  const res = await fetch(`${API_BASE}${url}`, { ...options, headers });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail?.error || errorData.error?.message || `API request failed with status ${res.status}`;
    const error = new Error(message) as any;
    error.detail = errorData.detail || errorData;
    throw error;
  }
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

export interface SessionStateData {
  session_id: string;
  patient_id: string;
  lifecycle_status: 'CREATED' | 'IN_PROGRESS' | 'SAFETY_ESCALATED' | 'COMPLETED';
  mode: 'MODERN' | 'AYUSH';
  disclaimer_acknowledged: boolean;
  disclaimer_acknowledged_at?: string;
  current_section: string;
  socrates_state?: string;
  latest_question: string;
  structured_history: any;
  safety: {
    flagged: boolean;
    rule_id?: string;
    severity?: string;
    emergency_message?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface SubmitResponseResultData {
  session_id: string;
  lifecycle_status: 'CREATED' | 'IN_PROGRESS' | 'SAFETY_ESCALATED' | 'COMPLETED';
  current_section: string;
  socrates_state?: string;
  next_question: string;
  structured_updates: any;
  safety: {
    flagged: boolean;
    rule_id?: string;
    severity?: string;
    emergency_message?: string;
  };
}

export interface ConversationTurnData {
  id: string;
  session_id: string;
  turn_index: number;
  speaker: 'PATIENT' | 'SYSTEM';
  content: string;
  extracted_data: any;
  safety_alerts: any;
  section: string;
  created_at: string;
}

export async function createSession(
  patientId: string,
  mode: 'MODERN' | 'AYUSH' = 'MODERN',
  disclaimerAcknowledged: boolean = false
): Promise<SessionStateData> {
  return request<SessionStateData>('/sessions', {
    method: 'POST',
    body: JSON.stringify({
      patient_id: patientId,
      mode,
      disclaimer_acknowledged: disclaimerAcknowledged,
    }),
  });
}

export async function acknowledgeDisclaimer(sessionId: string): Promise<SessionStateData> {
  return request<SessionStateData>(`/sessions/${sessionId}/disclaimer`, {
    method: 'POST',
    body: JSON.stringify({ disclaimer_acknowledged: true }),
  });
}

export async function getSessionState(sessionId: string): Promise<SessionStateData> {
  return request<SessionStateData>(`/sessions/${sessionId}`);
}

export async function submitPatientResponse(sessionId: string, text: string): Promise<SubmitResponseResultData> {
  return request<SubmitResponseResultData>(`/sessions/${sessionId}/responses`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}

export async function getConversationHistory(sessionId: string): Promise<ConversationTurnData[]> {
  return request<ConversationTurnData[]>(`/sessions/${sessionId}/conversation`);
}

// Module C Summary Methods
export interface SummaryData {
  id: string;
  session_id: string;
  version: number;
  workflow_status: string;
  status: string;
  structured_summary: any;
  physician_edited_summary: any;
  active_summary: any;
  llm_model: string;
  prompt_version: string;
  generation_error?: string;
  physician_notes?: string;
  accepted_at?: string;
  accepted_by?: string;
  rejected_at?: string;
  rejected_reason?: string;
  created_at: string;
  updated_at: string;
}

export async function generateSummary(sessionId: string): Promise<SummaryData> {
  return request<SummaryData>(`/sessions/${sessionId}/summary`, {
    method: 'POST',
  });
}

export async function getSummary(sessionId: string): Promise<SummaryData> {
  return request<SummaryData>(`/sessions/${sessionId}/summary`);
}

export async function editSummary(sessionId: string, editedSummary: Record<string, any>): Promise<SummaryData> {
  return request<SummaryData>(`/sessions/${sessionId}/summary`, {
    method: 'PATCH',
    body: JSON.stringify({ edited_summary: editedSummary }),
  });
}

export async function acceptSummary(sessionId: string, physicianNotes?: string): Promise<SummaryData> {
  return request<SummaryData>(`/sessions/${sessionId}/summary/accept`, {
    method: 'POST',
    body: JSON.stringify({ physician_notes: physicianNotes, physician_id: 'dr_physician_1' }),
  });
}

export async function rejectSummary(sessionId: string, reason: string): Promise<SummaryData> {
  return request<SummaryData>(`/sessions/${sessionId}/summary/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason, physician_id: 'dr_physician_1' }),
  });
}
