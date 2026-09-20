/* global console */
import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { TransactionHashVariant } from 'genlayer-js/types';

const address = '0x9c9d1993cd938846D1163Bba9AA81AC6d165de88';
const endpoint = 'https://studio.genlayer.com/api';
const pages = [
  ['get_node_ids_page', 'get_node_record'],
  ['get_edge_ids_page', 'get_dependency_record'],
  ['get_case_ids_page', 'get_revocation_case'],
  ['get_recovery_ids_page', 'get_recovery_case'],
  ['get_authority_ids_page', 'get_source_authority'],
];
const client = createClient({ chain: studionet, endpoint });

const results = {};
for (const [functionName, detailMethod] of pages) {
  const value = await client.readContract({ address, functionName, args: [0, 64], transactionHashVariant: TransactionHashVariant.LATEST_FINAL });
  const record = value && typeof value === 'object' ? value : {};
  const count = Number(record.count ?? 0);
  const nextCursor = Number(record.next_cursor ?? 0);
  if (!Number.isInteger(count) || count < 0 || count > 64) throw new Error(`${functionName}: invalid bounded count`);
  if (!Number.isInteger(nextCursor) || nextCursor < 0) throw new Error(`${functionName}: invalid cursor`);
  const ids = Array.from({ length: count }, (_, index) => record[`slot_${index}`]).filter(Boolean);
  const details = [];
  for (const id of ids) {
    const detail = await client.readContract({ address, functionName: detailMethod, args: [id], transactionHashVariant: TransactionHashVariant.LATEST_FINAL });
    if (!detail || typeof detail !== 'object') throw new Error(`${detailMethod}: malformed canonical record`);
    details.push(id);
  }
  results[functionName] = { count, nextCursor, detailsRead: details.length };
}

console.log(JSON.stringify({ network: 'Studionet', chainId: studionet.id, contract: address, pages: results }, null, 2));
