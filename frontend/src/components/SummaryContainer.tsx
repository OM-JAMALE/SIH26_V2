/**
 * SummaryContainer Component
 * Main orchestrator for summary generation, viewing, and review
 */

import React, { useState } from 'react';
import { SummaryGenerator } from './SummaryGenerator';
import { SummaryView } from './SummaryView';
import { SummaryReview } from './SummaryReview';
import { useSummary } from '../hooks/useSummary';
import type { SummaryResponse } from '../types/summary';
import './SummaryContainer.css';

interface SummaryContainerProps {
  sessionId: string | null;
}

export const SummaryContainer: React.FC<SummaryContainerProps> = ({ sessionId }) => {
  const [selectedSummaryId, setSelectedSummaryId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  const summaryQuery = useSummary(sessionId, selectedSummaryId);

  const handleGenerateSuccess = (summaryId: string) => {
    setSelectedSummaryId(summaryId);
    setSuccessMessage('Summary generated successfully!');
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleReviewSuccess = () => {
    setSuccessMessage('Review submitted successfully!');
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleError = (errorMsg: string) => {
    setError(errorMsg);
    setTimeout(() => setError(null), 5000);
  };

  if (!sessionId) {
    return (
      <div className="summary-container empty-state">
        <div className="empty-content">
          <p className="empty-icon">📋</p>
          <p className="empty-text">Start a conversation to generate a clinical summary</p>
        </div>
      </div>
    );
  }

  return (
    <div className="summary-container">
      {/* Success Message */}
      {successMessage && (
        <div className="success-message">
          <span className="success-icon">✓</span>
          <p>{successMessage}</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="error-message">
          <span className="error-icon">⚠</span>
          <p>{error}</p>
        </div>
      )}

      <div className="summary-layout">
        {/* Generator Section */}
        <section className="generator-section">
          <SummaryGenerator
            sessionId={sessionId}
            onGenerateSuccess={handleGenerateSuccess}
            onError={handleError}
          />
        </section>

        {/* View + Review Section */}
        <div className="view-review-section">
          {/* View Pane */}
          <section className="view-pane">
            <SummaryView
              summary={summaryQuery.data || null}
              isLoading={summaryQuery.isLoading}
              error={summaryQuery.error?.error || null}
            />
          </section>

          {/* Review Pane */}
          <section className="review-pane">
            <SummaryReview
              summary={summaryQuery.data || null}
              onReviewSuccess={handleReviewSuccess}
              onError={handleError}
            />
          </section>
        </div>
      </div>
    </div>
  );
};

export default SummaryContainer;
