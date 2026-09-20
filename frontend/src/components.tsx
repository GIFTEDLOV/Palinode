import { useState } from 'react';
import { NavLink, Outlet, Link, useLocation } from 'react-router-dom';
import { CONTRACT_ADDRESS, CONTRACT_SHA256, NETWORK, CHAIN_ID, FREEZE_COMMIT } from './config';
import { useProtocol, useTransactions, useWallet } from './context';
import { formatDate, formatStatus, statusClass, truncate } from './lib/utils';
import type { NodeRecord } from './types';
import type { CalldataEncodable } from 'genlayer-js/types';

export function StatusPill({ value, label }: { value?: string; label?: string }) { return <span className={statusClass(value)}>{label || formatStatus(value)}</span>; }
export function CopyButton({ value, compact = false }: { value: string; compact?: boolean }) {
  const [copied, setCopied] = useState(false);
  return <button className={compact ? 'copy-button compact' : 'copy-button'} title="Copy value" onClick={() => { void navigator.clipboard.writeText(value).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1200); }); }}>{copied ? 'COPIED' : compact ? '⧉' : 'COPY'}</button>;
}
export function Kicker({ children }: { children: React.ReactNode }) { return <div className="kicker">{children}</div>; }
export function SectionTitle({ eyebrow, title, action }: { eyebrow?: string; title: string; action?: React.ReactNode }) { return <div className="section-title"><div>{eyebrow && <Kicker>{eyebrow}</Kicker>}<h2>{title}</h2></div>{action}</div>; }
export function PageHeader({ eyebrow, title, intro, action }: { eyebrow: string; title: string; intro?: string; action?: React.ReactNode }) { return <header className="page-header"><div><Kicker>{eyebrow}</Kicker><h1>{title}</h1>{intro && <p>{intro}</p>}</div>{action && <div className="page-header-action">{action}</div>}</header>; }
export function EmptyState({ title, body, action }: { title: string; body: string; action?: React.ReactNode }) { return <div className="empty-state"><div className="empty-mark">∅</div><h3>{title}</h3><p>{body}</p>{action}</div>; }
export function ErrorState({ message, retry }: { message: string; retry?: () => void }) { return <div className="error-state"><Kicker>CANONICAL READ ERROR</Kicker><h3>Studionet is not responding</h3><p>{message}</p>{retry && <button className="button button-secondary" onClick={retry}>Retry read</button>}</div>; }
export function Metric({ label, value, note, tone = '' }: { label: string; value: string | number; note?: string; tone?: string }) { return <div className={`metric ${tone}`}><div className="metric-label">{label}</div><div className="metric-value">{value}</div>{note && <div className="metric-note">{note}</div>}</div>; }
export function DataRow({ label, value, mono = false, copy = false }: { label: string; value?: string; mono?: boolean; copy?: boolean }) { const display = value || '—'; return <div className="data-row"><span>{label}</span><strong className={mono ? 'mono' : ''}>{display}</strong>{copy && value && <CopyButton value={value} compact />}</div>; }
export function NodeBadge({ node }: { node: NodeRecord }) { return <span className={`node-badge node-${node.node_type.toLowerCase()}`}>{node.node_type}</span>; }

function navClass({ isActive }: { isActive: boolean }) { return isActive ? 'nav-link active' : 'nav-link'; }

export function AppShell() {
  const { address, connecting, connect, disconnect, error: walletError } = useWallet();
  const { nodes, revocations, recoveries, loading, error, refresh } = useProtocol();
  const { transactions, drawerOpen, setDrawerOpen } = useTransactions();
  const location = useLocation();
  const activeTx = transactions.filter((tx) => !['FINALIZED SUCCESS', 'FINALIZED ERROR', 'UNDETERMINED'].includes(tx.phase));
  return <div className="app-frame">
    <header className="topbar">
      <Link className="brand" to="/"><span className="brand-mark">P</span><span>PALINODE</span><small>REVOCATION GRAPH</small></Link>
      <div className="topbar-right"><span className="network-chip"><i />{NETWORK} / {CHAIN_ID}</span><button className="wallet-button" onClick={address ? disconnect : () => void connect()}>{connecting ? 'CONNECTING…' : address ? truncate(address) : 'CONNECT WALLET'}</button><button className="icon-button" aria-label="Open transaction drawer" onClick={() => setDrawerOpen(true)}>◌<b>{activeTx.length || ''}</b></button></div>
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
        {error && !loading && <ErrorState message={error} retry={() => void refresh()} />}
        {location.pathname.startsWith('/app') && <div className="breadcrumb"><span>PALINODE</span><b>/</b><span>{location.pathname.split('/').filter(Boolean).slice(1).join(' / ') || 'overview'}</span>{loading && <em>SYNCING CANONICAL STATE…</em>}</div>}
        <Outlet />
      </main>
    </div>
    {drawerOpen && <TransactionDrawer onClose={() => setDrawerOpen(false)} />}
  </div>;
}

export function TransactionDrawer({ onClose }: { onClose: () => void }) {
  const { transactions } = useTransactions();
  return <div className="drawer-backdrop" onClick={onClose}><aside className="transaction-drawer" onClick={(event) => event.stopPropagation()}><div className="drawer-header"><div><Kicker>FINALITY TRACKER</Kicker><h2>Transactions</h2></div><button className="icon-button" onClick={onClose}>×</button></div>{transactions.length === 0 ? <EmptyState title="No tracked transactions" body="Writes submitted from this browser will persist here and resume by ID after refresh." /> : <div className="tx-list">{transactions.map((tx) => <TransactionItem key={tx.id} tx={tx} />)}</div>}</aside></div>;
}

function TransactionItem({ tx }: { tx: import('./types').TrackedTransaction }) { return <div className="tx-item"><div className="tx-item-head"><strong>{tx.label}</strong><StatusPill value={tx.phase} /></div><div className="tx-method">{tx.method}</div><div className="tx-id mono">{truncate(tx.id, 14, 10)} <CopyButton value={tx.id} compact /></div><div className="tx-progress"><span className={tx.phase.includes('FINALIZED SUCCESS') ? 'done' : tx.phase.includes('ERROR') || tx.phase === 'UNDETERMINED' ? 'bad' : 'current'} /></div><div className="tx-meta"><span>{tx.protocolStatus}</span><span>{tx.executionResult}</span><span>{formatDate(tx.updatedAt)}</span></div>{tx.error && <div className="tx-error">{tx.error}</div>}</div>; }

export function LiveContractStrip() { return <div className="live-strip"><span className="live-dot" /> LIVE CANONICAL STATE <span className="strip-divider" /> {NETWORK} <span className="strip-divider" /> <span className="mono">{truncate(CONTRACT_ADDRESS, 10, 8)}</span> <span className="strip-divider" /> <span className="mono">SHA {truncate(CONTRACT_SHA256, 8, 6)}</span></div>; }

export function WriteAction({ label, method, args, children, className = 'button button-primary', onSubmitted }: { label: string; method: string; args: CalldataEncodable[]; children: React.ReactNode; className?: string; onSubmitted?: () => void }) {
  const { address, connect } = useWallet();
  const { submit, setDrawerOpen } = useTransactions();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const run = async () => {
    setBusy(true); setError(null);
    try { const connectedAddress = address || await connect(); if (!connectedAddress) throw new Error('Connect a wallet before sending a write.'); await submit(label, method, args, connectedAddress); onSubmitted?.(); setDrawerOpen(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Write was not submitted.'); }
    finally { setBusy(false); }
  };
  return <span className="action-wrap"><button type="button" className={className} disabled={busy} onClick={() => void run()}>{busy ? 'SUBMITTING…' : children}</button>{error && <small className="field-error">{error}</small>}</span>;
}

export function NodeRow({ node, onSelect }: { node: NodeRecord; onSelect?: () => void }) { return <button className="node-row" onClick={onSelect}><div><NodeBadge node={node} /><strong>{node.title}</strong><small>{node.subject_id || 'No subject identifier'}</small></div><div className="node-row-status"><StatusPill value={node.authentication_status} label={`AUTH ${formatStatus(node.authentication_status)}`} /><StatusPill value={node.reliance_status} label={formatStatus(node.reliance_status)} /><span className="mono">{truncate(node.node_id)}</span></div></button>; }

export function AddressLine({ value }: { value: string }) { return <span className="address-line mono">{truncate(value, 10, 8)} <CopyButton value={value} compact /></span>; }

export function ContractMeta() { return <div className="contract-meta"><DataRow label="Network" value={`${NETWORK} / ${CHAIN_ID}`} /><DataRow label="Contract" value={CONTRACT_ADDRESS} mono copy /><DataRow label="Frozen source" value={CONTRACT_SHA256} mono copy /><DataRow label="Freeze commit" value={FREEZE_COMMIT} mono copy /></div>; }
