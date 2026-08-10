<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { assessSnapshot, getVerdict } from "../lib/genlayer";

const token = ref("");
const chain = ref("ethereum");
const status = ref<"idle" | "loading" | "error">("idle");
const error = ref("");
const router = useRouter();

const CHAINS = ["ethereum", "base", "arbitrum", "polygon", "bsc", "optimism"];

async function run() {
  error.value = "";
  if (!/^0x[a-fA-F0-9]{40}$/.test(token.value)) {
    error.value = "Invalid ERC-20 address.";
    return;
  }
  status.value = "loading";
  try {
    try {
      await getVerdict(token.value, chain.value);
    } catch {
      await assessSnapshot(token.value, chain.value);
    }
    router.push(`/verdict/${chain.value}/${token.value}`);
  } catch (e: any) {
    status.value = "error";
    error.value = e?.message || String(e);
  }
}
</script>

<template>
  <section>
    <h1 style="font-family: var(--serif); font-weight: 500; font-size: 2.6rem; line-height: 1.1; margin-bottom: 8px;">
      Should your contract step aside from this token?
    </h1>
    <p style="color: var(--ink-3); font-size: 1.05rem; margin-bottom: 32px; max-width: 56ch;">
      A live token snapshot is written to a GenLayer contract, scored by
      a deterministic rubric, and returned as one of four verdicts. Integrating contracts use the verdict to
      decide whether to proceed, hold, or recuse themselves from the transaction.
    </p>

    <div class="search-block">
      <input
        v-model="token"
        type="text"
        placeholder="0x… ERC-20 contract address"
        @keyup.enter="run"
      />
      <select v-model="chain">
        <option v-for="c in CHAINS" :key="c" :value="c">{{ c }}</option>
      </select>
      <button @click="run" :disabled="status === 'loading'">
        <span v-if="status !== 'loading'">Request verdict</span>
        <span v-else class="loader">Reaching consensus</span>
      </button>
    </div>

    <div v-if="error" class="notice error">{{ error }}</div>

    <section style="margin-top: 48px;">
      <h2 style="font-size: 1.4rem; font-weight: 500; margin-bottom: 16px; border-bottom: var(--rule); padding-bottom: 8px;">
        The four verdicts
      </h2>
      <dl style="font-family: var(--mono); font-size: 0.88rem; line-height: 1.65;">
        <div style="display: grid; grid-template-columns: 120px 1fr; gap: 16px; padding: 12px 0; border-bottom: var(--rule);">
          <span class="bucket-tag clear" style="justify-self: start;">CLEAR</span>
          <span>Integrating contract may proceed without restriction.</span>
        </div>
        <div style="display: grid; grid-template-columns: 120px 1fr; gap: 16px; padding: 12px 0; border-bottom: var(--rule);">
          <span class="bucket-tag watch" style="justify-self: start;">WATCH</span>
          <span>Proceed but log; soft warning to the user; reassess sooner.</span>
        </div>
        <div style="display: grid; grid-template-columns: 120px 1fr; gap: 16px; padding: 12px 0; border-bottom: var(--rule);">
          <span class="bucket-tag flag" style="justify-self: start;">FLAG</span>
          <span>Hold; require explicit user override; show full reasoning.</span>
        </div>
        <div style="display: grid; grid-template-columns: 120px 1fr; gap: 16px; padding: 12px 0;">
          <span class="bucket-tag recuse" style="justify-self: start;">RECUSE</span>
          <span>Integrating contract must step aside. Transaction does not proceed.</span>
        </div>
      </dl>
    </section>

    <section style="margin-top: 48px;">
      <h2 style="font-size: 1.4rem; font-weight: 500; margin-bottom: 16px; border-bottom: var(--rule); padding-bottom: 8px;">
        How a verdict is reached
      </h2>
      <ol style="font-family: var(--mono); font-size: 0.85rem; line-height: 1.9; padding-left: 24px;">
        <li>The application fetches a fresh DexScreener and Honeypot.is snapshot at request time.</li>
        <li>The connected wallet signs an assess_snapshot transaction to RecuseOracle on Bradbury.</li>
        <li>Off-chain links from token metadata are folded into a compact footprint score.</li>
        <li>A deterministic risk rubric assigns CLEAR, WATCH, FLAG, or RECUSE.</li>
        <li>GenLayer validators agree on the transaction and persist the verdict in contract storage.</li>
        <li>The verdict page reads the stored struct back from the contract.</li>
      </ol>
    </section>
  </section>
</template>
