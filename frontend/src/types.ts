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
};

export type EdgeRecord = RawRecord & {
  edge_id: string;
  parent_node_id: string;
  child_node_id: string;
  relationship: Relationship;
  creation_sequence: string;
  active: string;
};

export type AuthorityRecord = RawRecord & {
  authority_id: string;
  canonical_origin: string;
  authority_address: string;
  current_version: string;
  status: string;
  verification_policy: string;
};

export type RevocationCase = RawRecord & {
  case_id: string;
  target_evidence_id: string;
  case_status: string;
  result_status: string;
  materiality: string;
  root_effect: string;
  reason_code: string;
  notice_uri: string;
  notice_sha256: string;
  target_reliance_status: string;
  target_authentication_status: string;
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
};

export type LifecyclePhase = 'SUBMITTED' | 'PENDING' | 'PROPOSING' | 'COMMITTING' | 'REVEALING' | 'ACCEPTED / PROVISIONAL' | 'APPEAL PERIOD' | 'FINALIZATION AVAILABLE' | 'FINALIZED SUCCESS' | 'FINALIZED ERROR' | 'UNDETERMINED' | 'TIMEOUT';

export type TrackedTransaction = {
  id: `0x${string}`;
  label: string;
  method: string;
  args: unknown[];
  phase: LifecyclePhase;
  protocolStatus: string;
  executionResult: string;
  result: string;
  submittedAt: string;
  updatedAt: string;
  error?: string;
};
