/**
 * DocumentContainer Component
 * Main container for document upload, list, and viewer
 */

import React, { useState } from 'react';
import { DocumentUpload } from './DocumentUpload';
import { DocumentList } from './DocumentList';
import { DocumentViewer } from './DocumentViewer';
import type { DocumentResponse } from '../types/document';
import './DocumentContainer.css';

interface DocumentContainerProps {
  sessionId: string | null;
}

export const DocumentContainer: React.FC<DocumentContainerProps> = ({ sessionId }) => {
  const [selectedDocument, setSelectedDocument] = useState<DocumentResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const handleUploadSuccess = (documentId: string) => {
    setUploadSuccess(true);
    setUploadError(null);
    // Clear success message after 3 seconds
    setTimeout(() => setUploadSuccess(false), 3000);
  };

  const handleUploadError = (error: string) => {
    setUploadError(error);
    setUploadSuccess(false);
  };

  if (!sessionId) {
    return (
      <div className="document-container empty-state">
        <p>Start a conversation to upload medical documents</p>
      </div>
    );
  }

  return (
    <div className="document-container">
      <div className="documents-layout">
        <div className="documents-main">
          {/* Success Message */}
          {uploadSuccess && (
            <div className="success-message">
              <span className="icon">✓</span>
              <p>Document uploaded successfully!</p>
            </div>
          )}

          {/* Upload Section */}
          <section className="upload-section">
            <DocumentUpload
              sessionId={sessionId}
              onUploadSuccess={handleUploadSuccess}
              onError={handleUploadError}
            />
          </section>

          {/* Document List */}
          <section className="list-section">
            <DocumentList
              sessionId={sessionId}
              onDocumentSelect={setSelectedDocument}
              onDeleteSuccess={() => setSelectedDocument(null)}
            />
          </section>
        </div>

        {/* Sidebar: Document Viewer */}
        <aside className="documents-sidebar">
          <DocumentViewer
            sessionId={sessionId}
            document={selectedDocument}
            onClose={() => setSelectedDocument(null)}
          />
        </aside>
      </div>
    </div>
  );
};

export default DocumentContainer;
