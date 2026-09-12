/**
 * DocumentViewer Component
 * Display extracted text and entities from a document
 */

import React from 'react';
import { useDocument, useExtractedEntities } from '../hooks/useDocument';
import type { DocumentResponse, ExtractedEntity, EntityType } from '../types/document';
import './DocumentViewer.css';

interface DocumentViewerProps {
  sessionId: string | null;
  documentId?: string;
  document: DocumentResponse | null;
  onClose?: () => void;
}

const getEntityIcon = (entityType: EntityType): string => {
  switch (entityType) {
    case 'LAB_RESULT':
      return '🧪';
    case 'VITAL_SIGN':
      return '💓';
    case 'MEDICATION':
      return '💊';
    case 'DIAGNOSIS':
      return '🏥';
    case 'ALLERGY':
      return '⚠';
    case 'IMAGING_FINDING':
      return '📸';
    case 'PROCEDURE':
      return '🔬';
    default:
      return '📌';
  }
};

const getEntityColor = (entityType: EntityType): string => {
  switch (entityType) {
    case 'LAB_RESULT':
      return 'lab-result';
    case 'VITAL_SIGN':
      return 'vital-sign';
    case 'MEDICATION':
      return 'medication';
    case 'DIAGNOSIS':
      return 'diagnosis';
    case 'ALLERGY':
      return 'allergy';
    default:
      return 'other';
  }
};

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
  sessionId,
  document,
  onClose,
}) => {
  const documentQuery = useDocument(sessionId, document?.document_id || null);
  const entitiesQuery = useExtractedEntities(sessionId);

  if (!document) {
    return (
      <div className="document-viewer empty">
        <p>Select a document to view details</p>
      </div>
    );
  }

  const currentDocument = documentQuery.data || document;
  const allEntities = entitiesQuery.data?.entities || [];
  const documentEntities = allEntities.filter(
    (e) => e.document_id === document.document_id
  );
  const abnormalEntities = documentEntities.filter((e) => e.is_abnormal);

  return (
    <div className="document-viewer">
      <div className="viewer-header">
        <div className="header-content">
          <h3>📄 Document Details</h3>
          <p className="document-name">{currentDocument.filename}</p>
        </div>
        {onClose && (
          <button className="close-button" onClick={onClose}>
            ✕
          </button>
        )}
      </div>

      {/* Document Info */}
      <div className="document-info">
        <div className="info-row">
          <span className="label">File Type:</span>
          <span className="value">
            {currentDocument.mime_type.split('/')[1]?.toUpperCase() || 'Unknown'}
          </span>
        </div>
        <div className="info-row">
          <span className="label">Status:</span>
          <span className={`status-badge status-${currentDocument.processing_status}`}>
            {currentDocument.processing_status === 'EXTRACTED'
              ? '✓ Ready'
              : currentDocument.processing_status === 'PENDING'
              ? '⏳ Processing'
              : '✕ Failed'}
          </span>
        </div>
        <div className="info-row">
          <span className="label">Uploaded:</span>
          <span className="value">
            {new Date(currentDocument.created_at).toLocaleString()}
          </span>
        </div>
      </div>

      {/* Extracted Entities */}
      <div className="entities-section">
        <div className="section-header">
          <h4>🔍 Extracted Data</h4>
          {abnormalEntities.length > 0 && (
            <span className="abnormal-badge">
              {abnormalEntities.length} abnormal
            </span>
          )}
        </div>

        {documentEntities.length === 0 ? (
          <p className="no-data">No data extracted from this document</p>
        ) : (
          <div className="entities-grid">
            {documentEntities.map((entity) => (
              <div
                key={entity.entity_id}
                className={`entity-card ${getEntityColor(entity.entity_type)} ${
                  entity.is_abnormal ? 'abnormal' : ''
                }`}
              >
                <div className="entity-header">
                  <span className="entity-icon">
                    {getEntityIcon(entity.entity_type)}
                  </span>
                  <span className="entity-type">{entity.entity_type}</span>
                </div>

                <div className="entity-name">{entity.entity_name}</div>

                <div className="entity-value">
                  <span className="value">{entity.value}</span>
                  {entity.numeric_value !== undefined && (
                    <span className="numeric">({entity.numeric_value})</span>
                  )}
                </div>

                {entity.reference_range && (
                  <div className="entity-range">
                    <span className="label">Normal Range:</span>
                    <span className="range">{entity.reference_range}</span>
                  </div>
                )}

                {entity.is_abnormal && (
                  <div className="abnormal-indicator">
                    <span className="icon">⚠</span>
                    <span className="text">Abnormal</span>
                    {entity.severity && (
                      <span className="severity">{entity.severity}</span>
                    )}
                  </div>
                )}

                <div className="entity-footer">
                  <span className="confidence">
                    Confidence: {(entity.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Raw Text */}
      {currentDocument.raw_text && (
        <div className="text-section">
          <h4>📝 Raw Text</h4>
          <div className="text-content">
            <p>{currentDocument.raw_text}</p>
          </div>
        </div>
      )}

      {/* Loading & Error States */}
      {documentQuery.isLoading && (
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading document details...</p>
        </div>
      )}

      {documentQuery.error && (
        <div className="error-state">
          <p className="error-message">⚠ Failed to load document</p>
          <p className="error-details">
            {documentQuery.error.error}
          </p>
        </div>
      )}
    </div>
  );
};

export default DocumentViewer;
