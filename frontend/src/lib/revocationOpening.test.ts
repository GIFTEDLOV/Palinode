import { describe, expect, it } from 'vitest';
import { buildOpenRevocationCaseCall, validateOpenReview, type OpenReviewContext, type OpenReviewFormValues } from './revocationOpening';
import { createPendingWriteDescriptor } from './writeDescriptor';

const targetEvidenceId = 'a'.repeat(64);
const noticeAuthorityId = 'b'.repeat(64);
const validValues: OpenReviewFormValues = {
  targetEvidenceId,
  noticeAuthorityId,
  noticeUri: 'https://authority.example/notices/review-001.json',
  noticeSha256: 'c'.repeat(64),
  noticeByteLength: '128',
  openingReasonCode: 'CHANGED',
  openingNote: 'The registered source has changed and should be reviewed.',
};
const validContext: OpenReviewContext = {
  nodes: [{ node_id: targetEvidenceId, node_type: 'EVIDENCE', authentication_status: 'CLEARED', authority_id: noticeAuthorityId }],
  authorities: [{ authority_id: noticeAuthorityId, canonical_origin: 'https://authority.example' }],
};
const nonClearedContext: OpenReviewContext = {
  ...validContext,
  nodes: [{ ...validContext.nodes[0], authentication_status: 'PENDING' }],
};

describe('open review application flow', () => {
  it('constructs open_revocation_case with seven valid arguments for CLEARED evidence', () => {
    expect(validateOpenReview(validValues, validContext)).toBeNull();
    const call = buildOpenRevocationCaseCall(validValues);
    const pendingWrite = createPendingWriteDescriptor({ label: 'Open review', ...call });

    expect(pendingWrite.method).toBe('open_revocation_case');
    expect(pendingWrite.args).toHaveLength(7);
    expect(pendingWrite.args).toEqual([
      targetEvidenceId,
      noticeAuthorityId,
      validValues.noticeUri,
      validValues.noticeSha256,
      128,
      'CHANGED',
      validValues.openingNote,
    ]);
  });

  it.each([
    ['non-CLEARED evidence', nonClearedContext, validValues, 'CLEARED'],
    ['non-HTTPS notice URI', validContext, { ...validValues, noticeUri: 'http://authority.example/notice.json' }, 'HTTPS'],
    ['malformed SHA-256', validContext, { ...validValues, noticeSha256: 'not-a-digest' }, 'SHA-256'],
    ['zero byte length', validContext, { ...validValues, noticeByteLength: '0' }, 'positive integer'],
    ['negative byte length', validContext, { ...validValues, noticeByteLength: '-1' }, 'positive integer'],
    ['unsupported reason code', validContext, { ...validValues, openingReasonCode: 'THIRD_PARTY_CHALLENGE' }, 'opening reason'],
    ['empty opening note', validContext, { ...validValues, openingNote: '   ' }, 'Opening note'],
  ])('blocks %s', (_label, context, values, expected) => {
    expect(validateOpenReview(values as OpenReviewFormValues, context as OpenReviewContext)).toContain(expected);
  });
});
