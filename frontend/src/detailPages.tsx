import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { CHAIN_ID, CONTRACT_ADDRESS, MAX_IMPACT_STEPS, NETWORK } from './config';
import { useProtocol } from './context';
import { loadAuthorityVersion, loadDirectAuthority, loadDirectNode, loadDirectRecovery, loadDirectRevocation, loadNodeViews } from './lib/client';
import { useCanonicalDetail } from './lib/detail';
import { truncate } from './lib/utils';
import type { NodeRecord, RawRecord } from './types';
import { ConfirmedWriteAction, DataRow, DetailLoadingState, DetailUnavailableState, Kicker, PageHeader, SectionTitle, StatusPill, WriteAction } from './components';
import { revocationActionState } from './lib/revocationActions';

function State({ detail, label }: { detail: { status: string; retry: () => void; record?: unknown }; label: string }) {
  if (detail.status === 'LOADING') return <div className="page"><DetailLoadingState label={label} /></div>;
  if (detail.status === 'DEGRADED') return <div className="page"><DetailUnavailableState label={label} retry={detail.retry} /></div>;
  return null;
}

function NotFound({ label }: { label: string }) {
  return <div className="page"><div className="empty-state"><div className="empty-mark">∅</div><h3>{label} not found</h3><p>The frozen V4 contract completed a canonical read and confirmed that this ID does not exist.</p></div></div>;
}

export function V4DecisionDetailPage() {
  const { id } = useParams();
  const { nodes } = useProtocol();
  const detail = useCanonicalDetail(id, nodes.find((node) => node.node_id === id), loadDirectNode);
  const state = State({ detail, label: 'decision record' });
  if (state) return state;
  if (detail.status === 'NOT_FOUND' || !detail.record) return <NotFound label="Decision" />;
  const node = detail.record;
  return <div className="page"><PageHeader eyebrow="DECISION / DETAIL" title={node.title} intro="Decision reliance is a canonical output of typed propagation, not generic graph reachability." /><section className="panel"><div className="verdict-grid"><DataRow label="Decision ID" value={node.node_id} mono copy /><DataRow label="Subject" value={node.subject_id} /><DataRow label="Authentication" value={node.authentication_status} /><DataRow label="Current reliance" value={node.reliance_status} /><DataRow label="Created" value={node.creation_sequence} /></div></section></div>;
}

export function V4EvidenceDetailPage() {
  const { id } = useParams();
  const { nodes, authorities } = useProtocol();
  const detail = useCanonicalDetail(id, nodes.find((node) => node.node_id === id), loadDirectNode);
  const node = detail.record;
  const [views, setViews] = useState<NodeRecord | null>(null);
  const [version, setVersion] = useState<RawRecord | null>(null);
  useEffect(() => {
    if (!node) return;
    void loadNodeViews(node).then(setViews).catch(() => setViews(node));
    if (node.authority_id && node.authority_version) void loadAuthorityVersion(node.authority_id, node.authority_version).then(setVersion).catch(() => setVersion(null));
  }, [node]);
  const state = State({ detail, label: 'evidence record' });
  if (state) return state;
  if (detail.status === 'NOT_FOUND' || !node) return <NotFound label="Evidence" />;
  const authority = authorities.find((item) => item.authority_id === node.authority_id);
  return <div className="page"><PageHeader eyebrow="EVIDENCE / CANONICAL DETAIL" title={node.title} intro="This record keeps immutable evidence identity, historical authority binding, authentication, and current reliance separate." /><div className="detail-grid"><section className="panel"><SectionTitle eyebrow="IMMUTABLE IDENTITY" title="Registered bytes" /><DataRow label="Evidence ID" value={node.node_id} mono copy /><DataRow label="Source URI" value={node.source_uri} /><DataRow label="SHA-256" value={node.content_sha256} mono copy /><DataRow label="Byte length" value={node.byte_length} /><DataRow label="Subject" value={node.subject_id} /><DataRow label="Creation sequence" value={node.creation_sequence} /></section><section className="panel"><SectionTitle eyebrow="HISTORICAL AUTHORITY BINDING" title="Version that authenticated this record" /><DataRow label="Source authority" value={node.authority_id} mono copy /><DataRow label="Bound version" value={node.authority_version ? 'V' + node.authority_version : undefined} /><DataRow label="Version controller" value={version?.controller || version?.authority_address || 'Read exact historical version'} mono /><DataRow label="Version status" value={version?.status || 'Historical version read'} /><div className="historical-callout">Current authority state is shown separately: <strong>{authority?.status || 'unavailable'} / V{authority?.current_version || '—'}</strong>. It does not replace the bound historical version.</div></section></div><section className="panel"><SectionTitle eyebrow="AUTHENTICATION ≠ RELIANCE" title="Current canonical state" /><div className="verdict-grid"><DataRow label="Authentication" value={node.authentication_status} /><DataRow label="Reliance" value={node.reliance_status} /><DataRow label="Assessment" value={node.assessment_status} /><DataRow label="Successor" value={node.successor_evidence_id} mono /></div></section>{views && <section className="panel"><SectionTitle eyebrow="V4 BOUNDED VIEWS" title="Evidence history and causes" /><div className="verdict-grid"><DataRow label="Active causes" value={views.get_active_causes_active_count || '0'} /><DataRow label="Questioned causes" value={views.get_active_causes_questioned_count || '0'} /><DataRow label="Cause slots" value={views.get_active_causes_slot_count || '0'} /></div></section>}</div>;
}

export function V4RevocationDetailPageLegacy() {
  const { id } = useParams();
  const { revocations, nodes } = useProtocol();
  const detail = useCanonicalDetail(id, revocations.find((item) => item.case_id === id), loadDirectRevocation);
  const state = State({ detail, label: 'review case' });
  if (state) return state;
  if (detail.status === 'NOT_FOUND' || !detail.record) return <NotFound label="Review case" />;
  const item = detail.record;
  const target = nodes.find((node) => node.node_id === item.target_evidence_id);
  const thirdParty = item.notice_kind === 'THIRD_PARTY_CHALLENGE' || item.reason_code === 'MATERIAL_THIRD_PARTY_CHALLENGE';
  return <div className="page"><PageHeader eyebrow={thirdParty ? 'REVIEW / THIRD-PARTY CHALLENGE' : 'REVIEW / SOURCE NOTICE'} title={thirdParty ? 'Independent challenge' : 'Source-authoritative review'} intro={thirdParty ? 'A separate authority may materially question reliance, but cannot impersonate publisher withdrawal or receive deterministic INVALIDATE power.' : 'Authoritative withdrawal requires standing from the target evidence authority lineage.'} /><div className="detail-grid"><section className="panel"><SectionTitle eyebrow="CASE RESULT" title={target?.title || truncate(item.target_evidence_id)} /><div className="state-pair"><span><small>AUTHENTICATION</small><StatusPill value={item.target_authentication_status} /></span><span><small>RELIANCE</small><StatusPill value={item.target_reliance_status} /></span></div><div className="verdict-grid"><DataRow label="Case ID" value={item.case_id} mono copy /><DataRow label="Case status" value={item.case_status} /><DataRow label="Result" value={item.result_status} /><DataRow label="Materiality" value={item.materiality} /><DataRow label="Root effect" value={item.root_effect} /><DataRow label="Reason" value={item.reason_code} /></div><div className="case-actions"><WriteAction label="Assess review" method="assess_revocation" args={[item.case_id]} validationError={item.target_authentication_status !== 'CLEARED' ? 'Semantic review is unavailable until authentication is CLEARED.' : undefined}>Assess consensus</WriteAction>{item.case_status === 'PROPAGATING' && <WriteAction label="Process impact" method="process_impact" args={[item.case_id, MAX_IMPACT_STEPS]}>Process impact</WriteAction>}</div></section><section className="panel"><SectionTitle eyebrow="NOTICE STANDING" title={thirdParty ? 'Third-party challenge' : 'Authoritative source notice'} /><DataRow label="Notice authority" value={item.notice_authority_id} mono copy /><DataRow label="Notice version" value={item.notice_authority_version ? 'V' + item.notice_authority_version : undefined} /><DataRow label="Notice URI" value={item.notice_uri} /><DataRow label="Notice SHA-256" value={item.notice_sha256} mono copy /><DataRow label="Standing guard" value={thirdParty ? 'INVALIDATE not allowed' : 'Source lineage required'} /><div className="challenge-callout">{thirdParty ? 'MATERIAL_THIRD_PARTY_CHALLENGE can produce QUESTION when consensus finds material undermining. It is not publisher revocation.' : 'MATERIAL_WITHDRAWAL is reserved for the target source authority lineage.'}</div></section></div>{item.case_status === 'COMPLETE' && <section className="panel safe-wallet-panel"><SectionTitle eyebrow="OPERATOR WALLET SMOKE" title="Completed-case state-neutral write" /><p>This exact V4 operation returns zero before queue/status/history mutation when the case is COMPLETE. Approve it only once from a real EIP-1193 wallet.</p><div className="verdict-grid"><DataRow label="Network" value={NETWORK + ' / ' + CHAIN_ID} /><DataRow label="Contract" value={CONTRACT_ADDRESS} mono /><DataRow label="Method" value="process_impact" mono /><DataRow label="Arguments" value={item.case_id + ', 1'} mono /><DataRow label="Expected effect" value="u256(0) · no canonical state change" /><DataRow label="Value" value="0 GEN" /><DataRow label="SDK fee estimate" value="Requested by genlayer-js immediately before wallet approval" /></div><WriteAction label="Process completed case" method="process_impact" args={[item.case_id, 1]}>Approve one safe no-op write</WriteAction></section>}</div>;
}

export function V4RecoveryDetailPageLegacy() {
  const { id } = useParams();
  const { recoveries, nodes } = useProtocol();
  const detail = useCanonicalDetail(id, recoveries.find((item) => item.recovery_id === id), loadDirectRecovery);
  const state = State({ detail, label: 'recovery case' });
  if (state) return state;
  if (detail.status === 'NOT_FOUND' || !detail.record) return <NotFound label="Recovery case" />;
  const item = detail.record;
  const affected = nodes.find((node) => node.node_id === item.affected_node_id);
  const successor = nodes.find((node) => node.node_id === item.successor_evidence_id);
  return <div className="page"><PageHeader eyebrow="RECOVERY / COMMAND CENTER" title="Recovery command center" intro="Recovery changes current reliance only through the matching cause. History is retained." /><div className="recovery-path"><div className="path-card old"><Kicker>ORIGINAL</Kicker><h3>{affected?.title || truncate(item.affected_node_id)}</h3><StatusPill value={affected?.reliance_status || item.target_reliance_status} /></div><div className="path-arrow">→<span>EXPLICIT SUCCESSOR</span></div><div className="path-card new"><Kicker>SUCCESSOR</Kicker><h3>{successor?.title || truncate(item.successor_evidence_id)}</h3><StatusPill value={successor?.authentication_status} /></div></div><section className="panel"><SectionTitle eyebrow="RECOVERY CONSENSUS" title="Resolution" /><div className="verdict-grid"><DataRow label="Recovery ID" value={item.recovery_id} mono copy /><DataRow label="Result" value={item.result_status} /><DataRow label="Effect" value={item.recovery_effect} /><DataRow label="Reason" value={item.reason_code} /><DataRow label="Case status" value={item.case_status} /></div><div className="case-actions"><WriteAction label="Assess recovery" method="assess_recovery" args={[item.recovery_id]} validationError={item.case_status === 'COMPLETE' ? 'Recovery is already complete.' : undefined}>Assess recovery</WriteAction></div></section></div>;
}

export function V4RevocationDetailPage() {
  const { id } = useParams();
  const { revocations, nodes } = useProtocol();
  const detail = useCanonicalDetail(id, revocations.find((item) => item.case_id === id), loadDirectRevocation);
  const state = State({ detail, label: 'review case' });
  if (state) return state;
  if (detail.status === 'NOT_FOUND' || !detail.record) return <NotFound label="Review case" />;
  const item = detail.record;
  const target = nodes.find((node) => node.node_id === item.target_evidence_id);
  const thirdParty = item.notice_kind === 'THIRD_PARTY_CHALLENGE' || item.reason_code === 'MATERIAL_THIRD_PARTY_CHALLENGE';
  const actions = revocationActionState(item);
  return <div className="page">
    <PageHeader eyebrow={thirdParty ? 'REVIEW / THIRD-PARTY CHALLENGE' : 'REVIEW / SOURCE NOTICE'} title={thirdParty ? 'Independent challenge' : 'Source-authoritative review'} intro={thirdParty ? 'A separate authority may materially question reliance, but cannot impersonate publisher withdrawal or receive deterministic INVALIDATE power.' : 'Authoritative withdrawal requires standing from the target evidence authority lineage.'} />
    <div className="detail-grid">
      <section className="panel">
        <SectionTitle eyebrow="CASE RESULT" title={target?.title || truncate(item.target_evidence_id)} />
        <div className="state-pair"><span><small>AUTHENTICATION</small><StatusPill value={item.target_authentication_status} /></span><span><small>RELIANCE</small><StatusPill value={item.target_reliance_status} /></span></div>
        <div className="verdict-grid"><DataRow label="Case ID" value={item.case_id} mono copy /><DataRow label="Case status" value={item.case_status} /><DataRow label="Result" value={item.result_status} /><DataRow label="Materiality" value={item.materiality} /><DataRow label="Root effect" value={item.root_effect} /><DataRow label="Reason" value={item.reason_code} /></div>
        <div className="case-actions">
          {actions.canAssess && <WriteAction label="Assess review" method="assess_revocation" args={[item.case_id]} validationError={item.target_authentication_status !== 'CLEARED' ? 'Semantic review is unavailable until authentication is CLEARED.' : undefined}>Assess consensus</WriteAction>}
          {actions.canRetry && <WriteAction label="Retry review" method="retry_revocation_case" args={[item.case_id, '', '']} className="button button-secondary">Retry review</WriteAction>}
          {actions.canProcessImpact && <WriteAction label="Process impact" method="process_impact" args={[item.case_id, MAX_IMPACT_STEPS]}>Process impact</WriteAction>}
          {actions.isComplete && <div className="case-finalized-note"><Kicker>CASE FINALIZED</Kicker><p>No further semantic assessment is available.</p></div>}
        </div>
      </section>
      <section className="panel"><SectionTitle eyebrow="NOTICE STANDING" title={thirdParty ? 'Third-party challenge' : 'Authoritative source notice'} /><DataRow label="Notice authority" value={item.notice_authority_id} mono copy /><DataRow label="Notice version" value={item.notice_authority_version ? 'V' + item.notice_authority_version : undefined} /><DataRow label="Notice URI" value={item.notice_uri} /><DataRow label="Notice SHA-256" value={item.notice_sha256} mono copy /><DataRow label="Standing guard" value={thirdParty ? 'INVALIDATE not allowed' : 'Source lineage required'} /><div className="challenge-callout">{thirdParty ? 'MATERIAL_THIRD_PARTY_CHALLENGE can produce QUESTION when consensus finds material undermining. It is not publisher revocation.' : 'MATERIAL_WITHDRAWAL is reserved for the target source authority lineage.'}</div></section>
    </div>
    {actions.isComplete && <section className="panel safe-wallet-panel"><SectionTitle eyebrow="OPERATOR WALLET SMOKE" title="Completed-case state-neutral write" /><p>This exact V4 operation returns zero before queue/status/history mutation when the case is COMPLETE. Approve it only once from a real EIP-1193 wallet.</p><div className="verdict-grid"><DataRow label="Network" value={NETWORK + ' / ' + CHAIN_ID} /><DataRow label="Contract" value={CONTRACT_ADDRESS} mono /><DataRow label="Method" value="process_impact" mono /><DataRow label="Case" value={item.case_id} mono /><DataRow label="max_steps" value="1" mono /><DataRow label="Expected return" value="u256(0)" /><DataRow label="Expected canonical mutation" value="NONE" /><DataRow label="Value" value="0 GEN" /><DataRow label="SDK fee estimate" value="Requested by genlayer-js immediately before wallet approval" /></div><ConfirmedWriteAction label="Process completed case" method="process_impact" args={[item.case_id, 1]} safeCaseId={item.case_id}>Approve one safe no-op write</ConfirmedWriteAction></section>}
  </div>;
}

export function V4RecoveryDetailPage() {
  const { id } = useParams();
  const { recoveries, nodes } = useProtocol();
  const detail = useCanonicalDetail(id, recoveries.find((item) => item.recovery_id === id), loadDirectRecovery);
  const state = State({ detail, label: 'recovery case' });
  if (state) return state;
  if (detail.status === 'NOT_FOUND' || !detail.record) return <NotFound label="Recovery case" />;
  const item = detail.record;
  const affected = nodes.find((node) => node.node_id === item.affected_node_id);
  const successor = nodes.find((node) => node.node_id === item.successor_evidence_id);
  const complete = item.case_status === 'COMPLETE';
  return <div className="page"><PageHeader eyebrow="RECOVERY / COMMAND CENTER" title="Recovery command center" intro="Recovery changes current reliance only through the matching cause. History is retained." /><div className="recovery-path"><div className="path-card old"><Kicker>ORIGINAL</Kicker><h3>{affected?.title || truncate(item.affected_node_id)}</h3><StatusPill value={affected?.reliance_status || item.target_reliance_status} /></div><div className="path-arrow">→<span>EXPLICIT SUCCESSOR</span></div><div className="path-card new"><Kicker>SUCCESSOR</Kicker><h3>{successor?.title || truncate(item.successor_evidence_id)}</h3><StatusPill value={successor?.authentication_status} /></div></div><section className="panel"><SectionTitle eyebrow="RECOVERY CONSENSUS" title="Resolution" /><div className="verdict-grid"><DataRow label="Recovery ID" value={item.recovery_id} mono copy /><DataRow label="Result" value={item.result_status} /><DataRow label="Effect" value={item.recovery_effect} /><DataRow label="Reason" value={item.reason_code} /><DataRow label="Case status" value={item.case_status} /></div><div className="case-actions">{!complete && <WriteAction label="Assess recovery" method="assess_recovery" args={[item.recovery_id]}>Assess recovery</WriteAction>}{complete && <div className="case-finalized-note"><Kicker>CASE FINALIZED</Kicker><p>No further semantic assessment is available.</p></div>}</div></section></div>;
}

export function V4AuthorityDetailPage() {
  const { id } = useParams();
  const { authorities, nodes } = useProtocol();
  const detail = useCanonicalDetail(id, authorities.find((item) => item.authority_id === id), loadDirectAuthority);
  const authority = detail.record;
  const [versions, setVersions] = useState<RawRecord[]>([]);
  useEffect(() => {
    if (!authority) return;
    void import('./lib/client').then(({ loadAuthorityViews }) => loadAuthorityViews(authority)).then((record) => {
      setVersions(Object.entries(record).filter(([key]) => key.startsWith('authority_versions_slot_')).map(([, value]) => ({ version: value })));
    }).catch(() => setVersions([]));
  }, [authority]);
  const state = State({ detail, label: 'authority record' });
  if (state) return state;
  if (detail.status === 'NOT_FOUND' || !authority) return <NotFound label="Authority" />;
  const bound = nodes.filter((node) => node.authority_id === authority.authority_id);
  return <div className="page"><PageHeader eyebrow="TRUST / AUTHORITY RECORD" title={authority.canonical_origin} intro="Evidence is bound to the historical authority version under which it was authenticated." /><div className="detail-grid"><section className="panel"><SectionTitle eyebrow="CURRENT AUTHORITY STATE" title="Binding" /><DataRow label="Authority ID" value={authority.authority_id} mono copy /><DataRow label="Current controller" value={authority.authority_address} mono copy /><DataRow label="Current version" value={'V' + authority.current_version} /><DataRow label="Status" value={authority.status} /><DataRow label="Policy" value={authority.verification_policy} /></section><section className="panel"><SectionTitle eyebrow="VERSION HISTORY" title="Historical bindings" />{versions.length ? versions.map((record, index) => <div className="history-line" key={record.version + '-' + index}><span>V{record.version}</span><code>Use evidence detail to read exact controller/status.</code></div>) : <p className="muted">No version page entries were returned.</p>}<p className="muted">Current metadata is never substituted for a historical evidence binding.</p></section></div><section className="panel"><SectionTitle eyebrow="BOUND EVIDENCE" title={bound.length + ' evidence records'} />{bound.length ? bound.map((node) => <div key={node.node_id}><DataRow label={node.title} value={node.node_id} mono copy /></div>) : <p className="muted">This authority is not referenced by a node in the current read model.</p>}</section></div>;
}
