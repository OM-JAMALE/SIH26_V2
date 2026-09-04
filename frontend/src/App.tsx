import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { PatientPage } from './pages/PatientPage';
import { ConversationPage } from './pages/ConversationPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { SummaryPage } from './pages/SummaryPage';
import { ConsentPage } from './pages/ConsentPage';

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
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/identify" replace />} />
            <Route path="identify" element={<PatientPage />} />
            <Route path="converse" element={<ConversationPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="summary" element={<SummaryPage />} />
            <Route path="consent" element={<ConsentPage />} />
          </Route>
        </Routes>

      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
