/// <reference types="vite/client" />
import { HealthResponse } from '../types';

// Uses Vite proxy in dev (vite.config.ts server.proxy) and env var in production
const API_BASE = import.meta.env.VITE_API_URL ?? '/api/v1';

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'X-Request-ID': crypto.randomUUID(),
    ...(options.headers as Record<string, string> || {}),
  };
  if (!isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${url}`, { ...options, headers });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    let message = `API request failed with status ${res.status}`;
    if (typeof errorData.detail === 'string') {
      message = errorData.detail;
    } else if (errorData.detail?.error) {
      message = errorData.detail.error;
    } else if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
      message = errorData.detail[0]?.msg || JSON.stringify(errorData.detail);
    } else if (errorData.error?.message) {
      message = errorData.error.message;
    }
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

// Module B: Medical Document Digitization
export interface ExtractedEntityData {
  id: string;
  session_id: string;
  document_id?: string;
  entity_type: 'LAB_RESULT' | 'MEDICATION' | 'DIAGNOSIS' | 'VITAL' | 'SYMPTOM' | string;
  entity_name: string;
  value: string;
  numeric_value?: number;
  unit?: string;
  reference_range?: string;
  is_abnormal: boolean;
  confidence_score: number;
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface DocumentData {
  id: string;
  session_id: string;
  filename: string;
  mime_type: string;
  file_size: number;
  processing_status: 'PENDING' | 'EXTRACTED' | 'FAILED' | string;
  raw_text?: string;
  created_at: string;
  extracted_entities: ExtractedEntityData[];
}

export interface DocumentListResponseData {
  documents: DocumentData[];
  total: number;
}

export interface EntityListResponseData {
  entities: ExtractedEntityData[];
  total: number;
  abnormal_count: number;
}

export interface DocumentDeleteResponseData {
  success: boolean;
  message: string;
  document_id: string;
}

export async function uploadDocument(sessionId: string, file: File): Promise<DocumentData> {
  const formData = new FormData();
  formData.append('file', file);

  return request<DocumentData>(`/sessions/${sessionId}/documents`, {
    method: 'POST',
    body: formData,
  });
}

export async function getSessionDocuments(sessionId: string): Promise<DocumentData[]> {
  const res = await request<DocumentListResponseData>(`/sessions/${sessionId}/documents`);
  return res.documents || [];
}

export async function getSessionEntities(
  sessionId: string,
  abnormalOnly: boolean = false
): Promise<EntityListResponseData> {
  const query = abnormalOnly ? '?abnormal_only=true' : '';
  return request<EntityListResponseData>(`/sessions/${sessionId}/entities${query}`);
}

export async function deleteDocument(
  sessionId: string,
  documentId: string
): Promise<DocumentDeleteResponseData> {
  return request<DocumentDeleteResponseData>(`/sessions/${sessionId}/documents/${documentId}`, {
    method: 'DELETE',
  });
}

// Patient & Doctor Portal APIs
export interface PatientData {
  id: string;
  national_health_id?: string;
  first_name: string;
  last_name: string;
  dob: string;
  gender: string;
  contact_number?: string;
  created_at?: string;
}

export async function createOrGetPatient(patient: Partial<PatientData>): Promise<PatientData> {
  return request<PatientData>('/patients', {
    method: 'POST',
    body: JSON.stringify(patient),
  });
}

export async function fetchPatientDetails(patientId: string): Promise<PatientData> {
  return request<PatientData>(`/patients/${patientId}`);
}

export async function fetchPatientSessions(patientId: string): Promise<any[]> {
  return request<any[]>(`/patients/${patientId}/sessions`);
}

export async function searchPatientsForDoctor(query: string): Promise<any[]> {
  return request<any[]>(`/doctors/patients/search?query=${encodeURIComponent(query)}`);
}

export async function fetchDoctorFullHistory(patientId: string): Promise<any> {
  return request<any>(`/doctors/patients/${patientId}/full-history`);
}
