/* global console, process */
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { TransactionHashVariant } from 'genlayer-js/types';

const repoRoot = path.resolve(process.cwd(), '..');
const contract = '0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b';
const caseId = '86bb1eaddcd802361a5105a8e492cc67f2d3fc647e2a20111bd1158ea4e07534';
const client = createClient({ chain: studionet, endpoint: 'https://studio.genlayer.com/api' });
const read = (functionName, args) => client.readContract({ address: contract, functionName, args, transactionHashVariant: TransactionHashVariant.LATEST_FINAL });
const [caseRecord, queue, history] = await Promise.all([
  read('get_revocation_case', [caseId]),
  read('get_impact_queue_state', [caseId]),
  read('get_case_result_history', [caseId]),
]);
const sourceBytes = await import('node:fs/promises').then(({ readFile }) => readFile(path.join(repoRoot, 'contracts', 'palinode_v2.py')));
const result = {
  result: caseRecord.case_status === 'COMPLETE' && Number(queue.cursor) >= Number(queue.queue_length) ? 'PASS' : 'BLOCKED_NOT_STATE_NEUTRAL',
  network: 'Studionet',
  chain_id: 61999,
  contract_address: contract,
  method: 'process_impact',
  args: [caseId, 1],
  caller_requirement: 'any caller accepted by the public write; this is a completed-case no-op',
  object_id: caseId,
  case_status: caseRecord.case_status,
  queue_state: queue,
  history: history,
  expected_effect: 'u256(0); no sequence counter, status/history, or queue mutation',
  source_proof: {
    path: 'contracts/palinode_v2.py',
    sha256: createHash('sha256').update(sourceBytes).digest('hex'),
    process_impact_definition_lines: '2863-2873',
    complete_case_branch: 'if self.case_status[case_id] == CASE_COMPLETE: return u256(0)',
  },
  value: '0 GEN',
  sdk_fee_estimate: 'genlayer-js performs eth_estimateGas during wallet write preparation; no signature has been requested',
};
const output = path.join(repoRoot, 'evidence', 'studionet', 'v4', 'frontend-wallet-smoke-preflight.json');
await mkdir(path.dirname(output), { recursive: true });
await writeFile(output, JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
