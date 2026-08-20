import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";
import type { Address, TransactionHash } from "genlayer-js/types";

const rpc = import.meta.env.VITE_GENLAYER_RPC || "https://rpc-bradbury.genlayer.com";
const oracleAddress = import.meta.env.VITE_ORACLE_ADDRESS || "0xcFAFCd13B843bcA830b90B678D6bAA75335D6A5f";

export const gl = createClient({
  chain: testnetBradbury,
  endpoint: rpc,
});

export const ORACLE_ADDRESS = oracleAddress;

export type Bucket = "clear" | "watch" | "flag" | "recuse";

export interface Verdict {
  token: string;
  chain: string;
  bucket: Bucket;
  score: number;
  onchain_json: string;
  offchain_json: string;
  reasoning: string;
  checked_at: number;
  version: number;
}

export interface OnchainSignals {
  contract_verified: boolean | null;
  ownership_renounced: boolean | null;
  owner_active_7d: boolean | null;
  lp_locked: boolean | null;
  lp_lock_days_left: number | null;
  liquidity_usd: number;
  market_cap_usd: number;
  holder_count: number;
  top10_pct: number;
  pair_age_days: number;
  contract_age_days: number;
  honeypot_can_sell: boolean | null;
  buy_tax_pct: number;
  sell_tax_pct: number;
  has_mint_function: boolean | null;
  has_blacklist: boolean | null;
  has_unrestricted_setfee: boolean | null;
  website_url: string | null;
  twitter_handle: string | null;
  github_org: string | null;
}

export interface OffchainSignals {
  website_quality: "none" | "low" | "medium" | "high";
  twitter_quality: "none" | "low" | "medium" | "high";
  github_activity: "none" | "low" | "medium" | "high";
  twitter_age_days: number;
  twitter_followers: number;
  github_last_commit_days: number;
  team_doxxed: boolean | null;
  whitepaper_present: boolean | null;
  notes: string;
}

export interface Subscription {
  subscriber: string;
  token: string;
  chain: string;
  last_bucket: string;
  last_checked: number;
}

type EthereumProvider = {
  request(args: { method: string; params?: unknown[] | Record<string, unknown> }): Promise<any>;
  on?(event: "accountsChanged" | "chainChanged", handler: (...args: any[]) => void): void;
  removeListener?(event: "accountsChanged" | "chainChanged", handler: (...args: any[]) => void): void;
  providers?: EthereumProvider[];
  isMetaMask?: boolean;
};

declare global {
  interface Window {
    ethereum?: EthereumProvider;
  }
}

export function getEthereumProvider(): EthereumProvider | undefined {
  const provider = window.ethereum;
  return (
    provider?.providers?.find(candidate => candidate.isMetaMask) ||
    (provider?.isMetaMask ? provider : undefined) ||
    provider?.providers?.[0] ||
    provider
  );
}

async function switchToBradbury(provider: EthereumProvider) {
  const chainId = `0x${testnetBradbury.id.toString(16)}`;
  try {
    await provider.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId }],
    });
  } catch (e: any) {
    if (e?.code !== 4902) {
      throw e;
    }
    await provider.request({
      method: "wallet_addEthereumChain",
      params: [
        {
          chainId,
          chainName: testnetBradbury.name,
          rpcUrls: testnetBradbury.rpcUrls.default.http,
          nativeCurrency: testnetBradbury.nativeCurrency,
          blockExplorerUrls: [testnetBradbury.blockExplorers?.default.url].filter(Boolean),
        },
      ],
    });
  }
}

async function walletClient() {
  const account = await connectWallet();
  return createClient({
    chain: testnetBradbury,
    endpoint: rpc,
    account,
    provider: getEthereumProvider(),
  });
}

export async function connectWallet(): Promise<Address> {
  const provider = getEthereumProvider();
  if (!provider) {
    throw new Error("MetaMask is required to connect a wallet.");
  }
  await switchToBradbury(provider);
  const accounts = (await provider.request({ method: "eth_requestAccounts" })) as Address[];
  const account = accounts[0];
  if (!account) {
    throw new Error("No wallet account selected.");
  }
  return account;
}

export async function getConnectedWallet(): Promise<Address | null> {
  const provider = getEthereumProvider();
  if (!provider) return null;
  try {
    const accounts = (await Promise.race([
      provider.request({ method: "eth_accounts" }),
      new Promise<[]>(resolve => window.setTimeout(() => resolve([]), 3000)),
    ])) as Address[];
    return accounts[0] ?? null;
  } catch {
    return null;
  }
}

function oracle(): Address {
  if (!/^0x[a-fA-F0-9]{40}$/.test(ORACLE_ADDRESS)) {
    throw new Error("Set VITE_ORACLE_ADDRESS to the deployed RecuseOracle address.");
  }
  return ORACLE_ADDRESS as Address;
}

const watchlistKey = "recuse.watchlist.v1";

function subKey(sub: Pick<Subscription, "subscriber" | "token" | "chain">) {
  return `${sub.subscriber.toLowerCase()}:${sub.chain}:${sub.token.toLowerCase()}`;
}

function normalizeSubscription(sub: any): Subscription | null {
  if (!sub?.subscriber || !sub?.token || !sub?.chain) return null;
  return {
    subscriber: String(sub.subscriber),
    token: String(sub.token),
    chain: String(sub.chain),
    last_bucket: String(sub.last_bucket || "unknown"),
    last_checked: Number(sub.last_checked || 0),
  };
}

export function rememberSubscription(sub: Subscription) {
  const existing = rememberedSubscriptions(sub.subscriber);
  const merged = new Map(existing.map(item => [subKey(item), item]));
  merged.set(subKey(sub), sub);
  window.localStorage.setItem(watchlistKey, JSON.stringify([...merged.values()]));
}

export function rememberedSubscriptions(who: string): Subscription[] {
  try {
    const raw = JSON.parse(window.localStorage.getItem(watchlistKey) || "[]");
    if (!Array.isArray(raw)) return [];
    return raw
      .map(normalizeSubscription)
      .filter((sub): sub is Subscription => Boolean(sub))
      .filter(sub => sub.subscriber.toLowerCase() === who.toLowerCase());
  } catch {
    return [];
  }
}

export function mergeSubscriptions(onchain: any[], cached: Subscription[]) {
  const merged = new Map<string, Subscription>();
  for (const sub of cached) merged.set(subKey(sub), sub);
  for (const raw of onchain) {
    const sub = normalizeSubscription(raw);
    if (sub) merged.set(subKey(sub), sub);
  }
  return [...merged.values()];
}

export async function assess(token: string, chain: string) {
  const client = await walletClient();
  const tx = await client.writeContract({
    address: oracle(),
    functionName: "assess",
    args: [token, chain],
    value: 0n,
  });
  return await client.waitForTransactionReceipt({
    hash: tx as TransactionHash,
    status: TransactionStatus.ACCEPTED,
  });
}

const chainToHoneypotId: Record<string, string> = {
  ethereum: "1",
  base: "8453",
  bsc: "56",
};

async function json(url: string): Promise<any> {
  const res = await fetch(url, { headers: { accept: "application/json" } });
  if (!res.ok) throw new Error(`Live data request failed: ${res.status} ${url}`);
  return await res.json();
}

function intNumber(value: unknown) {
  const n = Number(value || 0);
  return Number.isFinite(n) ? Math.max(0, Math.round(n)) : 0;
}

function buildSnapshot(dexs: any, hpot: any, chain: string) {
  const pairs = (dexs.pairs || []).filter((pair: any) => pair.chainId === chain);
  const bestPair = pairs.sort(
    (a: any, b: any) => Number(b?.liquidity?.usd || 0) - Number(a?.liquidity?.usd || 0)
  )[0] || {};
  const info = bestPair.info || {};
  const socials = info.socials || [];
  const twitter = socials.find((s: any) => /twitter\.com|x\.com/.test(s.url || ""));
  const github = socials.find((s: any) => /github\.com/.test(s.url || ""));
  const summary = hpot.summary || {};
  const simulation = hpot.simulationResult || {};
  const code = hpot.contractCode || {};

  const onchain = {
    contract_verified: Boolean(code.openSource),
    ownership_renounced: null,
    owner_active_7d: null,
    lp_locked: null,
    lp_lock_days_left: null,
    liquidity_usd: intNumber(bestPair?.liquidity?.usd || hpot?.pair?.liquidity),
    market_cap_usd: intNumber(bestPair.marketCap || bestPair.fdv),
    holder_count: intNumber(hpot?.token?.totalHolders),
    top10_pct: 0,
    pair_age_days: bestPair.pairCreatedAt || hpot?.pair?.createdAtTimestamp ? 999 : 0,
    contract_age_days: bestPair.pairCreatedAt || hpot?.pair?.createdAtTimestamp ? 999 : 0,
    honeypot_can_sell: Boolean(hpot.simulationSuccess) && !Boolean(hpot?.honeypotResult?.isHoneypot),
    buy_tax_pct: intNumber(simulation.buyTax),
    sell_tax_pct: intNumber(simulation.sellTax),
    has_mint_function: null,
    has_blacklist: null,
    has_unrestricted_setfee: null,
    website_url: info.websites?.[0]?.url || null,
    twitter_handle: twitter?.url?.replace(/\/$/, "").split("/").pop() || null,
    github_org: github?.url?.replace(/\/$/, "").split("/").pop() || null,
    source: "dexscreener_api+honeypot_api",
    risk_level: intNumber(summary.riskLevel),
    risk: summary.risk || "unknown",
    risk_flags: (summary.flags || hpot.flags || []).map((flag: any) => flag.flag || ""),
  };
  const offchain = {
    website_quality: onchain.website_url ? "medium" : "none",
    twitter_quality: onchain.twitter_handle ? "medium" : "none",
    github_activity: onchain.github_org ? "medium" : "none",
    twitter_age_days: 0,
    twitter_followers: 0,
    github_last_commit_days: onchain.github_org ? 0 : 9999,
    team_doxxed: null,
    whitepaper_present: null,
    notes: "Off-chain links are derived from DexScreener token profile metadata.",
  };
  return { onchain, offchain };
}

async function snapshotFromApi(token: string, chain: string) {
  const res = await fetch(`/api/snapshot?token=${encodeURIComponent(token)}&chain=${encodeURIComponent(chain)}`, {
    headers: { accept: "application/json" },
  });
  const contentType = res.headers.get("content-type") || "";
  if (!res.ok || !contentType.includes("application/json")) {
    throw new Error("Snapshot API is not available in this environment.");
  }
  return await res.json();
}

export async function collectLiveSnapshot(token: string, chain: string) {
  try {
    return await snapshotFromApi(token, chain);
  } catch {
    const [dexs, hpot] = await Promise.all([
      json(`https://api.dexscreener.com/latest/dex/tokens/${token}`),
      json(`https://api.honeypot.is/v2/IsHoneypot?address=${token}&chainID=${chainToHoneypotId[chain] || "1"}`),
    ]);
    return buildSnapshot(dexs, hpot, chain);
  }
}

export async function assessSnapshot(token: string, chain: string) {
  const { onchain, offchain } = await collectLiveSnapshot(token, chain);
  const client = await walletClient();
  const tx = await client.writeContract({
    address: oracle(),
    functionName: "assess_snapshot",
    args: [token, chain, onchain, offchain],
    value: 0n,
  });
  return await client.waitForTransactionReceipt({
    hash: tx as TransactionHash,
    status: TransactionStatus.ACCEPTED,
  });
}

export async function getVerdict(
  token: string,
  chain: string
): Promise<Verdict> {
  return (await gl.readContract({
    address: oracle(),
    functionName: "get_verdict",
    args: [token, chain],
  })) as unknown as Verdict;
}

export async function shouldRecuse(
  token: string,
  chain: string
): Promise<boolean> {
  return (await gl.readContract({
    address: oracle(),
    functionName: "should_recuse",
    args: [token, chain],
  })) as boolean;
}

export async function subscribe(token: string, chain: string) {
  const client = await walletClient();
  const tx = await client.writeContract({
    address: oracle(),
    functionName: "subscribe",
    args: [token, chain],
    value: 0n,
  });
  return await client.waitForTransactionReceipt({
    hash: tx as TransactionHash,
    status: TransactionStatus.ACCEPTED,
  });
}

export async function listSubscriptions(who: `0x${string}`) {
  const client = window.ethereum ? await walletClient() : gl;
  const result = await client.readContract({
    address: oracle(),
    functionName: "list_subscriptions",
    args: [who.toLowerCase()],
  });
  if (Array.isArray(result)) return result.map(normalizeSubscription).filter(Boolean);
  if (Array.isArray((result as any)?.result)) {
    return (result as any).result.map(normalizeSubscription).filter(Boolean);
  }
  if (Array.isArray((result as any)?.data)) {
    return (result as any).data.map(normalizeSubscription).filter(Boolean);
  }
  return [];
}
