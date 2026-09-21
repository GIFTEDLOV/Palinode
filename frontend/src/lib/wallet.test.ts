import { afterEach, describe, expect, it, vi } from 'vitest';
import { CHAIN_ID } from '../config';
import { connectedWalletState, connectWallet } from './client';

describe('provider-backed wallet guard', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('does not infer connection from a cached address when the provider has no account', async () => {
    const request = vi.fn(async ({ method }: { method: string }) => method === 'eth_chainId' ? '0xf22f' : []);
    vi.stubGlobal('window', { ethereum: { request } });
    expect(await connectedWalletState()).toEqual({ address: null, chainId: CHAIN_ID });
  });

  it('requests the correct chain and account through the EIP-1193 provider', async () => {
    let chain = '0x1';
    const request = vi.fn(async ({ method }: { method: string }) => {
      if (method === 'eth_chainId') return chain;
      if (method === 'wallet_switchEthereumChain') { chain = `0x${CHAIN_ID.toString(16)}`; return null; }
      if (method === 'eth_requestAccounts') return ['0x0000000000000000000000000000000000000001'];
      return [];
    });
    vi.stubGlobal('window', { ethereum: { request } });
    const result = await connectWallet();
    expect(result.chainId).toBe(CHAIN_ID);
    expect(request).toHaveBeenCalledWith({ method: 'eth_requestAccounts' });
  });
});
