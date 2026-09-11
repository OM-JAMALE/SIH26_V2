/**
 * API Types for Summary Module
 */

export type InformationStatus = 'KNOWN' | 'DENIED' | 'NOT_PROVIDED';

export interface ClinicalItem {
  name: string;
  status: InformationStatus;
  details?: string;
  value?: string;
  numeric_value?: number;
  unit?: string;
  reference_range?: string;
}

export interface MedicationItem {
  name: string;
  status: InformationStatus;
  dosage?: string;
  frequency?: string;
  route?: string;
}

export interface LabInvestigation {
  test_name: string;
  status: InformationStatus;
  value?: string;
  numeric_value?: number;
  unit?: string;
  reference_range?: string;
  is_abnormal?: boolean;
}

export interface RedFlagItem {
  flag_name: string;
  description: string;
  source: string;
}

export interface ClinicalSummarySchema {
  session_id: string;
  chief_complaint: ClinicalItem[];
  history_of_present_illness: ClinicalItem[];
  associated_symptoms: ClinicalItem[];
  relevant_positive_findings: ClinicalItem[];
  relevant_negative_findings: ClinicalItem[];
  past_medical_history: ClinicalItem[];
  past_surgical_history: ClinicalItem[];
  medications: MedicationItem[];
  allergies: ClinicalItem[];
  family_history: ClinicalItem[];
  personal_social_history: ClinicalItem[];
  review_of_systems: ClinicalItem[];
  investigations: LabInvestigation[];
  abnormal_findings: ClinicalItem[];
  red_flags: RedFlagItem[];
  information_gaps: string[];
  generated_summary_text: string;
}

export interface GenerateSummaryRequest {
  include_recommendations?: boolean;
  include_abnormalities_only?: boolean;
}

export interface SummaryResponse {
  summary_id: string;
  session_id: string;
  chief_complaint: string;
  generated_summary_text: string;
  key_findings: ClinicalItem[];
  red_flags: RedFlagItem[];
  recommendations?: string[];
  uncertainty_notes?: string[];
  model_version?: string;
  created_at: string;
  updated_at: string;
}

export type ReviewStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'EDITED';

export interface SummaryReview {
  review_id: string;
  summary_id: string;
  status: ReviewStatus;
  reviewer_id?: string;
  review_notes?: string;
  edited_summary?: string;
  created_at: string;
  updated_at: string;
}
