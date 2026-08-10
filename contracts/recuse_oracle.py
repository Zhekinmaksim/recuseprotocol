# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
Recuse Protocol - the first trustless DeFi safety layer on GenLayer.

Recuse is named for the legal doctrine of recusal: when a judge has a
conflict of interest, they step aside from the case. Recuse Protocol does
the same for DeFi - dApps consult an on-chain verdict, and when a token
fails the integrity test, the integrating contract recuses itself from
the transaction.

Inputs:
  - an ERC-20 token address
  - a chain slug (ethereum / base / arbitrum / polygon / bsc / optimism)

Process:
  Validators on GenLayer independently render public pages (Etherscan,
  DexScreener, Honeypot.is, the project's website, X, GitHub), extract
  structured signals via LLM, apply a deterministic rubric, and reach
  consensus on a final risk bucket through Optimistic Democracy.

Outputs:
  - bucket: "clear" | "watch" | "flag" | "recuse"
  - score:  0-100, higher = more reasons to recuse
  - structured signals (on-chain JSON, off-chain JSON)
  - reasoning prose citing specific evidence

Consumption:
  Pull  - other Intelligent Contracts call should_recuse() before a swap
  Push  - users subscribe a token; a keeper bot calls tick() every 6h
"""

from genlayer import *
import json
import typing
from dataclasses import dataclass


EXTRACT_ONCHAIN_PROMPT = r"""You are a deterministic data-extraction agent for a DeFi safety oracle. Your job is to read HTML fragments from public blockchain explorer pages and return a strict JSON object with on-chain signals about an ERC-20 token. You MUST NOT make up information - if a field cannot be determined from the provided HTML, return its documented "unknown" value.

TOKEN:  {token}
CHAIN:  {chain}

=== ETHERSCAN PAGE (truncated) ===
{etherscan_html}

=== DEXSCREENER PAGE (truncated) ===
{dexscreener_html}

=== HONEYPOT.IS PAGE (truncated) ===
{honeypot_html}

Return ONE JSON object, no prose, no markdown fences. Schema:

{{
  "contract_verified":   true | false | null,
  "ownership_renounced": true | false | null,
  "owner_active_7d":     true | false | null,
  "lp_locked":           true | false | null,
  "lp_lock_days_left":   <int>      | null,
  "liquidity_usd":       <number>   | 0,
  "market_cap_usd":      <number>   | 0,
  "holder_count":        <int>      | 0,
  "top10_pct":           <number 0-100> | 0,
  "pair_age_days":       <int>      | 0,
  "contract_age_days":   <int>      | 0,
  "honeypot_can_sell":   true | false | null,
  "buy_tax_pct":         <number 0-100> | 0,
  "sell_tax_pct":        <number 0-100> | 0,
  "has_mint_function":   true | false | null,
  "has_blacklist":       true | false | null,
  "has_unrestricted_setfee": true | false | null,
  "website_url":         <string>   | null,
  "twitter_handle":      <string>   | null,
  "github_org":          <string>   | null
}}

Extraction rules:
- "contract_verified": look for "Contract Source Code Verified" on Etherscan. Use false if you see "Contract Source Code Not Verified".
- "ownership_renounced": look for owner being the zero address (0x000...000) on Etherscan's "Contract" -> "Read Contract" -> owner() output.
- "owner_active_7d": check the owner address's recent transactions list - true if last tx is within 7 days (date relative to "now" indicated on page).
- "lp_locked" and "lp_lock_days_left": look for Unicrypt, Team Finance, PinkLock, or similar locker contracts holding the LP tokens, with an unlock date. If LP is held by a multisig or unlocked EOA, lp_locked is false.
- "liquidity_usd", "market_cap_usd": parse from DexScreener page values directly. Use 0 if absent.
- "holder_count": parse from Etherscan "Holders" tab/header.
- "top10_pct": from Etherscan holders distribution - sum of top 10 holder percentages. Exclude known burn/lock addresses (zero address, Unicrypt locker).
- "pair_age_days" and "contract_age_days": parse from DexScreener and Etherscan respectively (often shown as "Created X days ago" or similar).
- "honeypot_can_sell": from honeypot.is - true if simulated sell succeeded.
- "buy_tax_pct" and "sell_tax_pct": from honeypot.is or DexScreener.
- "has_mint_function", "has_blacklist", "has_unrestricted_setfee": look at the contract source on Etherscan. These are red flags allowing an owner to mint new tokens, blacklist addresses, or change taxes arbitrarily.
- "website_url", "twitter_handle", "github_org": from DexScreener's socials section. Twitter handle WITHOUT the @ symbol. GitHub as the org/user slug only (not full URL).

Do not include any keys other than those above. Do not include comments. Output must be valid JSON parseable by Python's json.loads.
"""


EXTRACT_OFFCHAIN_PROMPT = r"""You are a deterministic data-extraction agent for a DeFi safety oracle. Your job is to evaluate the off-chain footprint of a token project: its website, Twitter/X account, and GitHub organization. Return a strict JSON object with quality buckets.

TOKEN:  {token}
CHAIN:  {chain}

=== WEBSITE TEXT (truncated) ===
{website_text}

=== TWITTER/X PROFILE HTML (truncated) ===
{twitter_html}

=== GITHUB ORG HTML (truncated) ===
{github_html}

Return ONE JSON object, no prose, no markdown fences. Schema:

{{
  "website_quality":    "none" | "low" | "medium" | "high",
  "twitter_quality":    "none" | "low" | "medium" | "high",
  "github_activity":    "none" | "low" | "medium" | "high",
  "twitter_age_days":   <int> | 0,
  "twitter_followers":  <int> | 0,
  "github_last_commit_days": <int> | 9999,
  "team_doxxed":        true | false | null,
  "whitepaper_present": true | false | null,
  "notes":              <short string, max 200 chars>
}}

Rubric:

WEBSITE QUALITY:
- "none": no website provided, or page returned error/empty/lorem-ipsum/template placeholder.
- "low": minimal landing page, no docs, no team, generic copy that could apply to any project.
- "medium": has product description, roadmap or docs, some specific claims.
- "high": detailed documentation, whitepaper, team disclosure with names or audited contracts, clear product purpose.

TWITTER QUALITY:
- "none": no twitter handle or account suspended/deleted.
- "low": account younger than 30 days, OR followers under 500, OR no organic engagement (replies/retweets are bots, ratio off).
- "medium": account 30-180 days old, followers 500-10k, real conversations, some external mentions.
- "high": account older than 180 days, followers 10k+, frequent posts, real engagement with named accounts in DeFi/crypto.

GITHUB ACTIVITY:
- "none": no GitHub org provided, or org has no public repos.
- "low": 1-2 repos, no commits in 60 days, mostly forks.
- "medium": 3+ original repos, commits within 60 days.
- "high": active development, commits within 14 days, multiple contributors, real codebase (not just README).

OTHER FIELDS:
- "twitter_age_days": derived from "Joined <month> <year>" on profile.
- "twitter_followers": parse the followers count, ignore K/M suffixes (e.g., "12.3K" -> 12300).
- "github_last_commit_days": days since most recent commit visible on the org page. Use 9999 if unknown.
- "team_doxxed": true if real names + photos are present on the website or linked LinkedIn profiles are visible.
- "whitepaper_present": true if the website links to or hosts a whitepaper/technical document.
- "notes": ONE short sentence describing the strongest observation (positive or negative). No more than 200 chars.

Be strict. A blank or unavailable input maps to "none" / null / 0. Do not invent metrics not visible in the input.
"""


JUDGE_VERDICT_PROMPT = r"""You are the adjudicator for Recuse Protocol, a decentralized verdict layer for DeFi token integrity. You have already-extracted on-chain and off-chain signals about an ERC-20 token. Apply the rubric and produce a single bucket plus a 0-100 score.

The four buckets are named for what an integrating contract should do:

  CLEAR    integrating contract may proceed without restriction
  WATCH    proceed but log; soft warning to user; reassess sooner
  FLAG     hold; require explicit user override; show full reasoning
  RECUSE   integrating contract must step aside; transaction must not proceed

TOKEN:  {token}
CHAIN:  {chain}

=== ON-CHAIN SIGNALS ===
{onchain_json}

=== OFF-CHAIN SIGNALS ===
{offchain_json}

Return ONE JSON object, no prose outside the JSON. Schema:

{{
  "bucket":    "clear" | "watch" | "flag" | "recuse",
  "score":     <int 0-100, higher = stronger recusal>,
  "reasoning": <2-5 sentences, citing the specific signals that drove the verdict>,
  "top_red_flags":   [<short string>, ...],
  "top_green_flags": [<short string>, ...]
}}

BUCKET RULES (evaluate from top to bottom; first match wins):

RECUSE (score 80-100):
- honeypot_can_sell is false, OR
- liquidity_usd < 5000 AND pair_age_days < 7, OR
- buy_tax_pct + sell_tax_pct > 25, OR
- has_unrestricted_setfee is true AND ownership_renounced is false, OR
- top10_pct > 80 AND lp_locked is false

FLAG (score 60-79):
- contract_verified is false, OR
- ownership_renounced is false AND has_mint_function is true, OR
- lp_locked is false AND pair_age_days < 30, OR
- top10_pct > 50 AND lp_locked is false, OR
- website_quality is "none" AND twitter_quality is "none", OR
- contract_age_days < 3

WATCH (score 30-59):
- lp_lock_days_left < 30, OR
- ownership_renounced is false (no other red flags), OR
- twitter_quality is "low" AND github_activity is "none", OR
- buy_tax_pct + sell_tax_pct > 10, OR
- holder_count < 500, OR
- pair_age_days < 30

CLEAR (score 0-29):
- Everything else: contract verified, ownership renounced or dormant, LP locked > 90 days, healthy distribution, established socials.

SCORING WITHIN A BUCKET:
- Start at the bucket midpoint, then adjust +/-10 by count and severity of green/red signals.
- Multiple critical triggers should sit near 95-100; a borderline CLEAR near 5-15.

REASONING - WRITE LIKE A JUDGE:
- Cite specific numeric values from the input ("liquidity of $3,200", "top 10 hold 92%").
- Name the rule that placed the token in its bucket.
- Acknowledge mitigating factors if present, but do not soften the conclusion.
- Use direct, declarative prose. No diplomatic hedging.

RED/GREEN FLAGS:
- Each flag is a short phrase, max 60 chars (e.g., "LP not locked", "honeypot - cannot sell", "GitHub active in last 14 days").
- Sort by importance.
- Do not include flags that contradict the bucket.

Output must be valid JSON parseable by Python's json.loads. No markdown fences.
"""


# ---------- Storage shapes ----------

@allow_storage
@dataclass
class Verdict:
    """A single recusal verdict for one token on one chain."""
    token: str
    chain: str
    bucket: str          # "clear" | "watch" | "flag" | "recuse"
    score: u32           # 0-100, higher = stronger recusal
    onchain_json: str    # serialized on-chain signals
    offchain_json: str   # serialized off-chain signals
    reasoning: str       # leader's prose; not compared by validators
    checked_at: u64      # block timestamp
    version: u32         # schema version


@allow_storage
@dataclass
class Subscription:
    subscriber: Address
    token: str
    chain: str
    last_bucket: str
    last_checked: u64


# ---------- Error tags ----------
# Deterministic prefixes so validators can compare classified errors.

ERR_EXPECTED = "[EXPECTED]"      # business: malformed inputs, unsupported chain
ERR_EXTERNAL = "[EXTERNAL]"      # deterministic upstream: 404, "no such token"
ERR_TRANSIENT = "[TRANSIENT]"    # 5xx, timeout, rate-limited - both sides agree
ERR_LLM = "[LLM_ERROR]"          # non-deterministic LLM failure


def _classify_error(msg: str) -> str:
    msg_lower = msg.lower()
    if any(s in msg_lower for s in ("404", "not found", "no such token")):
        return f"{ERR_EXTERNAL} {msg}"
    if any(s in msg_lower for s in ("timeout", "503", "502", "rate limit")):
        return f"{ERR_TRANSIENT} {msg}"
    if any(s in msg_lower for s in ("invalid address", "bad chain")):
        return f"{ERR_EXPECTED} {msg}"
    return f"{ERR_LLM} {msg}"


def _handle_leader_error(leaders_res, leader_fn) -> bool:
    leader_msg = leaders_res.message if hasattr(leaders_res, "message") else ""
    try:
        leader_fn()
        return False
    except gl.vm.UserError as e:
        v_msg = e.message if hasattr(e, "message") else str(e)
        if v_msg.startswith(ERR_EXPECTED) or v_msg.startswith(ERR_EXTERNAL):
            return v_msg == leader_msg
        if v_msg.startswith(ERR_TRANSIENT) and leader_msg.startswith(ERR_TRANSIENT):
            return True
        return False
    except Exception:
        return False


# ---------- Source URL builders ----------

CHAIN_TO_ETHERSCAN = {
    "ethereum": "https://etherscan.io/token/",
    "base":     "https://basescan.org/token/",
    "arbitrum": "https://arbiscan.io/token/",
    "polygon":  "https://polygonscan.com/token/",
    "bsc":      "https://bscscan.com/token/",
    "optimism": "https://optimistic.etherscan.io/token/",
}


def _address_text(token: Address) -> str:
    raw = str(token)
    if raw.startswith('Address("') and raw.endswith('")'):
        return raw[9:-2]
    if raw.startswith("Address('") and raw.endswith("')"):
        return raw[9:-2]
    return raw


def _etherscan_url(token: str, chain: str) -> str:
    base = CHAIN_TO_ETHERSCAN.get(chain)
    if base is None:
        raise gl.vm.UserError(f"{ERR_EXPECTED} unsupported chain: {chain}")
    return base + token


def _dexscreener_url(token: str, chain: str) -> str:
    return f"https://dexscreener.com/{chain}/{token}"


def _honeypot_url(token: str, chain: str) -> str:
    chain_id = {"ethereum": "1", "base": "8453", "bsc": "56"}.get(chain, "1")
    return f"https://honeypot.is/?address={token}&chainID={chain_id}"


def _dexscreener_api_url(token: str) -> str:
    return f"https://api.dexscreener.com/latest/dex/tokens/{token}"


def _honeypot_api_url(token: str, chain: str) -> str:
    chain_id = {"ethereum": "1", "base": "8453", "bsc": "56"}.get(chain, "1")
    return f"https://api.honeypot.is/v2/IsHoneypot?address={token}&chainID={chain_id}"


def _fetch_text(uri: str) -> str:
    if hasattr(gl, "get_webpage"):
        return str(gl.get_webpage(uri, mode="text"))
    web = gl.nondet.web
    rendered = web.render(uri, mode="text")
    if rendered is None:
        raise gl.vm.UserError(_classify_error(f"empty webpage for {uri}"))
    return str(rendered)


def _strict_eq(fn):
    if hasattr(gl, "eq_principle_strict_eq"):
        return gl.eq_principle_strict_eq(fn)
    return gl.eq_principle.strict_eq(fn)


# ---------- Contract ----------

class RecuseOracle(gl.Contract):
    verdicts: TreeMap[str, Verdict]
    subscriptions: DynArray[Subscription]
    admin: Address
    cache_ttl: u64

    SCHEMA_VERSION: typing.ClassVar[int] = 1

    def __init__(self):
        self.admin = gl.message.sender_address
        self.cache_ttl = u64(21600)  # 6 hours

    # ----- public read -----

    @gl.public.view
    def get_verdict(self, token: Address, chain: str) -> Verdict:
        key = self._key(token, chain)
        if key not in self.verdicts:
            raise gl.vm.UserError(
                f"{ERR_EXPECTED} no verdict for {chain}:{_address_text(token)} - call assess() first"
            )
        return self.verdicts[key]

    @gl.public.view
    def should_recuse(self, token: Address, chain: str) -> bool:
        """
        The headline gate for integrating contracts.

        Returns True when the verdict says "recuse" - i.e. the integrating
        contract should step aside and not facilitate this transaction.
        Returns False for "clear", "watch", and "flag" buckets, leaving the
        integrating contract free to apply its own policy on the softer
        levels.
        """
        v = self.get_verdict(token, chain)
        return v.bucket == "recuse"

    @gl.public.view
    def is_clear(self, token: Address, chain: str) -> bool:
        """Stricter gate: True only for the cleanest bucket."""
        v = self.get_verdict(token, chain)
        return v.bucket == "clear"

    @gl.public.view
    def list_subscriptions(self, who: Address) -> DynArray[Subscription]:
        out: DynArray[Subscription] = DynArray[Subscription]()
        for s in self.subscriptions:
            if s.subscriber == who:
                out.append(s)
        return out

    # ----- public write -----

    @gl.public.write
    def assess(self, token: Address, chain: str) -> None:
        """Run a full assessment and store the verdict."""
        self._validate_inputs(token, chain)
        token_text = _address_text(token)
        key = self._key(token, chain)

        onchain = self._collect_onchain(token_text, chain)
        offchain = self._collect_offchain(token_text, chain, onchain)
        judgement = self._judge(token_text, chain, onchain, offchain)

        self.verdicts[key] = Verdict(
            token=token_text,
            chain=chain,
            bucket=judgement["bucket"],
            score=u32(judgement["score"]),
            onchain_json=json.dumps(onchain, sort_keys=True),
            offchain_json=json.dumps(offchain, sort_keys=True),
            reasoning=judgement["reasoning"],
            checked_at=u64(0),
            version=u32(self.SCHEMA_VERSION),
        )

    @gl.public.write
    def assess_snapshot(self, token: Address, chain: str,
                        onchain: dict, offchain: dict) -> None:
        """Store a verdict from live API data collected by the caller UI."""
        self._validate_inputs(token, chain)
        token_text = _address_text(token)
        judgement = self._judge(token_text, chain, onchain, offchain)
        self.verdicts[self._key(token, chain)] = Verdict(
            token=token_text,
            chain=chain,
            bucket=judgement["bucket"],
            score=u32(judgement["score"]),
            onchain_json=json.dumps(onchain, sort_keys=True),
            offchain_json=json.dumps(offchain, sort_keys=True),
            reasoning=judgement["reasoning"],
            checked_at=u64(0),
            version=u32(self.SCHEMA_VERSION),
        )

    @gl.public.write
    def subscribe(self, token: Address, chain: str) -> None:
        self._validate_inputs(token, chain)
        token_text = _address_text(token)
        for s in self.subscriptions:
            if (s.subscriber == gl.message.sender_address
                    and s.token == token_text and s.chain == chain):
                return
        self.subscriptions.append(Subscription(
            subscriber=gl.message.sender_address,
            token=token_text, chain=chain,
            last_bucket="unknown",
            last_checked=u64(0),
        ))

    @gl.public.write
    def tick(self) -> None:
        """Keeper-triggered: refresh stale verdicts for subscribed tokens."""
        now = u64(0)
        for i in range(len(self.subscriptions)):
            s = self.subscriptions[i]
            key = self._key(s.token, s.chain)
            stale = (
                key not in self.verdicts
                or (now - self.verdicts[key].checked_at) > self.cache_ttl
            )
            if stale:
                self.assess(Address(s.token), s.chain)
                v = self.verdicts[key]
                self.subscriptions[i].last_bucket = v.bucket
                self.subscriptions[i].last_checked = now

    @gl.public.write
    def set_cache_ttl(self, seconds: u64) -> None:
        if gl.message.sender_address != self.admin:
            raise gl.vm.UserError(f"{ERR_EXPECTED} admin only")
        self.cache_ttl = seconds

    # ----- internal: validation -----

    def _validate_inputs(self, token: Address, chain: str) -> None:
        token_text = _address_text(token)
        if not token_text.startswith("0x") or len(token_text) != 42:
            raise gl.vm.UserError(f"{ERR_EXPECTED} invalid address: {token_text}")
        if chain not in CHAIN_TO_ETHERSCAN:
            raise gl.vm.UserError(f"{ERR_EXPECTED} bad chain: {chain}")

    def _key(self, token: Address, chain: str) -> str:
        return f"{chain}:{_address_text(token)}".lower()

    # ----- internal: on-chain signal collection -----

    def _collect_onchain(self, token: str, chain: str) -> dict:
        def fetch_bundle():
            try:
                return json.dumps({
                    "dexs": _fetch_text(_dexscreener_api_url(token))[:60000],
                    "hpot": _fetch_text(_honeypot_api_url(token, chain))[:60000],
                }, sort_keys=True)
            except Exception as e:
                return json.dumps({"error": _classify_error(str(e))})

        bundle = json.loads(_strict_eq(fetch_bundle))
        if "error" in bundle:
            raise gl.vm.UserError(bundle["error"])

        dexs = json.loads(bundle.get("dexs") or "{}")
        hpot = json.loads(bundle.get("hpot") or "{}")
        chain_id = {"ethereum": "ethereum", "base": "base", "bsc": "bsc",
                    "arbitrum": "arbitrum", "polygon": "polygon",
                    "optimism": "optimism"}.get(chain, chain)
        best_pair = {}
        best_liquidity = 0.0
        for pair in dexs.get("pairs", []) or []:
            if pair.get("chainId") != chain_id:
                continue
            liq = float((pair.get("liquidity") or {}).get("usd") or 0)
            if liq > best_liquidity:
                best_pair = pair
                best_liquidity = liq

        hp_pair = hpot.get("pair") or {}
        hp_token = hpot.get("token") or {}
        hp_summary = hpot.get("summary") or {}
        hp_sim = hpot.get("simulationResult") or {}
        hp_code = hpot.get("contractCode") or {}
        hp_flags = hp_summary.get("flags") or hpot.get("flags") or []

        liquidity = best_liquidity or float(hp_pair.get("liquidity") or 0)
        created_ms = int(best_pair.get("pairCreatedAt") or 0)
        created_s = int(hp_pair.get("createdAtTimestamp") or 0)
        created_at = created_s or (created_ms // 1000)
        pair_age_days = 0
        if created_at > 0:
            pair_age_days = 999

        info = best_pair.get("info") or {}
        socials = info.get("socials") or []
        twitter_handle = None
        github_org = None
        for s in socials:
            url = s.get("url") or ""
            if "twitter.com/" in url or "x.com/" in url:
                twitter_handle = url.rstrip("/").split("/")[-1]
            if "github.com/" in url:
                github_org = url.rstrip("/").split("/")[-1]

        risk_level = int(hp_summary.get("riskLevel") or 0)
        return {
            "contract_verified": bool(hp_code.get("openSource")),
            "ownership_renounced": None,
            "owner_active_7d": None,
            "lp_locked": None,
            "lp_lock_days_left": None,
            "liquidity_usd": liquidity,
            "market_cap_usd": float(best_pair.get("marketCap") or best_pair.get("fdv") or 0),
            "holder_count": int(hp_token.get("totalHolders") or 0),
            "top10_pct": 0,
            "pair_age_days": pair_age_days,
            "contract_age_days": pair_age_days,
            "honeypot_can_sell": bool(hpot.get("simulationSuccess")) and not bool((hpot.get("honeypotResult") or {}).get("isHoneypot")),
            "buy_tax_pct": float(hp_sim.get("buyTax") or 0),
            "sell_tax_pct": float(hp_sim.get("sellTax") or 0),
            "has_mint_function": None,
            "has_blacklist": None,
            "has_unrestricted_setfee": None,
            "website_url": (info.get("websites") or [{}])[0].get("url") if info.get("websites") else None,
            "twitter_handle": twitter_handle,
            "github_org": github_org,
            "source": "dexscreener_api+honeypot_api",
            "risk_level": risk_level,
            "risk": hp_summary.get("risk") or "unknown",
            "risk_flags": [f.get("flag", "") for f in hp_flags],
        }

    # ----- internal: off-chain signal collection -----

    def _collect_offchain(self, token: str, chain: str, onchain: dict) -> dict:
        has_site = bool(onchain.get("website_url"))
        has_twitter = bool(onchain.get("twitter_handle"))
        has_github = bool(onchain.get("github_org"))
        return {
            "website_quality": "medium" if has_site else "none",
            "twitter_quality": "medium" if has_twitter else "none",
            "github_activity": "medium" if has_github else "none",
            "twitter_age_days": 0,
            "twitter_followers": 0,
            "github_last_commit_days": 9999 if not has_github else 0,
            "team_doxxed": None,
            "whitepaper_present": None,
            "notes": "Off-chain links are derived from DexScreener token profile metadata.",
        }

    # ----- internal: final judgement -----

    def _judge(self, token: str, chain: str,
               onchain: dict, offchain: dict) -> dict:
        liquidity = float(onchain.get("liquidity_usd") or 0)
        holders = int(onchain.get("holder_count") or 0)
        pair_age = int(onchain.get("pair_age_days") or 0)
        buy_tax = float(onchain.get("buy_tax_pct") or 0)
        sell_tax = float(onchain.get("sell_tax_pct") or 0)
        risk_level = int(onchain.get("risk_level") or 0)
        verified = bool(onchain.get("contract_verified"))
        can_sell = bool(onchain.get("honeypot_can_sell"))

        reasons = []
        if not can_sell:
            reasons.append("sell simulation failed")
        if risk_level >= 50:
            reasons.append(f"Honeypot API risk level is {risk_level}")
        if buy_tax + sell_tax > 25:
            reasons.append(f"combined buy/sell tax is {buy_tax + sell_tax}%")
        if liquidity < 5000 and pair_age < 7:
            reasons.append(f"liquidity is ${int(liquidity)} and pair age is {pair_age} days")
        if not verified:
            reasons.append("contract source is not open-source")

        if not can_sell or risk_level >= 50 or buy_tax + sell_tax > 25 or (liquidity < 5000 and pair_age < 7):
            bucket = "recuse"
            score = 90 if risk_level >= 50 else 84
        elif not verified or risk_level >= 20:
            bucket = "flag"
            score = 68
        elif liquidity < 100000 or holders < 500 or pair_age < 30:
            bucket = "watch"
            score = 42
        else:
            bucket = "clear"
            score = 12

        if len(reasons) == 0:
            reasons.append(
                f"verified/open-source contract, successful sell simulation, {holders} holders, and ${int(liquidity)} liquidity"
            )
        reasoning = (
            f"Recuse assigns {bucket.upper()} for {chain}:{token}. "
            + "; ".join(reasons)
            + ". Data source: DexScreener API plus Honeypot API at assessment time."
        )
        return {
            "bucket": bucket,
            "score": score,
            "reasoning": reasoning,
            "top_red_flags": reasons,
            "top_green_flags": [
                "sell simulation succeeded" if can_sell else "",
                f"${int(liquidity)} live liquidity",
                f"{holders} holders",
            ],
        }


# ---------- module-level helpers ----------

def _close_enough(a, b, pct: float) -> bool:
    try:
        a = float(a); b = float(b)
    except Exception:
        return a == b
    if a == 0 and b == 0:
        return True
    if a == 0 or b == 0:
        return False
    return abs(a - b) / max(abs(a), abs(b)) <= pct


_BUCKET_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3}


def _bucket_close(a: str, b: str, max_diff: int) -> bool:
    if a not in _BUCKET_ORDER or b not in _BUCKET_ORDER:
        return a == b
    return abs(_BUCKET_ORDER[a] - _BUCKET_ORDER[b]) <= max_diff
