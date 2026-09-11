/**
 * DocumentList Component
 * Table of uploaded documents with file info and status
 */

import React, { useState } from 'react';
import { useDocumentList, useDeleteDocument, formatFileSize } from '../hooks/useDocument';
import type { DocumentResponse, ProcessingStatus } from '../types/document';
import './DocumentList.css';

interface DocumentListProps {
  sessionId: string | null;
  onDocumentSelect?: (document: DocumentResponse) => void;
  onDeleteSuccess?: () => void;
}

const getStatusIcon = (status: ProcessingStatus): string => {
  switch (status) {
    case 'PENDING':
      return '⏳';
    case 'EXTRACTED':
      return '✓';
    case 'FAILED':
      return '✕';
    default:
      return '?';
  }
};

const getStatusLabel = (status: ProcessingStatus): string => {
  switch (status) {
    case 'PENDING':
      return 'Processing...';
    case 'EXTRACTED':
      return 'Ready';
    case 'FAILED':
      return 'Failed';
    default:
      return 'Unknown';
  }
};

const getStatusClass = (status: ProcessingStatus): string => {
  return `status-${status.toLowerCase()}`;
};

export const DocumentList: React.FC<DocumentListProps> = ({
  sessionId,
  onDocumentSelect,
  onDeleteSuccess,
}) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const documentsQuery = useDocumentList(sessionId);
  const deleteMutation = useDeleteDocument();

  const handleDelete = async (documentId: string) => {
    if (!sessionId) return;
    if (!window.confirm('Are you sure you want to delete this document?')) return;

    setDeletingId(documentId);
    try {
      await deleteMutation.mutateAsync({ sessionId, documentId });
      onDeleteSuccess?.();
    } catch (error) {
      console.error('Delete failed:', error);
    } finally {
      setDeletingId(null);
    }
  };

  if (documentsQuery.isLoading) {
    return (
      <div className="document-list loading">
        <div className="spinner" />
        <p>Loading documents...</p>
      </div>
    );
  }

  if (documentsQuery.error) {
    return (
      <div className="document-list error">
        <p className="error-message">⚠ Failed to load documents</p>
        <p className="error-details">{documentsQuery.error.error}</p>
      </div>
    );
  }

  const documents = documentsQuery.data?.documents || [];

  return (
    <div className="document-list">
      <div className="list-header">
        <h3>📚 Uploaded Documents</h3>
        <span className="doc-count">{documents.length} file(s)</span>
      </div>

      {documents.length === 0 ? (
        <div className="empty-state">
          <p>No documents uploaded yet</p>
          <p className="hint">Upload a PDF, PNG, or JPEG file above</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="documents-table">
            <thead>
              <tr>
                <th>File Name</th>
                <th>Type</th>
                <th>Size</th>
                <th>Uploaded</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.document_id} className="document-row">
                  <td className="filename-cell">
                    <span className="file-icon">
                      {doc.mime_type.includes('pdf') ? '📕' : '🖼'}
                    </span>
                    <span className="filename">{doc.filename}</span>
                  </td>
                  <td className="type-cell">
                    {doc.mime_type.split('/')[1]?.toUpperCase() || 'Unknown'}
                  </td>
                  <td className="size-cell">
                    {formatFileSize(doc.file_size)}
                  </td>
                  <td className="date-cell">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className={`status-cell ${getStatusClass(doc.processing_status)}`}>
                    <span className="status-icon">
                      {getStatusIcon(doc.processing_status)}
                    </span>
                    <span className="status-label">
                      {getStatusLabel(doc.processing_status)}
                    </span>
                  </td>
                  <td className="actions-cell">
                    {doc.processing_status === 'EXTRACTED' && (
                      <button
                        className="action-button view-button"
                        onClick={() => onDocumentSelect?.(doc)}
                        title="View extracted data"
                      >
                        👁 View
                      </button>
                    )}
                    <button
                      className="action-button delete-button"
                      onClick={() => handleDelete(doc.document_id)}
                      disabled={deletingId === doc.document_id || deleteMutation.isPending}
                      title="Delete document"
                    >
                      {deletingId === doc.document_id ? '...' : '🗑'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default DocumentList;
