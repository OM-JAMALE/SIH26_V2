/**
 * HistoryPanel Component
 * Sidebar showing all past turns in the conversation
 */

import React, { useEffect, useRef } from 'react';
import type { ConversationTurn } from '../types/conversation';
import './HistoryPanel.css';

interface HistoryPanelProps {
  turns: ConversationTurn[] | undefined;
  isLoading: boolean;
  error: Error | null;
}

export const HistoryPanel: React.FC<HistoryPanelProps> = ({
  turns = [],
  isLoading,
  error,
}) => {
  const panelRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new turns are added
  useEffect(() => {
    if (panelRef.current) {
      panelRef.current.scrollTop = panelRef.current.scrollHeight;
    }
  }, [turns?.length]);

  if (error) {
    return (
      <div className="history-panel error">
        <div className="error-message">
          <p>⚠ Failed to load history</p>
          <p className="error-details">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="history-panel">
      <div className="history-header">
        <h3>Conversation History</h3>
        <span className="turn-count">{turns?.length || 0} turns</span>
      </div>

      <div className="history-content" ref={panelRef}>
        {isLoading && !turns?.length ? (
          <div className="loading-state">
            <div className="spinner" />
            <p>Loading conversation history...</p>
          </div>
        ) : turns && turns.length > 0 ? (
          <div className="turns-list">
            {turns.map((turn) => (
              <div key={turn.turn_index} className={`turn ${turn.speaker.toLowerCase()}`}>
                <div className="turn-header">
                  <span className="speaker">
                    {turn.speaker === 'SYSTEM' ? '🤖 AI' : '👤 You'}
                  </span>
                  <span className="section-badge">{turn.section}</span>
                </div>

                <div className="turn-content">
                  {turn.content.length > 200 ? (
                    <>
                      <p>{turn.content.substring(0, 200)}...</p>
                      <details>
                        <summary>Read more</summary>
                        <p>{turn.content}</p>
                      </details>
                    </>
                  ) : (
                    <p>{turn.content}</p>
                  )}
                </div>

                <div className="turn-footer">
                  <time>{new Date(turn.created_at).toLocaleTimeString()}</time>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>No conversation history yet</p>
            <p className="hint">Start the interview to begin</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryPanel;
