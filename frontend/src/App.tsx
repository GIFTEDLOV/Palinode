import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components';
import { ProtocolProvider, TransactionProvider, WalletProvider } from './context';
import { EvidenceCanonicalViews, RecoveryCanonicalViews, RevocationCanonicalViews } from './detailViews';
import { ActivityPage, AuthoritiesPage, DecisionPage, DocsPage, EvidencePage, GraphPage, IntegratePage, LandingPage, OverviewPage, ProofPage, RecoveriesPage, SuccessorPage } from './pages';
import { RevocationsPage } from './revocationsPage';
import { V4AuthorityDetailPage, V4DecisionDetailPage, V4EvidenceDetailPage, V4RecoveryDetailPage, V4RevocationDetailPage } from './detailPages';

export default function App() {
  return <BrowserRouter><WalletProvider><ProtocolProvider><TransactionProvider><Routes>
    <Route path="/" element={<LandingPage />} />
    <Route path="/docs" element={<DocsPage />} />
    <Route path="/app" element={<AppShell />}>
      <Route index element={<OverviewPage />} />
      <Route path="graph" element={<GraphPage />} />
      <Route path="evidence" element={<EvidencePage />} />
      <Route path="evidence/successor" element={<SuccessorPage />} />
      <Route path="evidence/:id" element={<><V4EvidenceDetailPage /><EvidenceCanonicalViews /></>} />
      <Route path="decisions" element={<DecisionPage />} />
      <Route path="decisions/:id" element={<V4DecisionDetailPage />} />
      <Route path="revocations" element={<RevocationsPage />} />
      <Route path="revocations/:id" element={<><V4RevocationDetailPage /><RevocationCanonicalViews /></>} />
      <Route path="recoveries" element={<RecoveriesPage />} />
      <Route path="recoveries/:id" element={<><V4RecoveryDetailPage /><RecoveryCanonicalViews /></>} />
      <Route path="authorities" element={<AuthoritiesPage />} />
      <Route path="authorities/:id" element={<V4AuthorityDetailPage />} />
      <Route path="activity" element={<ActivityPage />} />
      <Route path="proof" element={<ProofPage />} />
      <Route path="integrate" element={<IntegratePage />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></TransactionProvider></ProtocolProvider></WalletProvider></BrowserRouter>;
}
