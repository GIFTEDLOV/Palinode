import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components';
import { ProtocolProvider, TransactionProvider, WalletProvider } from './context';
import { EvidenceCanonicalViews, RecoveryCanonicalViews, RevocationCanonicalViews } from './detailViews';
import { ActivityPage, AuthoritiesPage, AuthorityDetailPage, DecisionDetailPage, DecisionPage, DocsPage, EvidenceDetailPage, EvidencePage, GraphPage, IntegratePage, LandingPage, OverviewPage, ProofPage, RecoveryDetailPage, RecoveriesPage, RevocationDetailPage, RevocationsPage, SuccessorPage } from './pages';

export default function App() {
  return <BrowserRouter><WalletProvider><ProtocolProvider><TransactionProvider><Routes>
    <Route path="/" element={<LandingPage />} />
    <Route path="/docs" element={<DocsPage />} />
    <Route path="/app" element={<AppShell />}>
      <Route index element={<OverviewPage />} />
      <Route path="graph" element={<GraphPage />} />
      <Route path="evidence" element={<EvidencePage />} />
      <Route path="evidence/successor" element={<SuccessorPage />} />
      <Route path="evidence/:id" element={<><EvidenceDetailPage /><EvidenceCanonicalViews /></>} />
      <Route path="decisions" element={<DecisionPage />} />
      <Route path="decisions/:id" element={<DecisionDetailPage />} />
      <Route path="revocations" element={<RevocationsPage />} />
      <Route path="revocations/:id" element={<><RevocationDetailPage /><RevocationCanonicalViews /></>} />
      <Route path="recoveries" element={<RecoveriesPage />} />
      <Route path="recoveries/:id" element={<><RecoveryDetailPage /><RecoveryCanonicalViews /></>} />
      <Route path="authorities" element={<AuthoritiesPage />} />
      <Route path="authorities/:id" element={<AuthorityDetailPage />} />
      <Route path="activity" element={<ActivityPage />} />
      <Route path="proof" element={<ProofPage />} />
      <Route path="integrate" element={<IntegratePage />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></TransactionProvider></ProtocolProvider></WalletProvider></BrowserRouter>;
}
