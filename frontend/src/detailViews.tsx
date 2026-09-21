import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { loadCaseViews, loadNodeViews, loadRecoveryViews } from './lib/client';
import { useProtocol } from './context';
import type { NodeRecord, RawRecord } from './types';
import { DataRow, Kicker, SectionTitle } from './components';

function values(record: RawRecord, prefix: string) {
  return Object.entries(record).filter(([key]) => key.startsWith(`${prefix}_slot_`)).sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true })).map(([, value]) => value);
}
function History({ record, prefix, title }: { record: RawRecord; prefix: string; title: string }) { const entries = values(record, prefix); return <div className="bounded-history"><Kicker>{title}</Kicker>{entries.length ? entries.map((value, index) => <div className="history-line" key={`${prefix}-${index}`}><span>{index + 1}</span><code>{value}</code></div>) : <span className="muted">No recent entries.</span>}</div>; }
function Loading({ label }: { label: string }) { return <section className="panel detail-supplement"><Kicker>BOUNDED CANONICAL VIEWS</Kicker><p className="muted">Loading {label}…</p></section>; }
function Failure({ message }: { message: string }) { return <div className="inline-alert warning">DETAIL VIEW UNAVAILABLE: {message}</div>; }

export function EvidenceCanonicalViews() {
  const { id } = useParams(); const { nodes } = useProtocol(); const node = nodes.find((item) => item.node_id === id); const [record, setRecord] = useState<NodeRecord | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!node) return; let alive = true; void loadNodeViews(node).then((value) => { if (alive) setRecord(value); }).catch((reason) => { if (alive) setError(reason instanceof Error ? reason.message : 'The bounded evidence views could not be read.'); }); return () => { alive = false; }; }, [node]);
  if (!node) return null; if (error) return <Failure message={error} />; if (!record) return <Loading label="status history, assessment history, active causes, and mirrors" />;
  return <section className="panel detail-supplement"><SectionTitle eyebrow="V4 BOUNDED VIEWS" title="Evidence history and causes" /><div className="verdict-grid"><DataRow label="Active causes" value={record.get_active_causes_active_count || '0'} /><DataRow label="Questioned causes" value={record.get_active_causes_questioned_count || '0'} /><DataRow label="Cause slots" value={record.get_active_causes_slot_count || '0'} /><DataRow label="Verified mirrors" value={record.get_evidence_mirrors_items || '[]'} /></div><div className="history-grid"><History record={record} prefix="get_active_causes_page" title="ACTIVE CAUSE SLOTS" /><History record={record} prefix="get_status_history" title="STATUS HISTORY" /><History record={record} prefix="get_assessment_history" title="ASSESSMENT HISTORY" /><History record={record} prefix="successor_link" title="LINEAGE PROVENANCE" /></div></section>;
}

export function RevocationCanonicalViews() {
  const { id } = useParams(); const { revocations } = useProtocol(); const item = revocations.find((entry) => entry.case_id === id); const [record, setRecord] = useState<RawRecord | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!item) return; let alive = true; void loadCaseViews(item).then((value) => { if (alive) setRecord(value); }).catch((reason) => { if (alive) setError(reason instanceof Error ? reason.message : 'The bounded review views could not be read.'); }); return () => { alive = false; }; }, [item]);
  if (!item) return null; if (error) return <Failure message={error} />; if (!record) return <Loading label="impact queue, result history, retry telemetry, and mirrors" />;
  return <section className="panel detail-supplement"><SectionTitle eyebrow="V4 CANONICAL QUEUE VIEWS" title="Impact processing" /><div className="verdict-grid"><DataRow label="Queue status" value={record.impact_queue_status} /><DataRow label="Cursor" value={record.impact_queue_cursor} /><DataRow label="Remaining" value={record.impact_queue_remaining} /><DataRow label="Retry count" value={record.retry_telemetry_retry_count} /><DataRow label="Notice mirrors" value={record.notice_mirrors_items || '[]'} /></div><History record={record} prefix="case_result_history" title="CASE RESULT HISTORY" /></section>;
}

export function RecoveryCanonicalViews() {
  const { id } = useParams(); const { recoveries } = useProtocol(); const item = recoveries.find((entry) => entry.recovery_id === id); const [record, setRecord] = useState<RawRecord | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!item) return; let alive = true; void loadRecoveryViews(item).then((value) => { if (alive) setRecord(value); }).catch((reason) => { if (alive) setError(reason instanceof Error ? reason.message : 'The bounded recovery views could not be read.'); }); return () => { alive = false; }; }, [item]);
  if (!item) return null; if (error) return <Failure message={error} />; if (!record) return <Loading label="recovery queue, result history, and retry telemetry" />;
  return <section className="panel detail-supplement"><SectionTitle eyebrow="V4 CANONICAL RECOVERY VIEWS" title="Bounded recovery processing" /><div className="verdict-grid"><DataRow label="Queue status" value={record.recovery_queue_status} /><DataRow label="Cursor" value={record.recovery_queue_cursor} /><DataRow label="Remaining" value={record.recovery_queue_remaining} /><DataRow label="Retry count" value={record.recovery_retry_telemetry_retry_count} /></div><History record={record} prefix="recovery_result_history" title="RECOVERY RESULT HISTORY" /></section>;
}
