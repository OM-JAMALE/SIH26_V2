/**
 * API Types for Document Module
 */

export type DocumentType = 
  | 'LAB_REPORT'
  | 'IMAGING_REPORT'
  | 'PRESCRIPTION'
  | 'DISCHARGE_SUMMARY'
  | 'CLINICAL_NOTE'
  | 'UNKNOWN';

export type ProcessingStatus = 'PENDING' | 'EXTRACTED' | 'FAILED';

export type EntityType = 
  | 'LAB_RESULT'
  | 'VITAL_SIGN'
  | 'MEDICATION'
  | 'DIAGNOSIS'
  | 'PROCEDURE'
  | 'ALLERGY'
  | 'IMAGING_FINDING'
  | 'OTHER';

export interface DocumentEntity {
  entity_type: EntityType;
  entity_name: string;
  value: string;
  numeric_value?: number;
  unit?: string;
  reference_range?: string;
  is_abnormal: boolean;
  confidence_score: number;
  metadata_json?: Record<string, any>;
}

export interface ExtractedEntity {
  entity_id: string;
  entity_type: EntityType;
  entity_name: string;
  value: string;
  numeric_value?: number;
  unit?: string;
  reference_range?: string;
  is_abnormal: boolean;
  confidence_score: number;
  severity?: string;
  document_id: string;
}

export interface ApiError {
  error: string;
  code?: string;
  status?: number;
  request_id?: string;
  details?: Record<string, any>;
}

export interface DocumentResponse {
  document_id: string;
  session_id: string;
  filename: string;
  mime_type: string;
  file_size: number;
  processing_status: ProcessingStatus;
  extracted_entities?: DocumentEntity[];
  raw_text?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  total: number;
  documents: DocumentResponse[];
}

export interface EntityListResponse {
  total: number;
  entities: ExtractedEntity[];
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface DocumentUploadError {
  field: string;
  message: string;
  code: string;
}
