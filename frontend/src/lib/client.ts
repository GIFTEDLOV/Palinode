import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { TransactionHashVariant } from 'genlayer-js/types';
import type { CalldataEncodable, GenLayerClient, GenLayerTransaction } from 'genlayer-js/types';
import { CHAIN_ID, CONTRACT_ADDRESS, PAGE_SIZE, POLL_INTERVAL_MS, RPC_URL, STUDIONET_RPC_URL } from '../config';
import type { EdgeRecord, NodeRecord, Page, RawRecord, RevocationCase, AuthorityRecord, RecoveryCase, TrackedTransaction, TransactionLifecycle } from '../types';
import { asRecord, pageMeta, pageSlots } from './utils';

export type BrowserProvider = {
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
  on?: (event: string, listener: (...args: unknown[]) => void) => void;
  removeListener?: (event: string, listener: (...args: unknown[]) => void) => void;
};

declare global {
  interface Window { ethereum?: BrowserProvider; }
}

export function publicClient(): GenLayerClient<typeof studionet> {
  return createClient({ chain: studionet, endpoint: RPC_URL });
}

function provider(): BrowserProvider {
  if (!window.ethereum) throw new Error('A compatible wallet provider was not found. Install MetaMask or the GenLayer wallet.');
  return window.ethereum;
}

export function walletClient(address: string): GenLayerClient<typeof studionet> {
  return createClient({
    chain: studionet,
    endpoint: RPC_URL,
    account: address as `0x${string}`,
    provider: provider(),
  });
}

export async function connectedWalletState(): Promise<{ address: string | null; chainId: number | null }> {
  if (!window.ethereum) return { address: null, chainId: null };
  const [chain, accounts] = await Promise.all([
    window.ethereum.request({ method: 'eth_chainId' }),
    window.ethereum.request({ method: 'eth_accounts' }),
  ]);
  const address = Array.isArray(accounts) ? String(accounts[0] || '') : '';
  return { address: address || null, chainId: Number.parseInt(String(chain), 16) || null };
}

export async function connectWallet(): Promise<{ address: string; chainId: number }> {
  const currentProvider = provider();
  const chainHex = `0x${CHAIN_ID.toString(16)}`;
  const current = String(await currentProvider.request({ method: 'eth_chainId' }));
  if (current.toLowerCase() !== chainHex) {
    try {
      await currentProvider.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: chainHex }] });
    } catch {
      await currentProvider.request({ method: 'wallet_addEthereumChain', params: [{ chainId: chainHex, chainName: 'GenLayer Studionet', rpcUrls: [STUDIONET_RPC_URL], nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 } }] });
    }
  }
  const accounts = await currentProvider.request({ method: 'eth_requestAccounts' });
  const address = Array.isArray(accounts) ? String(accounts[0] || '') : '';
  if (!address) throw new Error('The wallet returned no account.');
  const finalChain = String(await currentProvider.request({ method: 'eth_chainId' }));
  const chainId = Number.parseInt(finalChain, 16);
  if (chainId !== CHAIN_ID) throw new Error(`Wallet is on chain ${chainId}; switch to ${CHAIN_ID} before writing.`);
  return { address, chainId };
}

export async function readContract<T = unknown>(method: string, args: CalldataEncodable[] = [], client = publicClient()): Promise<T> {
  return await client.readContract({ address: CONTRACT_ADDRESS, functionName: method, args, transactionHashVariant: TransactionHashVariant.LATEST_FINAL }) as T;
}

export async function loadDirectNode(nodeId: string, client = publicClient()): Promise<NodeRecord> {
  return { ...asRecord(await readContract('get_node_record', [nodeId], client)), node_id: nodeId } as NodeRecord;
}

export async function loadDirectAuthority(authorityId: string, client = publicClient()): Promise<AuthorityRecord> {
  return { ...asRecord(await readContract('get_source_authority', [authorityId], client)), authority_id: authorityId } as AuthorityRecord;
}

export async function loadDirectRevocation(caseId: string, client = publicClient()): Promise<RevocationCase> {
  return { ...asRecord(await readContract('get_revocation_case', [caseId], client)), case_id: caseId } as RevocationCase;
}

export async function loadDirectRecovery(recoveryId: string, client = publicClient()): Promise<RecoveryCase> {
  return { ...asRecord(await readContract('get_recovery_case', [recoveryId], client)), recovery_id: recoveryId } as RecoveryCase;
}

async function collectPage<T>(method: string, detailMethod: string, idKey: string, map: (record: RawRecord) => T, client: GenLayerClient<typeof studionet>): Promise<Page<T>> {
  const items: T[] = [];
  let cursor = 0;
  while (true) {
    const raw = await readContract(method, [cursor, PAGE_SIZE], client);
    const ids = pageSlots(raw);
    for (const id of ids) {
      const detail = await readContract(detailMethod, [id], client);
      items.push(map({ ...asRecord(detail), [idKey]: id }));
    }
    const meta = pageMeta(raw, cursor);
    if (meta.exhausted) return { items, cursor, nextCursor: meta.nextCursor, exhausted: true };
    if (meta.nextCursor <= cursor) throw new Error(`${method} returned a non-progressing cursor.`);
    cursor = meta.nextCursor;
  }
}

function namespacedView(value: unknown, prefix: string): RawRecord {
  if (Array.isArray(value)) return { [`${prefix}_items`]: JSON.stringify(value) };
  return Object.fromEntries(Object.entries(asRecord(value)).map(([key, item]) => [`${prefix}_${key}`, item]));
}

export async function loadNodeViews(node: NodeRecord, client = publicClient()) {
  const viewNames = node.node_type === 'EVIDENCE'
    ? ['get_active_causes', 'get_active_causes_page', 'get_status_history', 'get_assessment_history', 'get_evidence_mirrors']
    : ['get_active_causes', 'get_active_causes_page', 'get_status_history', 'get_assessment_history'];
  const views = await Promise.all(viewNames.map((method) => readContract(method, method === 'get_active_causes_page' ? [node.node_id, 0, PAGE_SIZE] : [node.node_id], client)));
  const extras = Object.assign({}, ...views.map((view, index) => namespacedView(view, viewNames[index])));
  if (node.node_type === 'EVIDENCE' && node.successor_evidence_id) {
    try { Object.assign(extras, namespacedView(await readContract('get_evidence_successor_link', [node.node_id], client), 'successor_link')); } catch { /* no link is a valid canonical state */ }
  }
  return { ...node, ...extras } as NodeRecord;
}

export async function loadAuthorityViews(item: AuthorityRecord, client = publicClient()) {
  const versions = await readContract('get_source_authority_versions_page', [item.authority_id, 0, PAGE_SIZE], client);
  return { ...item, ...namespacedView(versions, 'authority_versions') };
}

export async function loadAuthorityVersion(authorityId: string, version: string, client = publicClient()) {
  return await readContract('get_source_authority_version', [authorityId, Number(version)], client) as RawRecord;
}

export async function loadCaseViews(item: RevocationCase, client = publicClient()) {
  const [queue, mirrors, telemetry, history] = await Promise.all([
    readContract('get_impact_queue_state', [item.case_id], client),
    readContract('get_notice_mirrors', [item.case_id], client),
    readContract('get_retry_telemetry', [item.case_id], client),
    readContract('get_case_result_history', [item.case_id], client),
  ]);
  return { ...item, ...namespacedView(queue, 'impact_queue'), ...namespacedView(mirrors, 'notice_mirrors'), ...namespacedView(telemetry, 'retry_telemetry'), ...namespacedView(history, 'case_result_history') };
}

export async function loadCauseSlots(nodes: NodeRecord[], caseId: string, client = publicClient()) {
  const entries = await Promise.all(nodes.map(async (node) => {
    const page = await readContract('get_active_causes_page', [node.node_id, 0, PAGE_SIZE], client) as RawRecord;
    const slots = pageSlots(page).filter((slot) => slot.startsWith(`${caseId}|`));
    return [node.node_id, slots] as const;
  }));
  return Object.fromEntries(entries);
}

export async function loadRecoveryViews(item: RecoveryCase, client = publicClient()) {
  const [queue, telemetry, history] = await Promise.all([
    readContract('get_recovery_queue_state', [item.recovery_id], client),
    readContract('get_recovery_retry_telemetry', [item.recovery_id], client),
    readContract('get_recovery_result_history', [item.recovery_id], client),
  ]);
  return { ...item, ...namespacedView(queue, 'recovery_queue'), ...namespacedView(telemetry, 'recovery_retry_telemetry'), ...namespacedView(history, 'recovery_result_history') };
}

export async function loadSnapshot(client = publicClient()): Promise<Pick<import('../types').ProtocolSnapshot, 'nodes' | 'edges' | 'authorities' | 'revocations' | 'recoveries'>> {
  const [nodes, edges, authorities, revocations, recoveries] = await Promise.all([
    collectPage('get_node_ids_page', 'get_node_record', 'node_id', (record) => record as NodeRecord, client),
    collectPage('get_edge_ids_page', 'get_dependency_record', 'edge_id', (record) => record as EdgeRecord, client),
    collectPage('get_authority_ids_page', 'get_source_authority', 'authority_id', (record) => record as AuthorityRecord, client),
    collectPage('get_case_ids_page', 'get_revocation_case', 'case_id', (record) => record as RevocationCase, client),
    collectPage('get_recovery_ids_page', 'get_recovery_case', 'recovery_id', (record) => record as RecoveryCase, client),
  ]);
  return { nodes: nodes.items, edges: edges.items, authorities: authorities.items, revocations: revocations.items, recoveries: recoveries.items };
}

export function protocolPhase(status: string, execution: string, resolutionAction = ''): TrackedTransaction['phase'] {
  const normalized = status.toUpperCase();
  const exec = execution.toUpperCase();
  if (normalized === 'FINALIZED') return exec === 'FINISHED_WITH_RETURN' ? 'FINALIZED SUCCESS' : 'FINALIZED ERROR';
  if (normalized === 'CANCELED') return 'CANCELED';
  if (normalized === 'UNDETERMINED') return 'UNDETERMINED';
  if (normalized === 'ACCEPTED') return 'ACCEPTED / PROVISIONAL';
  if (normalized === 'APPEAL_COMMITTING' || normalized === 'APPEAL_REVEALING' || normalized === 'VALIDATORS_TIMEOUT' || normalized === 'LEADER_TIMEOUT' || normalized === 'LEADER_REVEALING') return resolutionAction === 'Finalize' ? 'FINALIZATION AVAILABLE' : 'APPEAL PERIOD';
  if (['PENDING', 'PROPOSING', 'COMMITTING', 'REVEALING'].includes(normalized)) return normalized as TrackedTransaction['phase'];
  return 'SUBMITTED';
}

function unknownRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

export async function getTransactionLifecycle(id: `0x${string}`): Promise<TransactionLifecycle | null> {
  const response = await fetch(RPC_URL, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: Date.now(), method: 'gen_getTransactionLifecycle', params: [{ txId: id }] }) });
  const body = unknownRecord(await response.json());
  if (!response.ok || body.error) return null;
  const result = body.result;
  return result && typeof result === 'object' ? result as TransactionLifecycle : null;
}

export function txSnapshot(transaction: GenLayerTransaction, prior: TrackedTransaction, lifecycle: TransactionLifecycle | null = null): TrackedTransaction {
  const status = String(transaction.statusName ?? transaction.status ?? lifecycle?.storedStatus ?? 'PENDING');
  const execution = String(transaction.txExecutionResultName ?? transaction.txExecutionResult ?? 'NOT_VOTED');
  const action = lifecycle?.resolutionAction;
  return {
    ...prior,
    phase: protocolPhase(status, execution, action),
    protocolStatus: status,
    projectedStatus: lifecycle?.projectedStatus,
    resolutionAction: action,
    executionResult: execution,
    result: String(transaction.resultName ?? transaction.result ?? '—'),
    updatedAt: new Date().toISOString(),
    error: status === 'FINALIZED' && execution !== 'FINISHED_WITH_RETURN' ? 'The finalized execution returned an error.' : undefined,
  };
}

export function isTerminalPhase(phase: TrackedTransaction['phase']) {
  return ['FINALIZED SUCCESS', 'FINALIZED ERROR', 'UNDETERMINED', 'CANCELED'].includes(phase);
}

export async function pollTransaction(client: GenLayerClient<typeof studionet>, tracked: TrackedTransaction, onUpdate: (next: TrackedTransaction) => void, signal?: AbortSignal) {
  let current = tracked;
  while (!signal?.aborted) {
    try {
      const tx = await client.getTransaction({ hash: current.id as import('genlayer-js/types').Hash });
      const lifecycle = await getTransactionLifecycle(current.id).catch(() => null);
      current = txSnapshot(tx, current, lifecycle);
      onUpdate(current);
      if (isTerminalPhase(current.phase)) return current;
    } catch (error) {
      current = { ...current, phase: 'TIMEOUT', updatedAt: new Date().toISOString(), error: error instanceof Error ? error.message : 'Unable to read transaction state.' };
      onUpdate(current);
    }
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }
  return current;
}
