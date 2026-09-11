/**
 * ConversationContainer Component
 * Main container managing the entire conversation flow
 */

import React, { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { ConversationStarter } from './ConversationStarter';
import { ConversationTurn } from './ConversationTurn';
import { SectionProgress } from './SectionProgress';
import { HistoryPanel } from './HistoryPanel';
import {
  useCreateSession,
  useSessionState,
  useSubmitResponse,
  useConversationHistory,
} from '../hooks/useConversation';
import type { SessionMode, ApiError } from '../types/conversation';
import './ConversationContainer.css';

export const ConversationContainer: React.FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // API Hooks
  const createSessionMutation = useCreateSession();
  const sessionQuery = useSessionState(sessionId);
  const submitResponseMutation = useSubmitResponse();
  const historyQuery = useConversationHistory(sessionId);

  // Handle session creation
  const handleStartConversation = async (patientId: string, mode: SessionMode) => {
    setErrorMessage(null);
    try {
      const result = await createSessionMutation.mutateAsync({
        patient_id: patientId,
        mode,
        disclaimer_acknowledged: true,
      });
      setSessionId(result.session_id);
    } catch (error) {
      const apiError = error as ApiError;
      setErrorMessage(apiError.error || 'Failed to start conversation');
    }
  };

  // Handle user response submission
  const handleSubmitResponse = async (text: string) => {
    if (!sessionId) return;
    setErrorMessage(null);
    try {
      await submitResponseMutation.mutateAsync({
        sessionId,
        text,
      });
    } catch (error) {
      const apiError = error as ApiError;
      setErrorMessage(apiError.error || 'Failed to process response');
    }
  };

  // Handle errors from queries
  useEffect(() => {
    if (sessionQuery.error) {
      const error = sessionQuery.error as ApiError;
      setErrorMessage(error.error || 'Failed to load session');
    }
  }, [sessionQuery.error]);

  useEffect(() => {
    if (historyQuery.error) {
      const error = historyQuery.error as ApiError;
      setErrorMessage(error.error || 'Failed to load history');
    }
  }, [historyQuery.error]);

  // Render conversation starter if no session
  if (!sessionId) {
    return (
      <div className="conversation-container starter-mode">
        <ConversationStarter
          onStartConversation={handleStartConversation}
          isLoading={createSessionMutation.isPending}
          error={errorMessage}
        />
      </div>
    );
  }

  // Render conversation view if session exists
  const sessionData = sessionQuery.data;
  const historyData = historyQuery.data;
  const lastResponse = historyData?.[historyData.length - 1]?.content || undefined;

  return (
    <div className="conversation-container active-session">
      <div className="conversation-layout">
        {/* Main Conversation Area */}
        <div className="main-area">
          {/* Header */}
          <div className="session-header">
            <div className="header-content">
              <h1>🏥 Clinical Interview</h1>
              <p>Session ID: <code>{sessionId}</code></p>
              {sessionData && (
                <p>
                  Status:{' '}
                  <span className="status-badge" data-status={sessionData.lifecycle_status}>
                    {sessionData.lifecycle_status}
                  </span>
                </p>
              )}
            </div>
            <button
              className="reset-button"
              onClick={() => {
                setSessionId(null);
                queryClient.clear();
              }}
              title="Start a new conversation"
            >
              ↻ New Session
            </button>
          </div>

          {/* Section Progress */}
          {sessionData && (
            <SectionProgress
              currentSection={sessionData.current_section}
              lifecycleStatus={sessionData.lifecycle_status}
            />
          )}

          {/* Conversation Turn */}
          {sessionData ? (
            <ConversationTurn
              currentQuestion={sessionData.latest_question}
              onSubmit={handleSubmitResponse}
              isLoading={submitResponseMutation.isPending || sessionQuery.isRefetching}
              error={errorMessage}
              lastResponse={lastResponse}
              currentSection={sessionData.current_section}
            />
          ) : (
            <div className="loading-state">
              <div className="spinner" />
              <p>Loading session...</p>
            </div>
          )}

          {/* Safety Alerts */}
          {sessionData?.safety.flagged && (
            <div className="safety-alert">
              <h3>⚠ Safety Alert</h3>
              <p>
                A concerning symptom or finding has been detected. 
                Please consult with a healthcare provider immediately.
              </p>
              {sessionData.safety.alerts && (
                <details>
                  <summary>Details</summary>
                  <pre>{JSON.stringify(sessionData.safety.alerts, null, 2)}</pre>
                </details>
              )}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <aside className="sidebar">
          <HistoryPanel
            turns={historyData}
            isLoading={historyQuery.isLoading}
            error={historyQuery.error as Error | null}
          />
        </aside>
      </div>
    </div>
  );
};

export default ConversationContainer;
