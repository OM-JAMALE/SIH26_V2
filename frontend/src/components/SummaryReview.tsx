/**
 * SummaryReview Component
 * Physician review interface with approve/edit/reject buttons
 */

import React, { useState } from 'react';
import { useSubmitReview } from '../hooks/useSummary';
import type { SummaryResponse } from '../types/summary';
import './SummaryReview.css';

interface SummaryReviewProps {
  summary: SummaryResponse | null;
  onReviewSuccess?: () => void;
  onError?: (error: string) => void;
}

type ReviewAction = 'approve' | 'reject' | 'edit' | null;

export const SummaryReview: React.FC<SummaryReviewProps> = ({
  summary,
  onReviewSuccess,
  onError,
}) => {
  const [action, setAction] = useState<ReviewAction>(null);
  const [notes, setNotes] = useState('');
  const [editedText, setEditedText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const reviewMutation = useSubmitReview();

  if (!summary) {
    return (
      <div className="summary-review empty">
        <p>Generate a summary to review</p>
      </div>
    );
  }

  const handleApprove = async () => {
    if (!summary) return;
    setError(null);
    try {
      await reviewMutation.mutateAsync({
        sessionId: summary.session_id,
        summaryId: summary.summary_id,
        status: 'APPROVED',
        notes: notes || undefined,
      });
      onReviewSuccess?.();
      setAction(null);
      setNotes('');
    } catch (err: any) {
      const errorMsg = err.error || 'Review failed';
      setError(errorMsg);
      onError?.(errorMsg);
    }
  };

  const handleReject = async () => {
    if (!notes.trim()) {
      setError('Please provide rejection notes');
      return;
    }
    if (!summary) return;
    setError(null);
    try {
      await reviewMutation.mutateAsync({
        sessionId: summary.session_id,
        summaryId: summary.summary_id,
        status: 'REJECTED',
        notes,
      });
      onReviewSuccess?.();
      setAction(null);
      setNotes('');
    } catch (err: any) {
      const errorMsg = err.error || 'Review failed';
      setError(errorMsg);
      onError?.(errorMsg);
    }
  };

  const handleEdit = async () => {
    if (!editedText.trim()) {
      setError('Please edit the summary text');
      return;
    }
    if (!summary) return;
    setError(null);
    try {
      await reviewMutation.mutateAsync({
        sessionId: summary.session_id,
        summaryId: summary.summary_id,
        status: 'EDITED',
        editedSummary: editedText,
        notes: notes || undefined,
      });
      onReviewSuccess?.();
      setAction(null);
      setEditedText('');
      setNotes('');
    } catch (err: any) {
      const errorMsg = err.error || 'Review failed';
      setError(errorMsg);
      onError?.(errorMsg);
    }
  };

  const isProcessing = reviewMutation.isPending;

  return (
    <div className="summary-review">
      <div className="review-header">
        <h3>👨‍⚕️ Physician Review</h3>
        <span className="review-status pending">PENDING REVIEW</span>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="error-alert">
          <span className="error-icon">⚠</span>
          <p>{error}</p>
        </div>
      )}

      {/* Action Buttons (Default View) */}
      {action === null && (
        <div className="review-actions">
          <button
            className="action-button approve-button"
            onClick={() => setAction('approve')}
            disabled={isProcessing}
            title="Approve this summary"
          >
            <span className="icon">✓</span>
            <span className="label">Approve</span>
          </button>
          <button
            className="action-button edit-button"
            onClick={() => {
              setAction('edit');
              setEditedText(summary.generated_summary_text);
            }}
            disabled={isProcessing}
            title="Make edits to the summary"
          >
            <span className="icon">✏️</span>
            <span className="label">Edit</span>
          </button>
          <button
            className="action-button reject-button"
            onClick={() => setAction('reject')}
            disabled={isProcessing}
            title="Reject this summary"
          >
            <span className="icon">✕</span>
            <span className="label">Reject</span>
          </button>
        </div>
      )}

      {/* Approve Panel */}
      {action === 'approve' && (
        <div className="review-panel approve-panel">
          <div className="panel-header">
            <h4>Approve Summary</h4>
            <p className="panel-hint">Optionally add notes before approving</p>
          </div>

          <div className="form-group">
            <label htmlFor="approve-notes">Approval Notes (Optional)</label>
            <textarea
              id="approve-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any approval comments or reviewer notes..."
              rows={3}
              disabled={isProcessing}
            />
          </div>

          <div className="panel-actions">
            <button
              className="confirm-button"
              onClick={handleApprove}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <>
                  <span className="spinner" />
                  Processing...
                </>
              ) : (
                <>
                  <span className="icon">✓</span>
                  Confirm Approval
                </>
              )}
            </button>
            <button
              className="cancel-button"
              onClick={() => {
                setAction(null);
                setNotes('');
              }}
              disabled={isProcessing}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Reject Panel */}
      {action === 'reject' && (
        <div className="review-panel reject-panel">
          <div className="panel-header">
            <h4>Reject Summary</h4>
            <p className="panel-hint required">Reason is required</p>
          </div>

          <div className="form-group">
            <label htmlFor="reject-notes">Reason for Rejection *</label>
            <textarea
              id="reject-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Explain why this summary should be rejected..."
              rows={4}
              disabled={isProcessing}
              required
            />
          </div>

          <div className="panel-actions">
            <button
              className="confirm-button reject"
              onClick={handleReject}
              disabled={isProcessing || !notes.trim()}
            >
              {isProcessing ? (
                <>
                  <span className="spinner" />
                  Processing...
                </>
              ) : (
                <>
                  <span className="icon">✕</span>
                  Confirm Rejection
                </>
              )}
            </button>
            <button
              className="cancel-button"
              onClick={() => {
                setAction(null);
                setNotes('');
              }}
              disabled={isProcessing}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Edit Panel */}
      {action === 'edit' && (
        <div className="review-panel edit-panel">
          <div className="panel-header">
            <h4>Edit Summary</h4>
            <p className="panel-hint">Make any necessary corrections or additions</p>
          </div>

          <div className="form-group">
            <label htmlFor="edit-text">Summary Text</label>
            <textarea
              id="edit-text"
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              placeholder="Edit the summary text..."
              rows={8}
              disabled={isProcessing}
            />
            <small className="char-count">
              {editedText.length} characters
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="edit-notes">Edit Notes (Optional)</label>
            <textarea
              id="edit-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Explain what you changed and why..."
              rows={3}
              disabled={isProcessing}
            />
          </div>

          <div className="panel-actions">
            <button
              className="confirm-button"
              onClick={handleEdit}
              disabled={isProcessing || !editedText.trim()}
            >
              {isProcessing ? (
                <>
                  <span className="spinner" />
                  Processing...
                </>
              ) : (
                <>
                  <span className="icon">✓</span>
                  Save Edits
                </>
              )}
            </button>
            <button
              className="cancel-button"
              onClick={() => {
                setAction(null);
                setEditedText('');
                setNotes('');
              }}
              disabled={isProcessing}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Review Status Footer */}
      <div className="review-footer">
        <small className="footer-note">
          This review will be recorded and timestamped in the medical record.
        </small>
      </div>
    </div>
  );
};

export default SummaryReview;
