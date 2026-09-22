import type { CalldataEncodable } from 'genlayer-js/types';
import { CASE_REASON_CODES, MAX_DECLARED_SOURCE_BYTES, MAX_REASON_NOTE_LENGTH } from '../config';
import type { AuthorityRecord, NodeRecord } from '../types';
import { authorityId, firstError, hexDigest, httpsUrl, nodeId, positiveInteger, required, supportedOpeningReason } from './validation';

export type OpenReviewFormValues = {
  targetEvidenceId: string;
  noticeAuthorityId: string;
  noticeUri: string;
  noticeSha256: string;
  noticeByteLength: string;
  openingReasonCode: string;
  openingNote: string;
};

export type OpenReviewContext = {
  nodes: ReadonlyArray<Pick<NodeRecord, 'node_id' | 'node_type' | 'authentication_status' | 'authority_id'>>;
  authorities: ReadonlyArray<Pick<AuthorityRecord, 'authority_id' | 'canonical_origin'>>;
};

export type OpenRevocationCaseCall = {
  method: 'open_revocation_case';
  args: CalldataEncodable[];
};

function sameOrigin(uri: string, origin: string): boolean {
  try { return new URL(uri).origin === new URL(origin).origin; } catch { return false; }
}

export function validateOpenReview(values: OpenReviewFormValues, context: OpenReviewContext): string | null {
  const targetIdError = nodeId(values.targetEvidenceId, 'Target evidence ID');
  const target = targetIdError ? undefined : context.nodes.find((node) => node.node_id.toLowerCase() === values.targetEvidenceId.trim().toLowerCase());
  const authorityIdError = authorityId(values.noticeAuthorityId);
  const noticeAuthority = authorityIdError ? undefined : context.authorities.find((authority) => authority.authority_id.toLowerCase() === values.noticeAuthorityId.trim().toLowerCase());
  const uriError = httpsUrl(values.noticeUri, 'Notice URI');

  return firstError(
    targetIdError,
    target ? null : 'Target evidence is not present in the current canonical read model.',
    target?.node_type === 'EVIDENCE' ? null : 'Target must be an EVIDENCE node.',
    target?.authentication_status === 'CLEARED' ? null : 'Target evidence must be CLEARED before opening review.',
    authorityIdError,
    noticeAuthority ? null : 'Notice authority is not present in the current canonical read model.',
    uriError,
    noticeAuthority && !sameOrigin(values.noticeUri.trim(), noticeAuthority.canonical_origin)
      ? 'Notice URI must use the registered HTTPS origin for this notice authority.'
      : null,
    hexDigest(values.noticeSha256),
    positiveInteger(values.noticeByteLength, 'Notice byte length', MAX_DECLARED_SOURCE_BYTES),
    supportedOpeningReason(values.openingReasonCode),
    required(values.openingNote, 'Opening note'),
    values.openingNote.trim().length > MAX_REASON_NOTE_LENGTH ? `Opening note must be ${MAX_REASON_NOTE_LENGTH} characters or fewer.` : null,
  );
}

export function buildOpenRevocationCaseCall(values: OpenReviewFormValues): OpenRevocationCaseCall {
  const args = [
    values.targetEvidenceId.trim(),
    values.noticeAuthorityId.trim(),
    values.noticeUri.trim(),
    values.noticeSha256.trim(),
    Number(values.noticeByteLength),
    values.openingReasonCode,
    values.openingNote.trim(),
  ] satisfies CalldataEncodable[];
  return { method: 'open_revocation_case', args };
}

export { CASE_REASON_CODES };
