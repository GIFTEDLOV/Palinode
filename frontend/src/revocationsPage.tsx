import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useProtocol } from './context';
import { OpenReviewForm } from './OpenReviewForm';
import { EmptyState, Kicker, PageHeader, StatusPill } from './components';
import { truncate } from './lib/utils';

export function RevocationsPage() {
  const { revocations } = useProtocol();
  const [open, setOpen] = useState(false);
  return <div className="page">
    <PageHeader eyebrow="REVIEW / REVOCATIONS" title="Review cases" intro="Source-authoritative notices and independent third-party challenges use different standing and result boundaries." action={<button className="button button-primary" onClick={() => setOpen((value) => !value)}>{open ? 'Close form' : 'Open review'}</button>} />
    {open && <OpenReviewForm onDone={() => setOpen(false)} />}
    <section className="case-list">{revocations.length ? revocations.map((item) => <Link className="case-card" to={`/app/revocations/${item.case_id}`} key={item.case_id}><div className="case-card-head"><Kicker>{item.notice_kind || 'AUTHORITATIVE SOURCE NOTICE'}</Kicker><StatusPill value={item.case_status} /></div><h3>{item.materiality || 'Awaiting consensus'} / {item.root_effect || 'UNASSESSED'}</h3><p>{truncate(item.target_evidence_id)} · {truncate(item.notice_authority_id || 'notice authority unavailable')}</p><div className="case-card-foot"><span>{item.reason_code || 'UNADJUDICATED'}</span><span>{item.case_status}</span></div></Link>) : <EmptyState title="No review cases" body="Canonical revocation and challenge cases will appear after a finalized opening write." />}</section>
  </div>;
}
