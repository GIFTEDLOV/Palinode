/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { CHAIN_ID, CONTRACT_ADDRESS, RPC_URL } from './config';
import type { ProtocolSnapshot, TrackedTransaction } from './types';
import { connectedWalletState, connectWallet, loadSnapshot, pollTransaction, publicClient, walletClient } from './lib/client';
import { decodeTransactions, encodeTransactions, mergeTrackedTransaction, resumableTransactions } from './lib/transactions';
import { retryRead } from './lib/resilience';
import type { PendingWriteDescriptor } from './lib/writeDescriptor';

const EMPTY_SNAPSHOT: ProtocolSnapshot = { nodes: [], edges: [], authorities: [], revocations: [], recoveries: [], loading: true, error: null, refreshedAt: null, freshness: 'REFRESHING' };
const TX_KEY = 'palinode.tracked.transactions.v2';
const SNAPSHOT_CACHE_KEY = 'palinode.derived.snapshot.v2';
const SNAPSHOT_CACHE_TTL_MS = 120_000;

type WalletContextValue = {
  address: string | null;
  chainId: number | null;
  lastUsedAddress: string | null;
  providerAvailable: boolean;
  connecting: boolean;
  error: string | null;
  connect: () => Promise<string>;
  disconnect: () => void;
};
const WalletContext = createContext<WalletContextValue | null>(null);

export function WalletProvider({ children }: { children: ReactNode }) {
  const [address, setAddress] = useState<string | null>(null);
  const [chainId, setChainId] = useState<number | null>(null);
  const [lastUsedAddress, setLastUsedAddress] = useState<string | null>(() => localStorage.getItem('palinode.wallet.lastUsed'));
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const providerAvailable = Boolean(window.ethereum);

  const syncProvider = useCallback(async () => {
    try {
      const state = await connectedWalletState();
      setAddress(state.address);
      setChainId(state.chainId);
      if (state.address) {
        setLastUsedAddress(state.address);
        localStorage.setItem('palinode.wallet.lastUsed', state.address);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to read wallet state.');
      setAddress(null);
    }
  }, []);

  const connect = useCallback(async () => {
    setConnecting(true); setError(null);
    try {
      const next = await connectWallet();
      setAddress(next.address); setChainId(next.chainId); setLastUsedAddress(next.address);
      localStorage.setItem('palinode.wallet.lastUsed', next.address);
      return next.address;
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : 'Wallet connection failed.';
      setError(message); return '';
    } finally { setConnecting(false); }
  }, []);

  const disconnect = useCallback(() => { setAddress(null); setChainId(null); }, []);

  useEffect(() => {
    // Initial provider synchronization intentionally mirrors an external wallet.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void syncProvider();
    const provider = window.ethereum;
    if (!provider) return undefined;
    const updateChain = (value: unknown) => setChainId(Number.parseInt(String(value), 16) || null);
    const updateAccounts = (value: unknown) => {
      const next = Array.isArray(value) ? String(value[0] || '') : '';
      setAddress(next || null);
      if (next) { setLastUsedAddress(next); localStorage.setItem('palinode.wallet.lastUsed', next); }
    };
    provider.on?.('chainChanged', updateChain);
    provider.on?.('accountsChanged', updateAccounts);
    return () => {
      provider.removeListener?.('chainChanged', updateChain);
      provider.removeListener?.('accountsChanged', updateAccounts);
    };
  }, [syncProvider]);

  return <WalletContext.Provider value={{ address, chainId, lastUsedAddress, providerAvailable, connecting, error, connect, disconnect }}>{children}</WalletContext.Provider>;
}

export function useWallet() {
  const value = useContext(WalletContext);
  if (!value) throw new Error('useWallet must be used inside WalletProvider');
  return value;
}

type ProtocolContextValue = ProtocolSnapshot & { refresh: (force?: boolean) => Promise<void> };
const ProtocolContext = createContext<ProtocolContextValue | null>(null);

export function ProtocolProvider({ children }: { children: ReactNode }) {
  const location = useLocation();
  const [snapshot, setSnapshot] = useState<ProtocolSnapshot>(EMPTY_SNAPSHOT);
  const refresh = useCallback(async (force = false) => {
    if (force) sessionStorage.removeItem(SNAPSHOT_CACHE_KEY);
    let cached = false;
    if (!force) {
      try {
        const stored = JSON.parse(sessionStorage.getItem(SNAPSHOT_CACHE_KEY) || 'null') as { savedAt?: number; data?: Omit<ProtocolSnapshot, 'loading' | 'error' | 'refreshedAt' | 'freshness'> } | null;
        if (stored?.savedAt && stored.data && Date.now() - stored.savedAt < SNAPSHOT_CACHE_TTL_MS) {
          cached = true;
          setSnapshot({ ...stored.data, loading: false, error: null, refreshedAt: stored.savedAt, freshness: 'CACHED' });
          return;
        }
      } catch { sessionStorage.removeItem(SNAPSHOT_CACHE_KEY); }
    }
    setSnapshot((current) => ({ ...current, loading: !cached, error: null, freshness: 'REFRESHING' }));
    try {
      const data = await retryRead(() => loadSnapshot(publicClient()));
      const savedAt = Date.now();
      try { sessionStorage.setItem(SNAPSHOT_CACHE_KEY, JSON.stringify({ savedAt, data })); } catch { /* cache is derived and optional */ }
      setSnapshot({ ...data, loading: false, error: null, refreshedAt: savedAt, freshness: 'LIVE' });
    } catch (reason) {
      setSnapshot((current) => {
        const hasVerifiedSnapshot = current.refreshedAt !== null && (current.nodes.length > 0 || current.edges.length > 0 || current.authorities.length > 0 || current.revocations.length > 0 || current.recoveries.length > 0);
        return { ...current, loading: false, error: reason instanceof Error ? reason.message : 'The canonical read surface is unavailable.', freshness: hasVerifiedSnapshot ? 'RPC_UNAVAILABLE' : 'REFRESHING' };
      });
    }
  }, []);
  useEffect(() => {
    if (!location.pathname.startsWith('/app')) return undefined;
    void refresh();
    const onTerminal = () => { void refresh(true); };
    window.addEventListener('palinode:transaction-terminal', onTerminal);
    return () => window.removeEventListener('palinode:transaction-terminal', onTerminal);
  }, [location.pathname, refresh]);
  return <ProtocolContext.Provider value={{ ...snapshot, refresh }}>{children}</ProtocolContext.Provider>;
}

export function useProtocol() {
  const value = useContext(ProtocolContext);
  if (!value) throw new Error('useProtocol must be used inside ProtocolProvider');
  return value;
}

type TransactionContextValue = { transactions: TrackedTransaction[]; submit: (descriptor: PendingWriteDescriptor, connectedAddress?: string) => Promise<TrackedTransaction>; drawerOpen: boolean; setDrawerOpen: (open: boolean) => void };
const TransactionContext = createContext<TransactionContextValue | null>(null);

function loadTransactions(): TrackedTransaction[] {
  return decodeTransactions(localStorage.getItem(TX_KEY));
}

export function TransactionProvider({ children }: { children: ReactNode }) {
  const { address, chainId } = useWallet();
  const [transactions, setTransactions] = useState<TrackedTransaction[]>(loadTransactions);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const pollControllers = useRef(new Map<string, AbortController>());
  const update = useCallback((next: TrackedTransaction) => {
    setTransactions((current) => {
      const value = mergeTrackedTransaction(current, [next]);
      localStorage.setItem(TX_KEY, encodeTransactions(value));
      if (['FINALIZED SUCCESS', 'FINALIZED ERROR', 'UNDETERMINED', 'CANCELED'].includes(next.phase)) window.dispatchEvent(new Event('palinode:transaction-terminal'));
      return value;
    });
  }, []);
  const resume = useCallback((tracked: TrackedTransaction) => {
    if (pollControllers.current.has(tracked.id)) return;
    const controller = new AbortController();
    pollControllers.current.set(tracked.id, controller);
    void pollTransaction(publicClient(), tracked, update, controller.signal).finally(() => { pollControllers.current.delete(tracked.id); });
  }, [update]);

  useEffect(() => { resumableTransactions(transactions).forEach(resume); }, [resume, transactions]);
  useEffect(() => () => { pollControllers.current.forEach((controller) => controller.abort()); pollControllers.current.clear(); }, []);

  const submit = useCallback(async (descriptor: PendingWriteDescriptor, connectedAddress?: string) => {
    const account = connectedAddress || address;
    if (!account) throw new Error('Connect a wallet before sending a write.');
    if (chainId !== CHAIN_ID) throw new Error(`Switch wallet to ${CHAIN_ID} before sending a write.`);
    const client = walletClient(account);
    const { label, method, args } = descriptor;
    const id = await client.writeContract({ address: descriptor.contract, functionName: descriptor.method, args: descriptor.args, value: descriptor.value });
    const tracked: TrackedTransaction = { id, label, method, args: args as unknown[], phase: 'SUBMITTED', protocolStatus: 'SUBMITTED', executionResult: 'NOT_VOTED', result: '—', submittedAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
    setTransactions((current) => {
      const value = mergeTrackedTransaction(current, [tracked]);
      localStorage.setItem(TX_KEY, encodeTransactions(value));
      return value;
    });
    setDrawerOpen(true);
    return tracked;
  }, [address, chainId]);

  const value = useMemo(() => ({ transactions, submit, drawerOpen, setDrawerOpen }), [transactions, submit, drawerOpen]);
  return <TransactionContext.Provider value={value}>{children}</TransactionContext.Provider>;
}

export function useTransactions() {
  const value = useContext(TransactionContext);
  if (!value) throw new Error('useTransactions must be used inside TransactionProvider');
  return value;
}

export function useChainLabel() { return `Studionet · ${CHAIN_ID}`; }
export const contractEndpoint = `${RPC_URL} / ${CONTRACT_ADDRESS}`;
