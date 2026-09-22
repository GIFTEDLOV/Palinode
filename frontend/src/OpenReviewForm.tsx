import { useState } from 'react';
import { CASE_REASON_CODES, MAX_DECLARED_SOURCE_BYTES, MAX_REASON_NOTE_LENGTH } from './config';
import { useProtocol } from './context';
import { Kicker, WriteAction } from './components';
import { buildOpenRevocationCaseCall, type OpenReviewFormValues, validateOpenReview } from './lib/revocationOpening';

const EMPTY_FORM: OpenReviewFormValues = {
  targetEvidenceId: '', noticeAuthorityId: '', noticeUri: '', noticeSha256: '', noticeByteLength: '', openingReasonCode: CASE_REASON_CODES[0], openingNote: '',
};

function FormField({ label, value, onChange, placeholder, mono = false, type = 'text' }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string; mono?: boolean; type?: string }) {
  return <label className="field"><span>{label}<i>*</i></span><input className={mono ? 'mono' : ''} type={type} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} /></label>;
}

export function OpenReviewForm({ onDone }: { onDone: () => void }) {
  const { nodes, authorities } = useProtocol();
  const [values, setValues] = useState<OpenReviewFormValues>(EMPTY_FORM);
  const update = (key: keyof OpenReviewFormValues) => (value: string) => setValues((current) => ({ ...current, [key]: value }));
  const error = validateOpenReview(values, { nodes, authorities });
  const target = nodes.find((node) => node.node_id.toLowerCase() === values.targetEvidenceId.trim().toLowerCase());
  const noticeAuthority = authorities.find((authority) => authority.authority_id.toLowerCase() === values.noticeAuthorityId.trim().toLowerCase());
  const call = buildOpenRevocationCaseCall(values);
  const noticeKind = target?.authority_id && noticeAuthority?.authority_id && target.authority_id.toLowerCase() === noticeAuthority.authority_id.toLowerCase()
    ? 'SOURCE-AUTHORITATIVE REVIEW' : target && noticeAuthority ? 'THIRD-PARTY CHALLENGE' : null;
  const reset = () => { setValues(EMPTY_FORM); onDone(); };

  return <form className="form-card open-review-form" onSubmit={(event) => event.preventDefault()}>
    <Kicker>CANONICAL REVIEW WRITE</Kicker>
    <h3>Open review</h3>
    <p className="form-help">Submit the registered notice identity exactly as stored by the frozen V4 contract. The target must be CLEARED evidence. Notice standing is inferred from the notice authority; the contract remains authoritative.</p>
    {noticeKind && <div className="challenge-callout"><strong>{noticeKind}</strong><br />{noticeKind === 'SOURCE-AUTHORITATIVE REVIEW' ? 'The notice authority matches the target evidence authority lineage.' : 'A different registered authority will be treated as a third-party challenge and cannot impersonate source-authoritative INVALIDATE.'}</div>}
    <FormField label="Target evidence ID" value={values.targetEvidenceId} onChange={update('targetEvidenceId')} placeholder="64-character PALINODE ID" mono />
    <FormField label="Notice authority ID" value={values.noticeAuthorityId} onChange={update('noticeAuthorityId')} placeholder="Registered authority ID" mono />
    <FormField label="Notice HTTPS URI" value={values.noticeUri} onChange={update('noticeUri')} placeholder="https://authority.example/notice.json" />
    <FormField label="Notice SHA-256" value={values.noticeSha256} onChange={update('noticeSha256')} placeholder="64 hexadecimal characters" mono />
    <FormField label={`Notice byte length (max ${MAX_DECLARED_SOURCE_BYTES.toLocaleString()})`} value={values.noticeByteLength} onChange={update('noticeByteLength')} type="number" />
    <label className="field"><span>Opening reason<i>*</i></span><select value={values.openingReasonCode} onChange={(event) => update('openingReasonCode')(event.target.value)}>{CASE_REASON_CODES.map((reason) => <option key={reason} value={reason}>{reason}</option>)}</select></label>
    <label className="field"><span>Opening note<i>*</i></span><textarea value={values.openingNote} onChange={(event) => update('openingNote')(event.target.value)} maxLength={MAX_REASON_NOTE_LENGTH} rows={4} placeholder={`Explain the review basis (max ${MAX_REASON_NOTE_LENGTH} characters).`} /></label>
    {error && <div className="field-error">{error}</div>}
    <p className="form-help">The application submits seven arguments in contract order: target evidence, notice authority, URI, SHA-256, byte length, reason code, and opening note.</p>
    <WriteAction label="Open revocation case" method={call.method} args={call.args} validationError={error} onSubmitted={reset}>Open review</WriteAction>
  </form>;
}
