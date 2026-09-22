import { useState } from 'react';
import { NavLink, Outlet, Link, useLocation } from 'react-router-dom';
import { CONTRACT_ADDRESS, CONTRACT_SHA256, NETWORK, CHAIN_ID, FREEZE_COMMIT } from './config';
import { useProtocol, useTransactions, useWallet } from './context';
import { formatDate, formatStatus, statusClass, truncate } from './lib/utils';
import type { NodeRecord } from './types';
import type { CalldataEncodable } from 'genlayer-js/types';
import { assertSafeProcessImpactDescriptor, createPendingWriteDescriptor, type PendingWriteDescriptor } from './lib/writeDescriptor';

export function StatusPill({ value, label }: { value?: string; label?: string }) { return <span className={statusClass(value)}>{label || formatStatus(value)}</span>; }
export function CopyButton({ value, compact = false }: { value: string; compact?: boolean }) {
  const [copied, setCopied] = useState(false);
  return <button type="button" aria-label={`Copy ${value}`} className={compact ? 'copy-button compact' : 'copy-button'} title="Copy value" onClick={() => { void navigator.clipboard.writeText(value).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1200); }); }}>{copied ? 'COPIED' : compact ? '⧉' : 'COPY'}</button>;
}
export function Kicker({ children }: { children: React.ReactNode }) { return <div className="kicker">{children}</div>; }
export function SectionTitle({ eyebrow, title, action }: { eyebrow?: string; title: string; action?: React.ReactNode }) { return <div className="section-title"><div>{eyebrow && <Kicker>{eyebrow}</Kicker>}<h2>{title}</h2></div>{action}</div>; }
export function PageHeader({ eyebrow, title, intro, action }: { eyebrow: string; title: string; intro?: string; action?: React.ReactNode }) { return <header className="page-header"><div><Kicker>{eyebrow}</Kicker><h1>{title}</h1>{intro && <p>{intro}</p>}</div>{action && <div className="page-header-action">{action}</div>}</header>; }
export function EmptyState({ title, body, action }: { title: string; body: string; action?: React.ReactNode }) { return <div className="empty-state"><div className="empty-mark">∅</div><h3>{title}</h3><p>{body}</p>{action}</div>; }
export function ErrorState({ hasSnapshot, retry }: { hasSnapshot: boolean; retry?: () => void }) { return <div className="error-state"><Kicker>{hasSnapshot ? 'SYNC DELAYED' : 'CANONICAL SYNC UNAVAILABLE'}</Kicker><h3>{hasSnapshot ? 'Last verified state remains visible' : 'No verified snapshot is available yet'}</h3><p>{hasSnapshot ? 'Studionet could not refresh the canonical read. PALINODE is continuing to show the last verified snapshot.' : 'PALINODE could not refresh Studionet state. Try again when the canonical read surface is available.'}</p>{retry && <button className="button button-secondary" onClick={retry}>Try again</button>}</div>; }
export function DetailLoadingState({ label }: { label: string }) { return <div className="detail-sync-state" role="status"><div className="detail-sync-mark" aria-hidden="true" /><Kicker>SYNCING CANONICAL RECORD</Kicker><h3>Reading {label} from frozen V4 state</h3><p>Reading frozen V4 state from Studionet…</p></div>; }
export function DetailUnavailableState({ label, retry }: { label: string; retry?: () => void }) { return <div className="detail-sync-state detail-sync-unavailable" role="status"><Kicker>CANONICAL SYNC UNAVAILABLE</Kicker><h3>Unable to load this {label}</h3><p>PALINODE could not refresh Studionet state. No verified local record is available yet.</p>{retry && <button className="button button-secondary" onClick={retry}>Try again</button>}</div>; }
export function Metric({ label, value, note, tone = '' }: { label: string; value: string | number; note?: string; tone?: string }) { return <div className={`metric ${tone}`}><div className="metric-label">{label}</div><div className="metric-value">{value}</div>{note && <div className="metric-note">{note}</div>}</div>; }
export function DataRow({ label, value, mono = false, copy = false }: { label: string; value?: string; mono?: boolean; copy?: boolean }) { const display = value || '—'; return <div className="data-row"><span>{label}</span><strong className={mono ? 'mono' : ''}>{display}</strong>{copy && value && <CopyButton value={value} compact />}</div>; }
export function NodeBadge({ node }: { node: NodeRecord }) { return <span className={`node-badge node-${node.node_type.toLowerCase()}`}>{node.node_type}</span>; }

function navClass({ isActive }: { isActive: boolean }) { return isActive ? 'nav-link active' : 'nav-link'; }

export function AppShell() {
  const { address, chainId, lastUsedAddress, connecting, connect, disconnect, error: walletError } = useWallet();
  const { nodes, revocations, recoveries, loading, error, refresh, freshness, refreshedAt } = useProtocol();
  const { transactions, drawerOpen, setDrawerOpen } = useTransactions();
  const location = useLocation();
  const activeTx = transactions.filter((tx) => !['FINALIZED SUCCESS', 'FINALIZED ERROR', 'UNDETERMINED', 'CANCELED'].includes(tx.phase));
  const hasCanonicalSnapshot = nodes.length > 0 || revocations.length > 0 || recoveries.length > 0;
  const isDetailRoute = /^\/app\/(evidence|decisions|revocations|recoveries|authorities)\/[^/]+/.test(location.pathname);
  return <div className="app-frame">
    <header className="topbar">
      <Link className="brand" to="/"><span className="brand-mark">P</span><span>PALINODE</span><small>REVOCATION GRAPH</small></Link>
      <div className="topbar-right"><span className={`network-chip ${address && chainId !== CHAIN_ID ? 'wrong-network' : ''}`}><i />{address && chainId !== CHAIN_ID ? 'WRONG NETWORK' : `${NETWORK} / ${CHAIN_ID}`}</span><button className="wallet-button" onClick={address ? disconnect : () => void connect()}>{connecting ? 'CONNECTING…' : address ? truncate(address) : 'CONNECT WALLET'}</button>{!address && lastUsedAddress && <small className="wallet-last-used">LAST USED {truncate(lastUsedAddress)}</small>}<button className="icon-button" aria-label="Open transaction drawer" onClick={() => setDrawerOpen(true)}>◌<b>{activeTx.length || ''}</b></button></div>
    </header>
    <div className="app-layout">
      <aside className="sidebar">
        <nav className="primary-nav">
          <div className="nav-label">CONTROL PLANE</div>
          <NavLink to="/app" end className={navClass}>Overview <span>⌂</span></NavLink>
          <NavLink to="/app/graph" className={navClass}>Dependency graph <span>⌁</span></NavLink>
          <NavLink to="/app/evidence" className={navClass}>Evidence registry <span>{nodes.filter((n) => n.node_type === 'EVIDENCE').length}</span></NavLink>
          <NavLink to="/app/decisions" className={navClass}>Decisions <span>{nodes.filter((n) => n.node_type === 'DECISION').length}</span></NavLink>
          <NavLink to="/app/revocations" className={navClass}>Revocations <span>{revocations.filter((c) => c.case_status !== 'COMPLETE').length || ''}</span></NavLink>
          <NavLink to="/app/recoveries" className={navClass}>Recoveries <span>{recoveries.length || ''}</span></NavLink>
          <div className="nav-label nav-label-spaced">TRUST SURFACE</div>
          <NavLink to="/app/authorities" className={navClass}>Authorities <span>{nodes.length ? '↗' : ''}</span></NavLink>
          <NavLink to="/app/activity" className={navClass}>Activity <span>◎</span></NavLink>
          <NavLink to="/app/proof" className={navClass}>Proof & security <span>◆</span></NavLink>
          <NavLink to="/app/integrate" className={navClass}>Integrate <span>⌘</span></NavLink>
        </nav>
        <div className="sidebar-foot"><div className="rail-line" /><div className="sidebar-note"><span>FROZEN CONTRACT</span><strong>{truncate(CONTRACT_ADDRESS)}</strong><small>SHA256 {truncate(CONTRACT_SHA256, 10, 8)}</small></div><Link to="/docs" className="docs-link">Read protocol docs →</Link></div>
      </aside>
      <main className="main-content">
        {walletError && <div className="inline-alert warning">{walletError}</div>}
        {error && !loading && !hasCanonicalSnapshot && !isDetailRoute && <ErrorState hasSnapshot={false} retry={() => void refresh(true)} />}
        {location.pathname.startsWith('/app') && <div className="breadcrumb"><span>PALINODE</span><b>/</b><span>{location.pathname.split('/').filter(Boolean).slice(1).join(' / ') || 'overview'}</span><em className={'freshness freshness-' + freshness.toLowerCase()}>{freshness === 'LIVE' && refreshedAt ? 'LIVE · refreshed ' + formatDate(new Date(refreshedAt).toISOString()) : freshness === 'CACHED' ? 'CACHED SNAPSHOT · refreshing' : freshness === 'RPC_UNAVAILABLE' ? (hasCanonicalSnapshot ? 'STUDIONET THROTTLED · USING VERIFIED CACHE' : 'CANONICAL SYNC UNAVAILABLE') : loading ? 'REFRESHING' : freshness}</em></div>}
        <Outlet />
      </main>
    </div>
    {drawerOpen && <TransactionDrawer onClose={() => setDrawerOpen(false)} />}
  </div>;
}

export function TransactionDrawer({ onClose }: { onClose: () => void }) {
  const { transactions } = useTransactions();
  return <div className="drawer-backdrop" onClick={onClose}><aside className="transaction-drawer" aria-label="Transaction drawer" onClick={(event) => event.stopPropagation()}><div className="drawer-header"><div><Kicker>FINALITY TRACKER</Kicker><h2>Transactions</h2></div><button className="icon-button" aria-label="Close transaction drawer" onClick={onClose}>×</button></div>{transactions.length === 0 ? <EmptyState title="No tracked transactions" body="Writes submitted from this browser will persist here and resume by ID after refresh." /> : <div className="tx-list">{transactions.map((tx) => <TransactionItem key={tx.id} tx={tx} />)}</div>}</aside></div>;
}

  function TransactionItem({ tx }: { tx: import('./types').TrackedTransaction }) { return <div className="tx-item"><div className="tx-item-head"><strong>{tx.label}</strong><StatusPill value={tx.phase} /></div><div className="tx-method">{tx.method}</div><div className="tx-id mono">{truncate(tx.id, 14, 10)} <CopyButton value={tx.id} compact /></div><div className="tx-progress"><span className={tx.phase.includes('FINALIZED SUCCESS') ? 'done' : tx.phase.includes('ERROR') || tx.phase === 'UNDETERMINED' || tx.phase === 'CANCELED' ? 'bad' : 'current'} /></div><div className="tx-meta"><span>STORED {tx.protocolStatus}</span><span>{tx.executionResult}</span><span>{formatDate(tx.updatedAt)}</span></div>{tx.resolutionAction === 'Finalize' && <div className="tx-action">FINALIZATION AVAILABLE · action=Finalize</div>}{tx.error && <div className="tx-error">{tx.error}</div>}</div>; }

export function LiveContractStrip() { const { nodes, revocations, recoveries, freshness, refreshedAt } = useProtocol(); const hasCanonicalSnapshot = nodes.length > 0 || revocations.length > 0 || recoveries.length > 0; return <div className="live-strip"><span className="live-dot" /> {freshness === 'LIVE' ? 'LIVE CANONICAL STATE' : freshness === 'CACHED' ? 'CACHED SNAPSHOT' : freshness === 'RPC_UNAVAILABLE' ? (hasCanonicalSnapshot ? 'SYNC DELAYED · LAST VERIFIED SNAPSHOT' : 'CANONICAL SYNC UNAVAILABLE') : 'REFRESHING'} <span className="strip-divider" /> {NETWORK} <span className="strip-divider" /> <span className="mono">{truncate(CONTRACT_ADDRESS, 10, 8)}</span> <span className="strip-divider" /> <span className="mono">SHA {truncate(CONTRACT_SHA256, 8, 6)}</span>{refreshedAt && <small>READ {formatDate(new Date(refreshedAt).toISOString())}</small>}</div>; }

export function WriteAction({ label, method, args, children, className = 'button button-primary', onSubmitted, validationError }: { label: string; method: string; args: CalldataEncodable[]; children: React.ReactNode; className?: string; onSubmitted?: () => void; validationError?: string | null }) {
  const { address, chainId, connect } = useWallet();
  const { submit, setDrawerOpen } = useTransactions();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const run = async () => {
    if (validationError) { setError(validationError); return; }
    setBusy(true); setError(null);
    try { const connectedAddress = address || await connect(); if (!connectedAddress) throw new Error('Connect a wallet before sending a write.'); if (chainId !== null && chainId !== CHAIN_ID) throw new Error(`Switch wallet to ${NETWORK} (chain ${CHAIN_ID}) before sending a write.`); const descriptor = createPendingWriteDescriptor({ label, method, args }); await submit(descriptor, connectedAddress); onSubmitted?.(); setDrawerOpen(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Write was not submitted.'); }
    finally { setBusy(false); }
  };
  return <span className="action-wrap"><button type="button" className={className} disabled={busy || Boolean(validationError)} onClick={() => void run()}>{busy ? 'SUBMITTING…' : children}</button>{(error || validationError) && <small className="field-error">{error || validationError}</small>}</span>;
}

export function ConfirmedWriteAction({ label, method, args, children, safeCaseId, className = 'button button-primary' }: { label: string; method: string; args: CalldataEncodable[]; children: React.ReactNode; safeCaseId: string; className?: string }) {
  const { address, chainId, connect } = useWallet();
  const { submit, setDrawerOpen } = useTransactions();
  const [pending, setPending] = useState<PendingWriteDescriptor | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const openConfirmation = () => { setError(null); setPending(createPendingWriteDescriptor({ label, method, args })); };
  const confirm = async () => {
    if (!pending) return;
    setBusy(true); setError(null);
    try {
      assertSafeProcessImpactDescriptor(pending, safeCaseId);
      const connectedAddress = address || await connect();
      if (!connectedAddress) throw new Error('Connect a wallet before sending a write.');
      if (chainId !== null && chainId !== CHAIN_ID) throw new Error(`Switch wallet to ${NETWORK} (chain ${CHAIN_ID}) before sending a write.`);
      await submit(pending, connectedAddress);
      setPending(null); setDrawerOpen(true);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Write was not submitted.'); }
    finally { setBusy(false); }
  };
  return <span className="action-wrap">
    <button type="button" className={className} onClick={openConfirmation} disabled={busy}>{children}</button>
    {pending && <div className="modal-backdrop" role="presentation">
      <div className="confirmation-dialog" role="dialog" aria-modal="true" aria-labelledby="wallet-qa-title">
        <Kicker>REAL WALLET QA</Kicker>
        <h2 id="wallet-qa-title">Sign exact no-op</h2>
        <p>Review the immutable write descriptor before the wallet provider is called.</p>
        <div className="verdict-grid confirmation-grid">
          <DataRow label="Network" value={`${NETWORK} / ${CHAIN_ID}`} />
          <DataRow label="Contract" value={pending.contract} mono />
          <DataRow label="Method" value={pending.method} mono />
          <DataRow label="Case" value={String(pending.args[0])} mono />
          <DataRow label="max_steps" value={String(pending.args[1])} mono />
          <DataRow label="Expected return" value="u256(0)" />
          <DataRow label="Expected canonical mutation" value="NONE" />
          <DataRow label="Value" value="0 GEN" />
        </div>
        {error && <div className="field-error confirmation-error">{error}</div>}
        <div className="confirmation-actions">
          <button type="button" className="button button-secondary" disabled={busy} onClick={() => setPending(null)}>CANCEL</button>
          <button type="button" className="button button-primary" disabled={busy} onClick={() => void confirm()}>{busy ? 'WAITING FOR WALLET…' : 'SIGN EXACT NO-OP'}</button>
        </div>
      </div>
    </div>}
  </span>;
}

export function NodeRow({ node, onSelect }: { node: NodeRecord; onSelect?: () => void }) { return <button className="node-row" onClick={onSelect}><div><NodeBadge node={node} /><strong>{node.title}</strong><small>{node.subject_id || 'No subject identifier'}</small></div><div className="node-row-status"><StatusPill value={node.authentication_status} label={`AUTH ${formatStatus(node.authentication_status)}`} /><StatusPill value={node.reliance_status} label={formatStatus(node.reliance_status)} /><span className="mono">{truncate(node.node_id)}</span></div></button>; }

export function AddressLine({ value }: { value: string }) { return <span className="address-line mono">{truncate(value, 10, 8)} <CopyButton value={value} compact /></span>; }

export function ContractMeta() { return <div className="contract-meta"><DataRow label="Network" value={`${NETWORK} / ${CHAIN_ID}`} /><DataRow label="Contract" value={CONTRACT_ADDRESS} mono copy /><DataRow label="Frozen source" value={CONTRACT_SHA256} mono copy /><DataRow label="Freeze commit" value={FREEZE_COMMIT} mono copy /></div>; }
