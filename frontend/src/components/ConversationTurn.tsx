/**
 * ConversationTurn Component
 * Displays current question, user input box, and shows responses
 */

import React, { useState, useRef, useEffect } from 'react';
import './ConversationTurn.css';

interface ConversationTurnProps {
  currentQuestion: string;
  onSubmit: (text: string) => void;
  isLoading: boolean;
  error: string | null;
  lastResponse?: string;
  currentSection: string;
}

export const ConversationTurn: React.FC<ConversationTurnProps> = ({
  currentQuestion,
  onSubmit,
  isLoading,
  error,
  lastResponse,
  currentSection,
}) => {
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Focus input when question changes
  useEffect(() => {
    if (inputRef.current && !isLoading) {
      inputRef.current.focus();
    }
  }, [currentQuestion, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSubmit(inputValue);
      setInputValue('');
    }
  };

  const isDisabled = isLoading || !inputValue.trim();

  return (
    <div className="conversation-turn">
      {/* Current Question Display */}
      <div className="question-section">
        <div className="question-header">
          <h3>🤖 AI Assistant</h3>
          <span className="section-badge">{currentSection}</span>
        </div>

        <div className="question-content">
          <p className="question">{currentQuestion}</p>
        </div>
      </div>

      {/* Last Response Display */}
      {lastResponse && (
        <div className="last-response-section">
          <h4>Last Response</h4>
          <p>{lastResponse}</p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-alert">
          <span className="error-icon">⚠</span>
          <p>{error}</p>
        </div>
      )}

      {/* User Input Form */}
      <form onSubmit={handleSubmit} className="user-input-form">
        <div className="input-container">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your response here... (Ctrl+Enter to submit)"
            className="input-textarea"
            disabled={isLoading}
            rows={3}
            onKeyDown={(e) => {
              if (e.ctrlKey && e.key === 'Enter') {
                handleSubmit(e as any);
              }
            }}
          />

          <div className="input-footer">
            <span className="char-count">
              {inputValue.length} / 1000 characters
            </span>
            <button
              type="submit"
              disabled={isDisabled}
              className="submit-button"
            >
              {isLoading ? (
                <>
                  <span className="spinner" />
                  Processing...
                </>
              ) : (
                <>
                  <span className="send-icon">→</span>
                  Send Response
                </>
              )}
            </button>
          </div>
        </div>

        {isLoading && (
          <div className="loading-message">
            <div className="spinner" />
            <p>AI is processing your response...</p>
          </div>
        )}
      </form>

      {/* Tips */}
      <div className="tips-section">
        <details>
          <summary>💡 Tips</summary>
          <ul>
            <li>Be descriptive when answering medical questions</li>
            <li>Include timeframes and severity when applicable</li>
            <li>Mention any relevant symptoms or conditions</li>
            <li>Press Ctrl+Enter to quickly submit</li>
          </ul>
        </details>
      </div>
    </div>
  );
};

export default ConversationTurn;
