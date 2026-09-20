import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { loadCaseViews, loadNodeViews, loadRecoveryViews } from './lib/client';
import { useProtocol } from './context';
import type { NodeRecord, RawRecord } from './types';
import { DataRow, Kicker, SectionTitle } from './components';

function slots(record: RawRecord, prefix: string) {
  return Object.entries(record).filter(([key]) => key.startsWith(`${prefix}_slot_`)).sort(([left], [right]) => left.localeCompare(right, undefined, { numeric: true })).map(([, value]) => value);
}

function BoundedSlots({ record, prefix, title }: { record: RawRecord; prefix: string; title: string }) {
  const values = slots(record, prefix);
  return <div className="bounded-history"><Kicker>{title}</Kicker>{values.length ? values.map((value, index) => <div className="history-line" key={`${prefix}-${index}`}><span>{index + 1}</span><code>{value}</code></div>) : <span className="muted">No recent entries.</span>}</div>;
}

function ViewError({ message }: { message: string }) { return <div className="inline-alert warning">DETAIL VIEW UNAVAILABLE: {message}</div>; }

export function EvidenceCanonicalViews() {
  const { id } = useParams(); const { nodes } = useProtocol(); const node = nodes.find((item) => item.node_id === id); const [record, setRecord] = useState<NodeRecord | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!node) return; let mounted = true; void loadNodeViews(node).then((value) => { if (mounted) setRecord(value); }).catch((reason) => { if (mounted) setError(reason instanceof Error ? reason.message : 'The bounded evidence views could not be read.'); }); return () => { mounted = false; }; }, [node]);
  if (!node) return null;
  if (error) return <ViewError message={error} />;
  if (!record) return <section className="panel detail-supplement"><Kicker>BOUNDED CANONICAL VIEWS</Kicker><p className="muted">Loading status history, assessment history, active causes, and verified mirrors…</p></section>;
  return <section className="panel detail-supplement"><SectionTitle eyebrow="BOUNDED CANONICAL VIEWS" title="History and retrieval" /><div className="verdict-grid"><DataRow label="Active causes" value={record.get_active_causes_active_count || '0'} /><DataRow label="Cause slots" value={record.get_active_causes_slot_count || '0'} /><DataRow label="Overflow causes" value={record.get_active_causes_overflow_count || '0'} /><DataRow label="Verified mirrors" value={record.get_evidence_mirrors_items || '[]'} /></div><div className="history-grid"><BoundedSlots record={record} prefix="get_status_history" title="STATUS HISTORY" /><BoundedSlots record={record} prefix="get_assessment_history" title="AUTHENTICATION HISTORY" /></div></section>;
}

export function RevocationCanonicalViews() {
  const { id } = useParams(); const { revocations } = useProtocol(); const item = revocations.find((entry) => entry.case_id === id); const [record, setRecord] = useState<RawRecord | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!item) return; let mounted = true; void loadCaseViews(item).then((value) => { if (mounted) setRecord(value); }).catch((reason) => { if (mounted) setError(reason instanceof Error ? reason.message : 'The bounded revocation views could not be read.'); }); return () => { mounted = false; }; }, [item]);
  if (!item) return null; if (error) return <ViewError message={error} />; if (!record) return <section className="panel detail-supplement"><Kicker>IMPACT QUEUE</Kicker><p className="muted">Loading canonical queue state…</p></section>;
  return <section className="panel detail-supplement"><SectionTitle eyebrow="CANONICAL QUEUE VIEWS" title="Impact processing" /><div className="verdict-grid"><DataRow label="Queue status" value={record.impact_queue_status} /><DataRow label="Cursor" value={record.impact_queue_cursor} /><DataRow label="Remaining" value={record.impact_queue_remaining} /><DataRow label="Retry count" value={record.retry_telemetry_retry_count} /><DataRow label="Notice mirrors" value={record.notice_mirrors_items || '[]'} /></div></section>;
}

export function RecoveryCanonicalViews() {
  const { id } = useParams(); const { recoveries } = useProtocol(); const item = recoveries.find((entry) => entry.recovery_id === id); const [record, setRecord] = useState<RawRecord | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!item) return; let mounted = true; void loadRecoveryViews(item).then((value) => { if (mounted) setRecord(value); }).catch((reason) => { if (mounted) setError(reason instanceof Error ? reason.message : 'The bounded recovery views could not be read.'); }); return () => { mounted = false; }; }, [item]);
  if (!item) return null; if (error) return <ViewError message={error} />; if (!record) return <section className="panel detail-supplement"><Kicker>RECOVERY QUEUE</Kicker><p className="muted">Loading canonical recovery queue state…</p></section>;
  return <section className="panel detail-supplement"><SectionTitle eyebrow="CANONICAL RECOVERY VIEWS" title="Bounded recovery processing" /><div className="verdict-grid"><DataRow label="Queue status" value={record.recovery_queue_status} /><DataRow label="Cursor" value={record.recovery_queue_cursor} /><DataRow label="Remaining" value={record.recovery_queue_remaining} /><DataRow label="Retry count" value={record.recovery_retry_telemetry_retry_count} /></div></section>;
}
