/**
 * React Query hooks for Document API
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type {
  DocumentResponse,
  DocumentListResponse,
  EntityListResponse,
  UploadProgress,
  ApiError,
} from '../types/document';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * Upload a document
 */
export function useUploadDocument() {
  return useMutation<
    DocumentResponse,
    ApiError,
    { sessionId: string; file: File; onProgress?: (progress: UploadProgress) => void }
  >({
    mutationFn: async ({ sessionId, file, onProgress }) => {
      const formData = new FormData();
      formData.append('file', file);

      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // Track upload progress
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const percentage = Math.round((event.loaded / event.total) * 100);
            onProgress?.({
              loaded: event.loaded,
              total: event.total,
              percentage,
            });
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(JSON.parse(xhr.responseText));
          }
        });

        xhr.addEventListener('error', () => {
          reject({
            error: 'Network error',
            code: 'NETWORK_ERROR',
            status: 0,
          });
        });

        xhr.open('POST', `${API_BASE}/sessions/${sessionId}/documents`);
        xhr.send(formData);
      });
    },
  });
}

/**
 * Get list of documents for a session
 */
export function useDocumentList(sessionId: string | null) {
  return useQuery<DocumentListResponse, ApiError>({
    queryKey: ['documents', sessionId],
    queryFn: async () => {
      if (!sessionId) throw new Error('Session ID required');

      const response = await fetch(`${API_BASE}/sessions/${sessionId}/documents`);

      if (!response.ok) {
        const error = await response.json();
        throw error;
      }

      return response.json();
    },
    enabled: !!sessionId,
  });
}

/**
 * Get a specific document
 */
export function useDocument(sessionId: string | null, documentId: string | null) {
  return useQuery<DocumentResponse, ApiError>({
    queryKey: ['document', sessionId, documentId],
    queryFn: async () => {
      if (!sessionId || !documentId) throw new Error('Session ID and Document ID required');

      const response = await fetch(`${API_BASE}/sessions/${sessionId}/documents/${documentId}`);

      if (!response.ok) {
        const error = await response.json();
        throw error;
      }

      return response.json();
    },
    enabled: !!sessionId && !!documentId,
  });
}

/**
 * Get extracted entities for a session
 */
export function useExtractedEntities(sessionId: string | null, abnormalOnly: boolean = false) {
  return useQuery<EntityListResponse, ApiError>({
    queryKey: ['entities', sessionId, abnormalOnly],
    queryFn: async () => {
      if (!sessionId) throw new Error('Session ID required');

      const url = new URL(`${API_BASE}/sessions/${sessionId}/entities`);
      if (abnormalOnly) {
        url.searchParams.append('abnormal_only', 'true');
      }

      const response = await fetch(url.toString());

      if (!response.ok) {
        const error = await response.json();
        throw error;
      }

      return response.json();
    },
    enabled: !!sessionId,
  });
}

/**
 * Delete a document
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation<{ success: boolean }, ApiError, { sessionId: string; documentId: string }>({
    mutationFn: async ({ sessionId, documentId }) => {
      const response = await fetch(
        `${API_BASE}/sessions/${sessionId}/documents/${documentId}`,
        { method: 'DELETE' }
      );

      if (!response.ok) {
        const error = await response.json();
        throw error;
      }

      return response.json();
    },
    onSuccess: (_, { sessionId }) => {
      // Invalidate document list
      queryClient.invalidateQueries({ queryKey: ['documents', sessionId] });
      // Invalidate extracted entities
      queryClient.invalidateQueries({ queryKey: ['entities', sessionId] });
    },
  });
}

/**
 * File validation utilities
 */
export const ALLOWED_MIME_TYPES = {
  'application/pdf': '.pdf',
  'image/png': '.png',
  'image/jpeg': '.jpg',
};

export const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB

export function validateFile(file: File): { valid: boolean; error?: string } {
  // Check MIME type
  if (!ALLOWED_MIME_TYPES[file.type as keyof typeof ALLOWED_MIME_TYPES]) {
    return {
      valid: false,
      error: `Invalid file type. Allowed types: PDF, PNG, JPEG`,
    };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    const maxMB = MAX_FILE_SIZE / (1024 * 1024);
    return {
      valid: false,
      error: `File size (${(file.size / (1024 * 1024)).toFixed(1)}MB) exceeds maximum of ${maxMB}MB`,
    };
  }

  return { valid: true };
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}
