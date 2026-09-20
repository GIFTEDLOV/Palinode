/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import type { CalldataEncodable } from 'genlayer-js/types';
import { CHAIN_ID, CONTRACT_ADDRESS, RPC_URL } from './config';
import type { ProtocolSnapshot, TrackedTransaction } from './types';
import { connectWallet, loadSnapshot, pollTransaction, walletClient } from './lib/client';

const EMPTY_SNAPSHOT: ProtocolSnapshot = { nodes: [], edges: [], authorities: [], revocations: [], recoveries: [], loading: true, error: null, refreshedAt: null };
const TX_KEY = 'palinode.tracked.transactions.v1';

type WalletContextValue = { address: string | null; chainId: number | null; connecting: boolean; error: string | null; connect: () => Promise<string>; disconnect: () => void };
const WalletContext = createContext<WalletContextValue | null>(null);

export function WalletProvider({ children }: { children: ReactNode }) {
  const [address, setAddress] = useState<string | null>(() => localStorage.getItem('palinode.wallet.address'));
  const [chainId, setChainId] = useState<number | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(async () => {
    setConnecting(true); setError(null);
    try {
      const next = await connectWallet();
      setAddress(next); localStorage.setItem('palinode.wallet.address', next); setChainId(CHAIN_ID); return next;
    } catch (reason) { const message = reason instanceof Error ? reason.message : 'Wallet connection failed.'; setError(message); return ''; }
    finally { setConnecting(false); }
  }, []);

  const disconnect = useCallback(() => { setAddress(null); setChainId(null); localStorage.removeItem('palinode.wallet.address'); }, []);
  useEffect(() => {
    if (!window.ethereum) return;
    void window.ethereum.request({ method: 'eth_chainId' }).then((value) => setChainId(Number.parseInt(String(value), 16))).catch(() => undefined);
  }, [address]);
  return <WalletContext.Provider value={{ address, chainId, connecting, error, connect, disconnect }}>{children}</WalletContext.Provider>;
}

export function useWallet() {
  const value = useContext(WalletContext);
  if (!value) throw new Error('useWallet must be used inside WalletProvider');
  return value;
}

type ProtocolContextValue = ProtocolSnapshot & { refresh: () => Promise<void> };
const ProtocolContext = createContext<ProtocolContextValue | null>(null);

export function ProtocolProvider({ children }: { children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<ProtocolSnapshot>(EMPTY_SNAPSHOT);
  const refresh = useCallback(async () => {
    setSnapshot((current) => ({ ...current, loading: true, error: null }));
    try {
      const client = createClient({ chain: studionet, endpoint: RPC_URL });
      const data = await loadSnapshot(client);
      setSnapshot({ ...data, loading: false, error: null, refreshedAt: Date.now() });
    } catch (reason) {
      setSnapshot((current) => ({ ...current, loading: false, error: reason instanceof Error ? reason.message : 'The canonical read surface is unavailable.' }));
    }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  return <ProtocolContext.Provider value={{ ...snapshot, refresh }}>{children}</ProtocolContext.Provider>;
}

export function useProtocol() {
  const value = useContext(ProtocolContext);
  if (!value) throw new Error('useProtocol must be used inside ProtocolProvider');
  return value;
}

type TransactionContextValue = { transactions: TrackedTransaction[]; submit: (label: string, method: string, args: CalldataEncodable[], connectedAddress?: string) => Promise<TrackedTransaction>; drawerOpen: boolean; setDrawerOpen: (open: boolean) => void };
const TransactionContext = createContext<TransactionContextValue | null>(null);

function loadTransactions(): TrackedTransaction[] {
  try { return JSON.parse(localStorage.getItem(TX_KEY) || '[]') as TrackedTransaction[]; } catch { return []; }
}

export function TransactionProvider({ children }: { children: ReactNode }) {
  const { address } = useWallet();
  const [transactions, setTransactions] = useState<TrackedTransaction[]>(loadTransactions);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const pollControllers = useRef(new Map<string, AbortController>());
  const update = useCallback((next: TrackedTransaction) => {
    setTransactions((current) => {
      const value = [next, ...current.filter((item) => item.id !== next.id)].slice(0, 20);
      localStorage.setItem(TX_KEY, JSON.stringify(value));
      return value;
    });
  }, []);
  const resume = useCallback((tracked: TrackedTransaction) => {
    if (pollControllers.current.has(tracked.id)) return;
    const controller = new AbortController();
    pollControllers.current.set(tracked.id, controller);
    const client = walletClient(address || '0x0000000000000000000000000000000000000000');
    void pollTransaction(client, tracked, (next) => update(next), controller.signal).finally(() => { pollControllers.current.delete(tracked.id); });
  }, [address, update]);

  useEffect(() => {
    const active = transactions.filter((item) => !['FINALIZED SUCCESS', 'FINALIZED ERROR', 'UNDETERMINED'].includes(item.phase));
    active.forEach(resume);
  }, [resume, transactions]);
  useEffect(() => () => { pollControllers.current.forEach((controller) => controller.abort()); pollControllers.current.clear(); }, []);

  const submit = useCallback(async (label: string, method: string, args: CalldataEncodable[], connectedAddress?: string) => {
    const account = connectedAddress || address;
    if (!account) throw new Error('Connect a wallet before sending a write.');
    const client = walletClient(account);
    const id = await client.writeContract({ address: CONTRACT_ADDRESS, functionName: method, args, value: 0n });
    const tracked: TrackedTransaction = { id, label, method, args: args as unknown[], phase: 'SUBMITTED', protocolStatus: 'SUBMITTED', executionResult: 'NOT_VOTED', result: '—', submittedAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
    setTransactions((current) => {
      const value = [tracked, ...current.filter((item) => item.id !== id)].slice(0, 20);
      localStorage.setItem(TX_KEY, JSON.stringify(value));
      return value;
    });
    setDrawerOpen(true);
    return tracked;
  }, [address]);

  const value = useMemo(() => ({ transactions, submit, drawerOpen, setDrawerOpen }), [transactions, submit, drawerOpen]);
  return <TransactionContext.Provider value={value}>{children}</TransactionContext.Provider>;
}

export function useTransactions() {
  const value = useContext(TransactionContext);
  if (!value) throw new Error('useTransactions must be used inside TransactionProvider');
  return value;
}

export function useChainLabel() {
  return `Studionet · ${CHAIN_ID}`;
}

export const contractEndpoint = `${RPC_URL} / ${CONTRACT_ADDRESS}`;
