/**
 * DocumentUpload Component
 * Drag-and-drop file upload with progress tracking
 */

import React, { useState, useRef } from 'react';
import { useUploadDocument, validateFile, formatFileSize } from '../hooks/useDocument';
import type { UploadProgress } from '../types/document';
import './DocumentUpload.css';

interface DocumentUploadProps {
  sessionId: string | null;
  onUploadSuccess?: (documentId: string) => void;
  onError?: (error: string) => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  sessionId,
  onUploadSuccess,
  onError,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadDocument();

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = (file: File) => {
    setError(null);

    // Validate file
    const validation = validateFile(file);
    if (!validation.valid) {
      setError(validation.error || 'Invalid file');
      onError?.(validation.error || 'Invalid file');
      return;
    }

    setSelectedFile(file);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !sessionId) return;

    setError(null);
    try {
      const result = await uploadMutation.mutateAsync({
        sessionId,
        file: selectedFile,
        onProgress: setUploadProgress,
      });

      // Reset state
      setSelectedFile(null);
      setUploadProgress(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      onUploadSuccess?.(result.document_id);
    } catch (err: any) {
      const errorMsg = err.error || 'Upload failed';
      setError(errorMsg);
      onError?.(errorMsg);
    }
  };

  const handleCancel = () => {
    setSelectedFile(null);
    setUploadProgress(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const isUploading = uploadMutation.isPending;
  const isDisabled = isUploading || !sessionId;

  return (
    <div className="document-upload">
      <div className="upload-header">
        <h3>📄 Upload Medical Document</h3>
        <p className="upload-hint">
          Supports PDF, PNG, JPEG (Max 25MB)
        </p>
      </div>

      {/* Drag-Drop Zone */}
      <div
        className={`drag-drop-zone ${isDragging ? 'dragging' : ''} ${
          selectedFile ? 'has-file' : ''
        }`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleFileDrop}
      >
        {!selectedFile ? (
          <>
            <div className="drop-icon">📥</div>
            <h4>Drag and drop your file here</h4>
            <p className="or-text">or</p>
            <button
              type="button"
              className="browse-button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isDisabled}
            >
              Browse Files
            </button>
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleInputChange}
              accept=".pdf,.png,.jpg,.jpeg"
              style={{ display: 'none' }}
              disabled={isDisabled}
            />
          </>
        ) : (
          <>
            <div className="file-preview">
              <div className="file-icon">
                {selectedFile.type.includes('pdf') ? '📕' : '🖼'}
              </div>
              <div className="file-info">
                <div className="file-name">{selectedFile.name}</div>
                <div className="file-size">
                  {formatFileSize(selectedFile.size)}
                </div>
              </div>
            </div>

            {uploadProgress && (
              <div className="upload-progress">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${uploadProgress.percentage}%` }}
                  />
                </div>
                <div className="progress-text">
                  {uploadProgress.percentage}% uploaded
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Error Alert */}
      {error && (
        <div className="error-alert">
          <span className="error-icon">⚠</span>
          <p>{error}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="upload-actions">
        {selectedFile && !isUploading && (
          <button
            type="button"
            className="cancel-button"
            onClick={handleCancel}
          >
            Clear
          </button>
        )}
        {selectedFile && (
          <button
            type="button"
            className="upload-button"
            onClick={handleUpload}
            disabled={isUploading || isDisabled}
          >
            {isUploading ? (
              <>
                <span className="spinner" />
                Uploading...
              </>
            ) : (
              <>
                <span className="upload-icon">↑</span>
                Upload Document
              </>
            )}
          </button>
        )}
      </div>

      {/* Info */}
      <div className="upload-info">
        <details>
          <summary>📋 Accepted Formats</summary>
          <ul>
            <li><strong>PDF:</strong> Lab reports, discharge summaries</li>
            <li><strong>PNG:</strong> Scanned documents, screenshots</li>
            <li><strong>JPEG:</strong> Photos of medical records</li>
          </ul>
          <p className="info-note">
            All files are encrypted and processed securely.
          </p>
        </details>
      </div>
    </div>
  );
};

export default DocumentUpload;
