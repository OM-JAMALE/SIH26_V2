/**
 * SectionProgress Component
 * Displays visual indicator of progress through interview sections
 */

import React from 'react';
import type { InterviewSection } from '../types/conversation';
import './SectionProgress.css';

interface SectionProgressProps {
  currentSection: InterviewSection;
  lifecycleStatus: string;
  socratesState?: string;
}

const SECTIONS: InterviewSection[] = [
  'IDENTIFICATION',
  'CHIEF_COMPLAINT',
  'HPI',
  'PAST_MEDICAL_HISTORY',
  'PAST_SURGICAL_HISTORY',
  'MEDICATIONS',
  'ALLERGIES',
  'FAMILY_HISTORY',
  'PERSONAL_HISTORY',
  'REVIEW_OF_SYSTEMS',
  'COMPLETED',
];

const SECTION_LABELS: Record<InterviewSection, string> = {
  IDENTIFICATION: 'Identification',
  CHIEF_COMPLAINT: 'Chief Complaint',
  HPI: 'History of Present Illness',
  PAST_MEDICAL_HISTORY: 'Past Medical History',
  PAST_SURGICAL_HISTORY: 'Past Surgical History',
  MEDICATIONS: 'Medications',
  ALLERGIES: 'Allergies',
  FAMILY_HISTORY: 'Family History',
  PERSONAL_HISTORY: 'Personal History',
  REVIEW_OF_SYSTEMS: 'Review of Systems',
  COMPLETED: 'Completed',
};

export const SectionProgress: React.FC<SectionProgressProps> = ({
  currentSection,
  lifecycleStatus,
}) => {
  const currentIndex = SECTIONS.indexOf(currentSection);
  const progress = ((currentIndex + 1) / SECTIONS.length) * 100;

  return (
    <div className="section-progress">
      <div className="progress-header">
        <h3>Interview Progress</h3>
        <span className="status-badge" data-status={lifecycleStatus}>
          {lifecycleStatus === 'COMPLETED' ? '✓ Completed' : 'In Progress'}
        </span>
      </div>

      <div className="progress-bar-container">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="progress-text">
          {currentIndex + 1} of {SECTIONS.length}
        </div>
      </div>

      <div className="sections-grid">
        {SECTIONS.map((section, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = section === currentSection;

          return (
            <div
              key={section}
              className={`section-item ${isCompleted ? 'completed' : ''} ${
                isCurrent ? 'current' : ''
              }`}
              title={SECTION_LABELS[section]}
            >
              <div className="section-number">
                {isCompleted ? '✓' : index + 1}
              </div>
              <div className="section-name">
                {SECTION_LABELS[section]}
              </div>
            </div>
          );
        })}
      </div>

      <div className="current-section-display">
        <p className="label">Current Section:</p>
        <p className="section-name">{SECTION_LABELS[currentSection]}</p>
      </div>
    </div>
  );
};

export default SectionProgress;
