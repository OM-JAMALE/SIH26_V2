/**
 * ConversationStarter Component
 * Form to start a new conversation session
 */

import React, { useState } from 'react';
import type { SessionMode } from '../types/conversation';
import './ConversationStarter.css';

interface ConversationStarterProps {
  onStartConversation: (patientId: string, mode: SessionMode) => void;
  isLoading: boolean;
  error: string | null;
}

export const ConversationStarter: React.FC<ConversationStarterProps> = ({
  onStartConversation,
  isLoading,
  error,
}) => {
  const [patientId, setPatientId] = useState('');
  const [mode, setMode] = useState<SessionMode>('MODERN');
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (patientId.trim() && disclaimerAccepted && !isLoading) {
      onStartConversation(patientId, mode);
    }
  };

  const isFormValid = patientId.trim() && disclaimerAccepted && !isLoading;

  return (
    <div className="conversation-starter">
      <div className="starter-header">
        <h2>🏥 Healthcare AI Pre-Consultation</h2>
        <p>Start a new clinical interview session</p>
      </div>

      <form onSubmit={handleSubmit} className="starter-form">
        {/* Patient ID Input */}
        <div className="form-group">
          <label htmlFor="patientId" className="form-label">
            Patient ID / MRN
            <span className="required">*</span>
          </label>
          <input
            id="patientId"
            type="text"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            placeholder="Enter patient ID or medical record number"
            className="form-input"
            disabled={isLoading}
            required
          />
          <p className="form-hint">
            This can be any identifier (UUID, MRN, etc.)
          </p>
        </div>

        {/* Mode Selection */}
        <div className="form-group">
          <label className="form-label">
            Interview Mode
            <span className="required">*</span>
          </label>
          <div className="mode-options">
            <label className="radio-option">
              <input
                type="radio"
                value="MODERN"
                checked={mode === 'MODERN'}
                onChange={(e) => setMode(e.target.value as SessionMode)}
                disabled={isLoading}
              />
              <span className="radio-label">
                <strong>Modern Medicine</strong>
                <small>Conventional medical interview</small>
              </span>
            </label>

            <label className="radio-option">
              <input
                type="radio"
                value="AYUSH"
                checked={mode === 'AYUSH'}
                onChange={(e) => setMode(e.target.value as SessionMode)}
                disabled={isLoading}
              />
              <span className="radio-label">
                <strong>AYUSH</strong>
                <small>Ayurveda, Yoga, Unani, Siddha, Homeopathy</small>
              </span>
            </label>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="disclaimer-section">
          <div className="disclaimer-box">
            <h4>⚠ Important Disclaimer</h4>
            <p>
              This AI system is designed as a pre-consultation aid only. It is:
            </p>
            <ul>
              <li>NOT a substitute for professional medical advice</li>
              <li>NOT intended for emergency situations</li>
              <li>For informational purposes only</li>
              <li>Subject to data privacy regulations (HIPAA/GDPR)</li>
            </ul>
            <p>
              Always consult with a licensed healthcare provider for diagnosis and treatment.
            </p>
          </div>

          <label className="checkbox-option">
            <input
              type="checkbox"
              checked={disclaimerAccepted}
              onChange={(e) => setDisclaimerAccepted(e.target.checked)}
              disabled={isLoading}
              required
            />
            <span>
              I understand and accept the disclaimer above
              <span className="required">*</span>
            </span>
          </label>
        </div>

        {/* Error Display */}
        {error && (
          <div className="error-alert">
            <span className="error-icon">✕</span>
            <p>{error}</p>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!isFormValid}
          className="start-button"
        >
          {isLoading ? (
            <>
              <span className="spinner" />
              Starting Interview...
            </>
          ) : (
            <>
              <span className="start-icon">▶</span>
              Start Interview
            </>
          )}
        </button>
      </form>

      {/* Information Footer */}
      <div className="starter-footer">
        <p className="privacy-note">
          💾 Your conversation data is encrypted and stored securely.
          See our privacy policy for details.
        </p>
      </div>
    </div>
  );
};

export default ConversationStarter;
