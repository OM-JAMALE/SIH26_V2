export type SessionStatus =
  | 'INITIATED'
  | 'IN_CONVERSATION'
  | 'DOCUMENTS_UPLOADED'
  | 'SUMMARY_GENERATED'
  | 'PHYSICIAN_REVIEWED'
  | 'CONSENTED'
  | 'COMPLETED';

export type ClinicalSection =
  | 'CHIEF_COMPLAINT'
  | 'HPI'
  | 'SOCRATES'
  | 'PMH'
  | 'PSH'
  | 'DRUG_HISTORY'
  | 'ALLERGY_HISTORY'
  | 'FAMILY_HISTORY'
  | 'PERSONAL_HISTORY'
  | 'ROS'
  | 'COMPLETED';

export interface Patient {
  id: string;
  national_health_id?: string;
  first_name: string;
  last_name: string;
  dob: string;
  gender: string;
  contact_number?: string;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  patient_id: string;
  status: SessionStatus;
  current_section: ClinicalSection;
  session_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  app_name: string;
  environment: string;
  ai_provider: string;
  timestamp: string;
  services: {
    database: { status: string; error?: string };
    redis: { status: string; error?: string };
  };
}
