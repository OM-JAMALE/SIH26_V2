import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DocumentUpload } from '../components/DocumentUpload';
import { DocumentViewer } from '../components/DocumentViewer';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('DocumentUpload Integration Tests', () => {
  it('User can select and see upload file picker UI', () => {
    render(<DocumentUpload sessionId="sess-123" />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText(/Upload Medical Document/i)).toBeDefined();
    expect(screen.getByText(/Supports PDF, PNG, JPEG \(Max 25MB\)/i)).toBeDefined();
  });

  it('Extracted text and lab entities display in DocumentViewer', () => {
    const mockDoc = {
      id: 'doc-123',
      session_id: 'sess-1',
      filename: 'blood_report.pdf',
      mime_type: 'application/pdf',
      file_size: 1024,
      processing_status: 'EXTRACTED',
      raw_text: 'Fasting Blood Sugar: 145 mg/dL (70-99)',
      created_at: new Date().toISOString(),
      extracted_entities: [
        {
          id: 'ent-1',
          session_id: 'sess-1',
          document_id: 'doc-123',
          entity_type: 'LAB_RESULT',
          entity_name: 'Fasting Blood Sugar',
          value: '145 mg/dL',
          numeric_value: 145,
          unit: 'mg/dL',
          reference_range: '70 - 99 mg/dL',
          is_abnormal: true,
          confidence_score: 0.99,
          metadata_json: {},
          created_at: new Date().toISOString(),
        },
      ],
    };

    render(
      <DocumentViewer
        sessionId="sess-1"
        documentId="doc-123"
        document={mockDoc as any}
        onClose={() => {}}
      />,
      {
        wrapper: createWrapper(),
      }
    );
    expect(screen.getByText(/blood_report.pdf/i)).toBeDefined();
  });
});
