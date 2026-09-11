import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from './pages/App';
import { PatientPage } from './pages/PatientPage';
import { ConversationPage } from './pages/ConversationPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { SummaryPage } from './pages/SummaryPage';
import { ConsentPage } from './pages/ConsentPage';
import { ConversationSkeleton, DocumentSkeleton, SummarySkeleton } from './components/common/Skeleton';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Navigate to="/identify" replace />} />
            <Route path="identify" element={<PatientPage />} />
            <Route
              path="converse"
              element={
                <Suspense fallback={<ConversationSkeleton />}>
                  <ConversationPage />
                </Suspense>
              }
            />
            <Route
              path="documents"
              element={
                <Suspense fallback={<DocumentSkeleton />}>
                  <DocumentsPage />
                </Suspense>
              }
            />
            <Route
              path="summary"
              element={
                <Suspense fallback={<SummarySkeleton />}>
                  <SummaryPage />
                </Suspense>
              }
            />
            <Route path="consent" element={<ConsentPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
