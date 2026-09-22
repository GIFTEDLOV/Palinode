import type { CalldataEncodable } from 'genlayer-js/types';
import { CHAIN_ID, CONTRACT_ADDRESS } from '../config';

export type PendingWriteDescriptor = Readonly<{
  contract: typeof CONTRACT_ADDRESS;
  method: string;
  args: CalldataEncodable[];
  value: bigint;
  chainId: number;
  label: string;
}>;

export function createPendingWriteDescriptor({
  label,
  method,
  args,
  value = 0n,
  chainId = CHAIN_ID,
  contract = CONTRACT_ADDRESS,
}: {
  label: string;
  method: string;
  args: CalldataEncodable[];
  value?: bigint;
  chainId?: number;
  contract?: typeof CONTRACT_ADDRESS;
}): PendingWriteDescriptor {
  const frozenArgs = Object.freeze([...args]) as unknown as CalldataEncodable[];
  return Object.freeze({ contract, method, args: frozenArgs, value, chainId, label });
}

export function assertSafeProcessImpactDescriptor(descriptor: PendingWriteDescriptor, caseId: string): void {
  const expectedArgs: CalldataEncodable[] = [caseId, 1];
  const matches = descriptor.contract === CONTRACT_ADDRESS
    && descriptor.method === 'process_impact'
    && descriptor.chainId === CHAIN_ID
    && descriptor.value === 0n
    && descriptor.args.length === expectedArgs.length
    && descriptor.args.every((value, index) => value === expectedArgs[index]);
  if (!matches) throw new Error('The confirmed wallet action does not match the verified process_impact no-op.');
}
