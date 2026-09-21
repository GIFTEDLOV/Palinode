export const NETWORK = 'Studionet';
export const CHAIN_ID = 61999;
export const STUDIONET_RPC_URL = 'https://studio.genlayer.com/api';
export const RPC_URL = import.meta.env.VITE_GENLAYER_RPC_URL || '/api/rpc';
export const CONTRACT_ADDRESS = '0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b' as const;
export const CONTRACT_SHA256 = '0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601';
export const FREEZE_COMMIT = '14bb4574a8d248c978b55ff1fb70f32c0293f313';
export const FROZEN_SOURCE_PATH = 'contracts/palinode_v2.py';
export const FIXTURE_URL = 'https://palinode-fixture.vercel.app';
export const REVIEWER_FIXTURE_URL = 'https://palinode-reviewer-fixture.vercel.app';
export const PAGE_SIZE = 64;
export const POLL_INTERVAL_MS = 4_000;
export const MAX_IMPACT_STEPS = 32;

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

export const V4_SCHEMA_METHODS = new Set([
  'add_evidence_mirror', 'add_notice_mirror', 'assess_recovery', 'assess_revocation',
  'authenticate_evidence', 'get_active_causes', 'get_active_causes_page', 'get_assessment_history',
  'get_authority_ids_page', 'get_case_ids_page', 'get_case_result_history', 'get_dependency_record',
  'get_edge_ids_page', 'get_evidence_mirrors', 'get_evidence_successor_link', 'get_impact_queue_state',
  'get_node_ids_page', 'get_node_record', 'get_notice_mirrors', 'get_recovery_case', 'get_recovery_ids_page',
  'get_recovery_queue_state', 'get_recovery_result_history', 'get_recovery_retry_telemetry', 'get_retry_telemetry',
  'get_revocation_case', 'get_source_authority', 'get_source_authority_version', 'get_source_authority_versions_page',
  'get_status_history', 'link_evidence_successor', 'open_recovery_case', 'open_revocation_case', 'process_impact',
  'process_recovery_impact', 'register_attestation', 'register_authorization', 'register_claim', 'register_decision',
  'register_dependency', 'register_evidence', 'register_node', 'register_source_authority', 'retry_revocation_case',
  'revoke_source_authority', 'rotate_source_authority',
] as const);
