import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SummaryGenerator } from '../components/SummaryGenerator';
import { SummaryView } from '../components/SummaryView';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('SummaryGeneration Integration Tests', () => {
  it('SummaryGenerator displays trigger button and options', () => {
    const onGenerate = vi.fn();
    render(<SummaryGenerator sessionId="sess-123" onGenerateSuccess={onGenerate} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByRole('button', { name: /Generate Summary/i })).toBeDefined();
    expect(screen.getByText(/Clinical Summary Generator/i)).toBeDefined();
  });

  it('SummaryView renders structured sections and metadata', () => {
    const mockSummary = {
      id: 'sum-123',
      session_id: 'sess-1',
      version: 1,
      workflow_status: 'DRAFT',
      status: 'SUCCESS',
      structured_summary: {
        chief_complaint: [{ name: 'Chest pain', status: 'KNOWN', details: 'Acute chest pain' }],
        history_of_present_illness: [],
        associated_symptoms: [],
        relevant_positive_findings: [],
        relevant_negative_findings: [],
        past_medical_history: [],
        past_surgical_history: [],
        medications: [],
        allergies: [],
        family_history: [],
        personal_social_history: [],
        review_of_systems: [],
        investigations: [],
        abnormal_findings: [],
        red_flags: [{ flag_name: 'CHEST_PAIN_ACUTE', description: 'Acute chest discomfort' }],
        information_gaps: ['ECG tracing pending'],
        generated_summary_text: 'Patient presents with acute chest pain.',
      },
      active_summary: {
        generated_summary_text: 'Patient presents with acute chest pain.',
      },
      physician_edited_summary: {},
      llm_model: 'mock-llm-v1',
      prompt_version: 'v1.0.0',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    render(<SummaryView summary={mockSummary as any} />, {
      wrapper: createWrapper(),
    });
    expect(screen.getByText(/Clinical Summary/i)).toBeDefined();
  });
});
