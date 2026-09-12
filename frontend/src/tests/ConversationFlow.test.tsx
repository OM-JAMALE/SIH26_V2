import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { ConversationStarter } from '../components/ConversationStarter';
import { SectionProgress } from '../components/SectionProgress';
import { ConversationTurn } from '../components/ConversationTurn';

describe('ConversationFlow Integration Tests', () => {
  it('User can start a conversation with patient ID form', () => {
    const onStart = vi.fn();
    render(
      <ConversationStarter
        onStartConversation={onStart}
        isLoading={false}
        error={null}
      />
    );

    expect(screen.getByText(/Start a new clinical interview session/i)).toBeDefined();
    expect(screen.getByRole('button', { name: /Start Interview/i })).toBeDefined();
  });

  it('Section progress advances through interview states', () => {
    render(
      <SectionProgress
        currentSection="CHIEF_COMPLAINT"
        socratesState="SITE"
        lifecycleStatus="IN_PROGRESS"
      />
    );

    expect(screen.getByText(/Interview Progress/i)).toBeDefined();
    expect(screen.getAllByText(/Chief Complaint/i).length).toBeGreaterThan(0);
  });

  it('History displays question and response in ConversationTurn', () => {
    const onSubmit = vi.fn();
    render(
      <ConversationTurn
        currentQuestion="What brings you in today?"
        onSubmit={onSubmit}
        isLoading={false}
        error={null}
        lastResponse="I have severe headache for 3 days"
        currentSection="CHIEF_COMPLAINT"
      />
    );

    expect(screen.getByText(/What brings you in today\?/i)).toBeDefined();
    expect(screen.getByText(/I have severe headache for 3 days/i)).toBeDefined();
  });
});
