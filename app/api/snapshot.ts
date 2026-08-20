const chainToHoneypotId: Record<string, string> = {
  ethereum: "1",
  base: "8453",
  bsc: "56",
};

async function json(url: string) {
  const res = await fetch(url, { headers: { accept: "application/json" } });
  if (!res.ok) {
    throw new Error(`Live data request failed: ${res.status} ${url}`);
  }
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

export default async function handler(req: any, res: any) {
  const token = String(req.query.token || "");
  const chain = String(req.query.chain || "ethereum");

  if (!/^0x[a-fA-F0-9]{40}$/.test(token)) {
    res.status(400).json({ error: "Invalid ERC-20 address." });
    return;
  }

  try {
    const [dexs, hpot] = await Promise.all([
      json(`https://api.dexscreener.com/latest/dex/tokens/${token}`),
      json(`https://api.honeypot.is/v2/IsHoneypot?address=${token}&chainID=${chainToHoneypotId[chain] || "1"}`),
    ]);
    res.setHeader("Cache-Control", "s-maxage=60, stale-while-revalidate=300");
    res.status(200).json(buildSnapshot(dexs, hpot, chain));
  } catch (e: any) {
    res.status(502).json({ error: e?.message || String(e) });
  }
}
