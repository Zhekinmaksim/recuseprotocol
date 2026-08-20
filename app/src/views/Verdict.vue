<script setup lang="ts">
import { ref, onMounted } from "vue";
import {
  getConnectedWallet,
  getVerdict,
  rememberSubscription,
  subscribe,
  type Verdict,
  type OnchainSignals,
  type OffchainSignals,
} from "../lib/genlayer";

const props = defineProps<{ chain: string; token: string }>();

const verdict = ref<Verdict | null>(null);
const onchain = ref<OnchainSignals | null>(null);
const offchain = ref<OffchainSignals | null>(null);
const error = ref("");
const subscribed = ref(false);

function fmtUsd(n: number) {
  if (!n) return "$0";
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

function fmtBool(b: boolean | null, trueLabel = "Yes", falseLabel = "No") {
  if (b === null || b === undefined) return "Unknown";
  return b ? trueLabel : falseLabel;
}

function flagClass(good: boolean) {
  return good ? "flag-green" : "flag-red";
}

onMounted(async () => {
  try {
    const v = await getVerdict(props.token, props.chain);
    verdict.value = v;
    onchain.value = JSON.parse(v.onchain_json);
    offchain.value = JSON.parse(v.offchain_json);
  } catch (e: any) {
    error.value = e?.message || String(e);
  }
});

async function watch() {
  try {
    await subscribe(props.token, props.chain);
    const subscriber = await getConnectedWallet();
    if (subscriber) {
      rememberSubscription({
        subscriber,
        token: props.token,
        chain: props.chain,
        last_bucket: verdict.value?.bucket || "unknown",
        last_checked: Number(verdict.value?.checked_at || 0),
      });
    }
    subscribed.value = true;
  } catch (e: any) {
    error.value = e?.message || String(e);
  }
}
</script>

<template>
  <div v-if="error" class="notice error">{{ error }}</div>
  <div v-else-if="!verdict" class="notice"><span class="loader">Loading verdict</span></div>

  <article v-else>
    <header class="report-head">
      <div>
        <h1 class="title">Verdict</h1>
        <div class="subtitle">{{ chain }} · ERC-20 token</div>
        <div class="addr">{{ token }}</div>
      </div>
      <div style="text-align: right;">
        <div class="bucket-tag" :class="verdict.bucket">{{ verdict.bucket }}</div>
        <div style="font-family: var(--mono); font-size: 0.78rem; color: var(--ink-3); margin-top: 8px;">
          score {{ verdict.score }} / 100
        </div>
      </div>
    </header>

    <div class="report-grid">
      <dl class="facts">
        <template v-if="onchain">
          <dt>Contract verified</dt>
          <dd :class="flagClass(onchain.contract_verified === true)">{{ fmtBool(onchain.contract_verified) }}</dd>

          <dt>Ownership renounced</dt>
          <dd :class="flagClass(onchain.ownership_renounced === true || onchain.owner_active_7d === false)">
            {{ fmtBool(onchain.ownership_renounced) }}
          </dd>

          <dt>Liquidity locked</dt>
          <dd :class="flagClass(onchain.lp_locked === true)">
            {{ fmtBool(onchain.lp_locked) }}
            <span v-if="onchain.lp_lock_days_left" style="color: var(--ink-3);">· {{ onchain.lp_lock_days_left }}d left</span>
          </dd>

          <dt>Liquidity (USD)</dt>
          <dd>{{ fmtUsd(onchain.liquidity_usd) }}</dd>

          <dt>Market cap</dt>
          <dd>{{ fmtUsd(onchain.market_cap_usd) }}</dd>

          <dt>Holders</dt>
          <dd>{{ onchain.holder_count.toLocaleString() }}</dd>

          <dt>Top-10 concentration</dt>
          <dd :class="flagClass(onchain.top10_pct < 50)">{{ onchain.top10_pct.toFixed(1) }}%</dd>

          <dt>Pair age</dt>
          <dd>{{ onchain.pair_age_days }} days</dd>

          <dt>Can sell (honeypot)</dt>
          <dd :class="flagClass(onchain.honeypot_can_sell === true)">{{ fmtBool(onchain.honeypot_can_sell) }}</dd>

          <dt>Buy / sell tax</dt>
          <dd>{{ onchain.buy_tax_pct }}% / {{ onchain.sell_tax_pct }}%</dd>
        </template>

        <template v-if="offchain">
          <dt style="padding-top: 24px;">Website quality</dt>
          <dd>{{ offchain.website_quality }}</dd>

          <dt>Twitter quality</dt>
          <dd>
            {{ offchain.twitter_quality }}
            <span v-if="offchain.twitter_followers" style="color: var(--ink-3);">· {{ offchain.twitter_followers.toLocaleString() }} followers</span>
          </dd>

          <dt>GitHub activity</dt>
          <dd>
            {{ offchain.github_activity }}
            <span v-if="offchain.github_last_commit_days < 9999" style="color: var(--ink-3);">· {{ offchain.github_last_commit_days }}d since last commit</span>
          </dd>

          <dt>Team doxxed</dt>
          <dd :class="flagClass(offchain.team_doxxed === true)">{{ fmtBool(offchain.team_doxxed) }}</dd>
        </template>
      </dl>

      <div>
        <p class="reasoning">{{ verdict.reasoning }}</p>

        <div class="flags" v-if="offchain?.notes">
          <h3>Observation</h3>
          <p style="font-family: var(--mono); font-size: 0.9rem; color: var(--ink-2);">{{ offchain.notes }}</p>
        </div>

        <div style="margin-top: 48px; padding-top: 24px; border-top: var(--rule); display: flex; gap: 16px;">
          <button v-if="!subscribed" @click="watch">Add to watchlist</button>
          <span v-else style="font-family: var(--mono); font-size: 0.82rem; color: var(--moss); letter-spacing: 0.06em;">✓ WATCHED</span>
          <router-link to="/" style="text-decoration: none;">
            <button class="ghost">Request another verdict</button>
          </router-link>
        </div>

        <div style="margin-top: 32px; font-family: var(--mono); font-size: 0.72rem; color: var(--ink-3); letter-spacing: 0.06em;">
          ASSESSED AT BLOCK TIMESTAMP {{ verdict.checked_at }} · SCHEMA v{{ verdict.version }}
        </div>
      </div>
    </div>
  </article>
</template>
