export const NETWORK = 'Studionet';
export const CHAIN_ID = 61999;
export const RPC_URL = 'https://studio.genlayer.com/api';
export const CONTRACT_ADDRESS = '0x9c9d1993cd938846D1163Bba9AA81AC6d165de88' as const;
export const CONTRACT_SHA256 = 'bd5e981605f2533bd5354a4e884288d585020514d4be9eaabd9cdb4ff39d4c06';
export const FREEZE_COMMIT = '4a18242600218914ef4fa5de441bebd385967a1b';
export const FIXTURE_URL = 'https://palinode-fixture.vercel.app';
export const PAGE_SIZE = 64;
export const POLL_INTERVAL_MS = 4_000;

export const NODE_TYPES = ['EVIDENCE', 'CLAIM', 'DECISION', 'ATTESTATION', 'AUTHORIZATION'] as const;
export type NodeType = (typeof NODE_TYPES)[number];
export const RELATIONSHIPS = ['SUPPORTS', 'REQUIRES', 'DERIVED_FROM', 'QUALIFIES', 'AUTHORIZES', 'CORROBORATES', 'CONTRADICTS'] as const;
export type Relationship = (typeof RELATIONSHIPS)[number];
export const RELIANCE_STATUSES = ['ACTIVE', 'QUESTIONED', 'UNDER_REVIEW', 'QUARANTINED', 'SUPERSEDED', 'INVALIDATED', 'REINSTATED', 'INCONCLUSIVE'] as const;
export type RelianceStatus = (typeof RELIANCE_STATUSES)[number];
export const AUTH_STATUSES = ['UNASSESSED', 'PENDING', 'CLEARED', 'REJECTED', 'INCONCLUSIVE', 'SOURCE_UNAVAILABLE'] as const;
export type AuthStatus = (typeof AUTH_STATUSES)[number];

export const WRITE_METHODS = new Set([
  'add_evidence_mirror', 'add_notice_mirror', 'assess_recovery', 'assess_revocation',
  'authenticate_evidence', 'link_evidence_successor', 'open_recovery_case',
  'open_revocation_case', 'process_impact', 'process_recovery_impact',
  'register_attestation', 'register_authorization', 'register_claim', 'register_decision',
  'register_dependency', 'register_evidence', 'register_node', 'register_source_authority',
  'retry_revocation_case', 'revoke_source_authority', 'rotate_source_authority',
]);
