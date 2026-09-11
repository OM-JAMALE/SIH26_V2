/**
 * SummaryGenerator Component
 * Button to generate clinical summary with loading state
 */

import React, { useState } from 'react';
import { useGenerateSummary } from '../hooks/useSummary';
import './SummaryGenerator.css';

interface SummaryGeneratorProps {
  sessionId: string | null;
  onGenerateSuccess?: (summaryId: string) => void;
  onError?: (error: string) => void;
}

export const SummaryGenerator: React.FC<SummaryGeneratorProps> = ({
  sessionId,
  onGenerateSuccess,
  onError,
}) => {
  const [includeRecommendations, setIncludeRecommendations] = useState(true);
  const [includeAbnormalitiesOnly, setIncludeAbnormalitiesOnly] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const generateMutation = useGenerateSummary();

  const handleGenerate = async () => {
    if (!sessionId) return;

    setError(null);
    try {
      const result = await generateMutation.mutateAsync({
        sessionId,
        data: {
          include_recommendations: includeRecommendations,
          include_abnormalities_only: includeAbnormalitiesOnly,
        },
      });

      onGenerateSuccess?.(result.summary_id);
    } catch (err: any) {
      const errorMsg = err.error || 'Failed to generate summary';
      setError(errorMsg);
      onError?.(errorMsg);
    }
  };

  const isDisabled = !sessionId || generateMutation.isPending;

  return (
    <div className="summary-generator">
      <div className="generator-header">
        <h3>📋 Clinical Summary Generator</h3>
        <p className="subtitle">Generate a comprehensive summary from the conversation</p>
      </div>

      <div className="generator-options">
        <label className="checkbox-option">
          <input
            type="checkbox"
            checked={includeRecommendations}
            onChange={(e) => setIncludeRecommendations(e.target.checked)}
            disabled={isDisabled}
          />
          <span>
            <strong>Include Recommendations</strong>
            <small>Add suggested next steps</small>
          </span>
        </label>

        <label className="checkbox-option">
          <input
            type="checkbox"
            checked={includeAbnormalitiesOnly}
            onChange={(e) => setIncludeAbnormalitiesOnly(e.target.checked)}
            disabled={isDisabled}
          />
          <span>
            <strong>Show Abnormal Findings Only</strong>
            <small>Filter to significant findings</small>
          </span>
        </label>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="error-alert">
          <span className="error-icon">⚠</span>
          <p>{error}</p>
        </div>
      )}

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={isDisabled}
        className="generate-button"
      >
        {generateMutation.isPending ? (
          <>
            <span className="spinner" />
            Generating Summary...
          </>
        ) : (
          <>
            <span className="icon">✨</span>
            Generate Summary
          </>
        )}
      </button>

      {/* Info */}
      <div className="generator-info">
        <p className="info-text">
          The summary will combine conversation history with uploaded documents
          to create a comprehensive clinical overview. Physicians can review and
          approve the generated summary before sharing.
        </p>
      </div>
    </div>
  );
};

export default SummaryGenerator;
