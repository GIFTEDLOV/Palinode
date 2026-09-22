import type { AuthStatus, NodeType, RelianceStatus, Relationship } from './config';

export type RawRecord = Record<string, string>;

export type NodeRecord = RawRecord & {
  node_id: string;
  node_type: NodeType;
  subject_id: string;
  title: string;
  creation_sequence: string;
  reliance_status: RelianceStatus;
  authentication_status: AuthStatus;
  assessment_status: AuthStatus;
  status: RelianceStatus;
  source_uri: string;
  content_sha256?: string;
  byte_length?: string;
  authority_id?: string;
  authority_version?: string;
  authority_version_id?: string;
  creator?: string;
  successor_evidence_id?: string;
  predecessor_evidence_id?: string;
};

export type EdgeRecord = RawRecord & {
  edge_id: string;
  parent_node_id: string;
  child_node_id: string;
  relationship: Relationship;
  creation_sequence: string;
  active: string;
  assertor?: string;
};

export type AuthorityVersionRecord = RawRecord & {
  authority_version_id?: string;
  authority_id?: string;
  version?: string;
  controller?: string;
  origin?: string;
  policy?: string;
  nonce?: string;
  status?: string;
  challenge_uri?: string;
};

export type AuthorityRecord = RawRecord & {
  authority_id: string;
  canonical_origin: string;
  authority_address: string;
  current_version: string;
  status: string;
  verification_policy: string;
  challenge_nonce?: string;
  challenge_uri?: string;
};

export type CauseSummary = RawRecord & {
  active_count?: string;
  invalidated_count?: string;
  quarantined_count?: string;
  questioned_count?: string;
  under_review_count?: string;
};

export type CausePage = RawRecord & {
  count?: string;
  cursor?: string;
  next_cursor?: string;
  [key: `slot_${number}`]: string | undefined;
};

export type RevocationCase = RawRecord & {
  case_id: string;
  target_evidence_id: string;
  case_status: string;
  result_status: string;
  materiality: string;
  root_effect: string;
  reason_code: string;
  notice_kind?: string;
  notice_uri: string;
  notice_sha256: string;
  notice_byte_length?: string;
  notice_authority_id?: string;
  notice_authority_version?: string;
  target_reliance_status: string;
  target_authentication_status: string;
  semantic_verdict?: string;
  assessment_count?: string;
};

export type RecoveryCase = RawRecord & {
  recovery_id: string;
  affected_node_id: string;
  successor_evidence_id: string;
  adverse_case_id: string;
  case_status: string;
  result_status: string;
  recovery_effect: string;
  reason_code: string;
  target_reliance_status: string;
};

export type Page<T> = {
  items: T[];
  cursor: number;
  nextCursor: number;
  exhausted: boolean;
};

export type ProtocolSnapshot = {
  nodes: NodeRecord[];
  edges: EdgeRecord[];
  authorities: AuthorityRecord[];
  revocations: RevocationCase[];
  recoveries: RecoveryCase[];
  loading: boolean;
  error: string | null;
  refreshedAt: number | null;
  freshness: 'LIVE' | 'CACHED' | 'REFRESHING' | 'RPC_UNAVAILABLE';
};

export type LifecycleStatus =
  | 'SUBMITTED' | 'PENDING' | 'PROPOSING' | 'COMMITTING' | 'REVEALING'
  | 'ACCEPTED' | 'UNDETERMINED' | 'FINALIZED' | 'CANCELED'
  | 'APPEAL_REVEALING' | 'APPEAL_COMMITTING' | 'VALIDATORS_TIMEOUT'
  | 'LEADER_TIMEOUT' | 'LEADER_REVEALING';

export type LifecyclePhase =
  | LifecycleStatus
  | 'FINALIZED SUCCESS'
  | 'FINALIZED ERROR'
  | 'ACCEPTED / PROVISIONAL'
  | 'FINALIZATION AVAILABLE'
  | 'APPEAL PERIOD'
  | 'TRACKING DELAYED'
  | 'TIMEOUT';

export type TransactionLifecycle = {
  storedStatus?: string;
  projectedStatus?: string;
  resolutionAction?: string;
  resolutionSource?: string;
  decisionId?: string | null;
  decisionActive?: boolean;
};

export type TrackedTransaction = {
  id: `0x${string}`;
  label: string;
  method: string;
  args: unknown[];
  phase: LifecyclePhase;
  protocolStatus: string;
  projectedStatus?: string;
  resolutionAction?: string;
  executionResult: string;
  result: string;
  submittedAt: string;
  updatedAt: string;
  error?: string;
};
