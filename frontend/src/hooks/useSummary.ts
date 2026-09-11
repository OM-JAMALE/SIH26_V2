/**
 * React Query hooks for Summary API
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type {
  SummaryResponse,
  GenerateSummaryRequest,
  SummaryReview,
} from '../types/summary';

interface ApiError {
  error: string;
  status?: number;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * Generate a clinical summary from conversation + documents
 */
export function useGenerateSummary() {
  return useMutation<SummaryResponse, ApiError, { sessionId: string; data: GenerateSummaryRequest }>({
    mutationFn: async ({ sessionId, data }) => {
      const response = await fetch(`${API_BASE}/sessions/${sessionId}/summaries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const error = await response.json();
        throw error;
      }

      return response.json();
    },
  });
}

/**
 * Get a generated summary
 */
export function useSummary(sessionId: string | null, summaryId: string | null) {
  return useQuery<SummaryResponse, ApiError>({
    queryKey: ['summary', sessionId, summaryId],
    queryFn: async () => {
      if (!sessionId || !summaryId) throw new Error('Session ID and Summary ID required');

      const response = await fetch(`${API_BASE}/sessions/${sessionId}/summaries/${summaryId}`);

      if (!response.ok) {
        const error = await response.json();
        throw error;
      }

      return response.json();
    },
    enabled: !!sessionId && !!summaryId,
  });
}

/**
 * Submit physician review
 */
export function useSubmitReview() {
  const queryClient = useQueryClient();

  return useMutation<
    SummaryReview,
    ApiError,
    {
      sessionId: string;
      summaryId: string;
      status: 'APPROVED' | 'REJECTED' | 'EDITED';
      notes?: string;
      editedSummary?: string;
    }
  >({
    mutationFn: async ({ sessionId, summaryId, status, notes, editedSummary }) => {
      const response = await fetch(
        `${API_BASE}/sessions/${sessionId}/summaries/${summaryId}/review`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            status,
            review_notes: notes,
            edited_summary: editedSummary,
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw error;
      }

      return response.json();
    },
    onSuccess: (_, { sessionId, summaryId }) => {
      queryClient.invalidateQueries({ queryKey: ['summary', sessionId, summaryId] });
    },
  });
}

/**
 * Export summary as PDF or JSON
 */
export function useExportSummary() {
  return useMutation<Blob, ApiError, { sessionId: string; summaryId: string; format: 'pdf' | 'json' }>({
    mutationFn: async ({ sessionId, summaryId, format }) => {
      const response = await fetch(
        `${API_BASE}/sessions/${sessionId}/summaries/${summaryId}/export?format=${format}`,
        { method: 'GET' }
      );

      if (!response.ok) {
        const error = await response.json();
        throw error;
      }

      return response.blob();
    },
  });
}
