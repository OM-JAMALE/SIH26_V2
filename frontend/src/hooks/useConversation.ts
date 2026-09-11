/**
 * React Query hooks for Conversation API
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type {
  SessionStateResponse,
  ProcessResponseResult,
  CreateSessionRequest,
  SubmitResponseRequest,
  ConversationTurn,
  ApiError,
} from '../types/conversation';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * Create a new conversation session
 */
export function useCreateSession() {
  return useMutation<SessionStateResponse, ApiError, CreateSessionRequest>({
    mutationFn: async (data) => {
      const response = await fetch(`${API_BASE}/sessions/`, {
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
 * Get current session state
 */
export function useSessionState(sessionId: string | null) {
  return useQuery<SessionStateResponse, ApiError>({
    queryKey: ['session', sessionId],
    queryFn: async () => {
      if (!sessionId) throw new Error('Session ID required');

      const response = await fetch(`${API_BASE}/sessions/${sessionId}`);

      if (!response.ok) {
        const error = await response.json();
        throw error;
      }

      return response.json();
    },
    enabled: !!sessionId,
    refetchInterval: 2000, // Poll every 2 seconds for real-time updates
  });
}

/**
 * Submit user response to conversation
 */
export function useSubmitResponse() {
  const queryClient = useQueryClient();

  return useMutation<ProcessResponseResult, ApiError, { sessionId: string; text: string }>({
    mutationFn: async ({ sessionId, text }) => {
      const response = await fetch(`${API_BASE}/sessions/${sessionId}/responses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw error;
      }

      return response.json();
    },
    onSuccess: (_, variables) => {
      // Invalidate session state to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['session', variables.sessionId] });
      // Invalidate history
      queryClient.invalidateQueries({ queryKey: ['conversation-history', variables.sessionId] });
    },
  });
}

/**
 * Get conversation history (all turns)
 */
export function useConversationHistory(sessionId: string | null) {
  return useQuery<ConversationTurn[], ApiError>({
    queryKey: ['conversation-history', sessionId],
    queryFn: async () => {
      if (!sessionId) throw new Error('Session ID required');

      const response = await fetch(`${API_BASE}/sessions/${sessionId}/conversation`);

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
 * Acknowledge disclaimer
 */
export function useAcknowledgeDisclaimer() {
  const queryClient = useQueryClient();

  return useMutation<SessionStateResponse, ApiError, { sessionId: string }>({
    mutationFn: async ({ sessionId }) => {
      const response = await fetch(`${API_BASE}/sessions/${sessionId}/disclaimer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ acknowledged: true }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw error;
      }

      return response.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['session', variables.sessionId] });
    },
  });
}
