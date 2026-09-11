/**
 * SummaryView Component
 * Display generated clinical summary with all sections
 */

import React from 'react';
import type { SummaryResponse, RedFlagItem, ClinicalItem } from '../types/summary';
import './SummaryView.css';

interface SummaryViewProps {
  summary: SummaryResponse | null;
  isLoading?: boolean;
  error?: string | null;
}

export const SummaryView: React.FC<SummaryViewProps> = ({
  summary,
  isLoading = false,
  error = null,
}) => {
  if (!summary && !isLoading && !error) {
    return (
      <div className="summary-view empty">
        <p>Generate a summary to view results</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="summary-view loading">
        <div className="spinner" />
        <p>Generating summary...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="summary-view error">
        <p className="error-message">⚠ Failed to load summary</p>
        <p className="error-details">{error}</p>
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="summary-view">
      <div className="view-header">
        <h2>📋 Clinical Summary</h2>
        <div className="view-metadata">
          {summary.model_version && (
            <span className="metadata-item">
              <strong>Model:</strong> {summary.model_version}
            </span>
          )}
          <span className="metadata-item">
            <strong>Generated:</strong> {new Date(summary.created_at).toLocaleString()}
          </span>
        </div>
      </div>

      {/* Chief Complaint */}
      <section className="summary-section chief-complaint">
        <h3>🏥 Chief Complaint</h3>
        <p className="chief-complaint-text">{summary.chief_complaint}</p>
      </section>

      {/* Summary Text */}
      <section className="summary-section summary-text">
        <h3>📝 Summary</h3>
        <div className="summary-content">
          <p>{summary.generated_summary_text}</p>
        </div>
      </section>

      {/* Key Findings */}
      {summary.key_findings && summary.key_findings.length > 0 && (
        <section className="summary-section key-findings">
          <h3>🔍 Key Findings</h3>
          <ul className="findings-list">
            {summary.key_findings.map((finding, idx) => (
              <li key={idx} className="finding-item">
                <span className="finding-name">{finding.name}</span>
                {finding.details && (
                  <span className="finding-details">— {finding.details}</span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Red Flags */}
      {summary.red_flags && summary.red_flags.length > 0 && (
        <section className="summary-section red-flags">
          <h3>⚠ Red Flags</h3>
          <div className="flags-container">
            {summary.red_flags.map((flag, idx) => (
              <div key={idx} className="red-flag-card">
                <div className="flag-header">
                  <span className="flag-icon">🚨</span>
                  <span className="flag-name">{flag.flag_name}</span>
                </div>
                <p className="flag-description">{flag.description}</p>
                <div className="flag-source">
                  <small>Source: {flag.source}</small>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Recommendations */}
      {summary.recommendations && summary.recommendations.length > 0 && (
        <section className="summary-section recommendations">
          <h3>💡 Recommendations</h3>
          <ul className="recommendations-list">
            {summary.recommendations.map((rec, idx) => (
              <li key={idx} className="recommendation-item">
                <span className="rec-number">{idx + 1}</span>
                <span className="rec-text">{rec}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Uncertainty Notes */}
      {summary.uncertainty_notes && summary.uncertainty_notes.length > 0 && (
        <section className="summary-section uncertainty">
          <h3>❓ Uncertainty Notes</h3>
          <div className="uncertainty-list">
            {summary.uncertainty_notes.map((note, idx) => (
              <div key={idx} className="uncertainty-item">
                <span className="note-icon">?</span>
                <p>{note}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Metadata Footer */}
      <div className="view-footer">
        <div className="footer-info">
          <small>
            <strong>Summary ID:</strong> {summary.summary_id}
          </small>
          <small>
            <strong>Session ID:</strong> {summary.session_id}
          </small>
        </div>
      </div>
    </div>
  );
};

export default SummaryView;
