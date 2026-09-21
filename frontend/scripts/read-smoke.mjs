/* global console */
import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { TransactionHashVariant } from 'genlayer-js/types';

const address = '0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b';
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
  const details = [];
  let cursor = 0;
  let pagesRead = 0;
  while (true) {
    const value = await client.readContract({ address, functionName, args: [cursor, 64], transactionHashVariant: TransactionHashVariant.LATEST_FINAL });
    const record = value && typeof value === 'object' ? value : {};
    const count = Number(record.count ?? 0);
    const nextCursor = Number(record.next_cursor ?? cursor);
    if (!Number.isInteger(count) || count < 0 || count > 64) throw new Error(`${functionName}: invalid bounded count`);
    if (!Number.isInteger(nextCursor) || nextCursor < cursor) throw new Error(`${functionName}: invalid cursor`);
    const ids = Array.from({ length: count }, (_, index) => record[`slot_${index}`]).filter(Boolean);
    for (const id of ids) {
      const detail = await client.readContract({ address, functionName: detailMethod, args: [id], transactionHashVariant: TransactionHashVariant.LATEST_FINAL });
      if (!detail || typeof detail !== 'object') throw new Error(`${detailMethod}: malformed canonical record`);
      details.push(id);
    }
    pagesRead += 1;
    if (count === 0 || nextCursor <= cursor) break;
    cursor = nextCursor;
  }
  results[functionName] = { pagesRead, detailsRead: details.length };
}

console.log(JSON.stringify({ network: 'Studionet', chainId: studionet.id, contract: address, pages: results }, null, 2));
