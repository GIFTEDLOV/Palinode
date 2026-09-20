import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { TransactionHashVariant } from 'genlayer-js/types';
import type { CalldataEncodable, GenLayerClient } from 'genlayer-js/types';
import { CHAIN_ID, CONTRACT_ADDRESS, PAGE_SIZE, POLL_INTERVAL_MS, RPC_URL } from '../config';
import type { EdgeRecord, NodeRecord, Page, RawRecord, RevocationCase, AuthorityRecord, RecoveryCase, TrackedTransaction, LifecyclePhase } from '../types';
import { asRecord, pageMeta, pageSlots } from './utils';

export type BrowserProvider = { request: (args: { method: string; params?: unknown[] }) => Promise<unknown> };
declare global { interface Window { ethereum?: BrowserProvider } }

export function publicClient(): GenLayerClient<typeof studionet> {
  return createClient({ chain: studionet, endpoint: RPC_URL });
}

export function walletClient(address: string): GenLayerClient<typeof studionet> {
  return createClient({ chain: studionet, endpoint: RPC_URL, account: address as any });
}

export async function connectWallet() {
  if (!window.ethereum) throw new Error('A compatible wallet provider was not found. Install MetaMask or the GenLayer wallet.');
  const chainHex = `0x${CHAIN_ID.toString(16)}`;
  const current = String(await window.ethereum.request({ method: 'eth_chainId' }));
  if (current.toLowerCase() !== chainHex) {
    try {
      await window.ethereum.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: chainHex }] });
    } catch {
      await window.ethereum.request({ method: 'wallet_addEthereumChain', params: [{ chainId: chainHex, chainName: 'GenLayer Studionet', rpcUrls: [RPC_URL], nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 } }] });
    }
  }
  const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
  const account = Array.isArray(accounts) ? String(accounts[0] || '') : '';
  if (!account) throw new Error('The wallet returned no account.');
  return account;
}

export async function readContract<T = unknown>(method: string, args: CalldataEncodable[] = [], client = publicClient()): Promise<T> {
  return await client.readContract({ address: CONTRACT_ADDRESS, functionName: method, args, transactionHashVariant: TransactionHashVariant.LATEST_FINAL }) as T;
}

async function collectPage<T>(method: string, detailMethod: string, map: (record: RawRecord) => T, client: GenLayerClient<typeof studionet>): Promise<Page<T>> {
  const items: T[] = [];
  let cursor = 0;
  while (items.length < 256) {
    const raw = await readContract(method, [cursor, PAGE_SIZE], client);
    const ids = pageSlots(raw);
    for (const id of ids) {
      const detail = await readContract(detailMethod, [id], client);
      items.push(map({ ...asRecord(detail), [detailMethod === 'get_node_record' ? 'node_id' : detailMethod === 'get_dependency_record' ? 'edge_id' : detailMethod === 'get_source_authority' ? 'authority_id' : detailMethod === 'get_revocation_case' ? 'case_id' : 'recovery_id']: id }));
    }
    const meta = pageMeta(raw, cursor);
    if (meta.exhausted) return { items, cursor: 0, nextCursor: meta.nextCursor, exhausted: true };
    cursor = meta.nextCursor;
  }
  return { items, cursor: 0, nextCursor: cursor, exhausted: false };
}

function namespacedView(value: unknown, prefix: string): RawRecord {
  if (Array.isArray(value)) return { [`${prefix}_items`]: JSON.stringify(value) };
  return Object.fromEntries(Object.entries(asRecord(value)).map(([key, item]) => [`${prefix}_${key}`, item]));
}

export async function loadNodeViews(node: NodeRecord, client = publicClient()) {
  const viewNames = node.node_type === 'EVIDENCE'
      ? ['get_active_causes', 'get_status_history', 'get_assessment_history', 'get_evidence_mirrors']
      : ['get_active_causes', 'get_status_history', 'get_assessment_history'];
  const views = await Promise.all(viewNames.map((method) => readContract(method, [node.node_id], client)));
  const extras = Object.assign({}, ...views.map((view, index) => namespacedView(view, viewNames[index])));
  return { ...node, ...extras } as NodeRecord;
}

export async function loadCaseViews(item: RevocationCase, client = publicClient()) {
    const [queue, mirrors, telemetry] = await Promise.all([
      readContract('get_impact_queue_state', [item.case_id], client),
      readContract('get_notice_mirrors', [item.case_id], client),
      readContract('get_retry_telemetry', [item.case_id], client),
    ]);
    return { ...item, ...namespacedView(queue, 'impact_queue'), ...namespacedView(mirrors, 'notice_mirrors'), ...namespacedView(telemetry, 'retry_telemetry') };
}

export async function loadRecoveryViews(item: RecoveryCase, client = publicClient()) {
    const [queue, telemetry] = await Promise.all([
      readContract('get_recovery_queue_state', [item.recovery_id], client),
      readContract('get_recovery_retry_telemetry', [item.recovery_id], client),
    ]);
    return { ...item, ...namespacedView(queue, 'recovery_queue'), ...namespacedView(telemetry, 'recovery_retry_telemetry') };
}

export async function loadSnapshot(client = publicClient()): Promise<Pick<import('../types').ProtocolSnapshot, 'nodes' | 'edges' | 'authorities' | 'revocations' | 'recoveries'>> {
  const [nodes, edges, authorities, revocations, recoveries] = await Promise.all([
    collectPage('get_node_ids_page', 'get_node_record', (record) => record as NodeRecord, client),
    collectPage('get_edge_ids_page', 'get_dependency_record', (record) => record as EdgeRecord, client),
    collectPage('get_authority_ids_page', 'get_source_authority', (record) => record as AuthorityRecord, client),
    collectPage('get_case_ids_page', 'get_revocation_case', (record) => record as RevocationCase, client),
    collectPage('get_recovery_ids_page', 'get_recovery_case', (record) => record as RecoveryCase, client),
  ]);
  return { nodes: nodes.items, edges: edges.items, authorities: authorities.items, revocations: revocations.items, recoveries: recoveries.items };
}

export function protocolPhase(status: string, execution: string): LifecyclePhase {
  const normalized = status.toUpperCase();
  if (normalized === 'FINALIZED') return execution === 'FINISHED_WITH_RETURN' ? 'FINALIZED SUCCESS' : 'FINALIZED ERROR';
  if (normalized === 'READY_TO_FINALIZE') return 'FINALIZATION AVAILABLE';
  if (normalized === 'ACCEPTED') return 'ACCEPTED / PROVISIONAL';
  if (normalized === 'APPEAL_COMMITTING' || normalized === 'APPEAL_REVEALING') return 'APPEAL PERIOD';
  if (normalized === 'UNDETERMINED' || normalized === 'LEADER_TIMEOUT' || normalized === 'VALIDATORS_TIMEOUT') return 'UNDETERMINED';
  if (normalized === 'PENDING') return 'PENDING';
  if (normalized === 'PROPOSING') return 'PROPOSING';
  if (normalized === 'COMMITTING') return 'COMMITTING';
  if (normalized === 'REVEALING') return 'REVEALING';
  return 'SUBMITTED';
}

export function txSnapshot(transaction: any, prior: TrackedTransaction): TrackedTransaction {
  const status = String(transaction?.statusName ?? transaction?.status ?? 'PENDING');
  const execution = String(transaction?.txExecutionResultName ?? transaction?.txExecutionResult ?? 'NOT_VOTED');
  return { ...prior, phase: protocolPhase(status, execution), protocolStatus: status, executionResult: execution, result: String(transaction?.resultName ?? transaction?.result ?? '—'), updatedAt: new Date().toISOString(), error: execution === 'FINISHED_WITH_ERROR' ? 'The finalized execution returned an error.' : undefined };
}

export async function pollTransaction(client: GenLayerClient<typeof studionet>, tracked: TrackedTransaction, onUpdate: (next: TrackedTransaction) => void, signal?: AbortSignal) {
  let current = tracked;
  while (!signal?.aborted) {
    try {
      const tx = await client.getTransaction({ hash: current.id as any });
      current = txSnapshot(tx, current);
      onUpdate(current);
      if (current.phase === 'FINALIZED SUCCESS' || current.phase === 'FINALIZED ERROR' || current.phase === 'UNDETERMINED') return current;
    } catch (error) {
      current = { ...current, phase: 'TIMEOUT', updatedAt: new Date().toISOString(), error: error instanceof Error ? error.message : 'Unable to read transaction state.' };
      onUpdate(current);
    }
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }
  return current;
}
