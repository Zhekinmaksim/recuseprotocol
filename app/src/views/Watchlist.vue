<script setup lang="ts">
import { ref, onMounted } from "vue";
import { listSubscriptions, gl } from "../lib/genlayer";

const subs = ref<any[]>([]);
const error = ref("");
const loading = ref(true);

onMounted(async () => {
  try {
    const me = (gl as any).account?.address || "0x0000000000000000000000000000000000000000";
    subs.value = (await listSubscriptions(me as `0x${string}`)) as any[];
  } catch (e: any) {
    error.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <h1 style="font-family: var(--serif); font-weight: 500; font-size: 2.2rem; margin-bottom: 24px;">Watchlist</h1>
  <p style="color: var(--ink-3); margin-bottom: 32px; max-width: 56ch;">
    A keeper calls <code style="font-family: var(--mono);">tick()</code> every 6 hours.
    When a verdict bucket shifts (CLEAR → FLAG, FLAG → RECUSE), the new state is
    written on-chain and visible here.
  </p>

  <div v-if="loading" class="notice"><span class="loader">Loading</span></div>
  <div v-else-if="error" class="notice error">{{ error }}</div>
  <div v-else-if="subs.length === 0" class="notice">
    No tokens watched yet. Start with a check.
  </div>

  <table v-else class="watchlist">
    <thead>
      <tr>
        <th style="width: 12%;">Chain</th>
        <th style="width: 48%;">Address</th>
        <th style="width: 20%;">Last verdict</th>
        <th style="width: 20%;">Last checked</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(s, i) in subs" :key="i">
        <td>{{ s.chain }}</td>
        <td><router-link :to="`/verdict/${s.chain}/${s.token}`">{{ s.token }}</router-link></td>
        <td>
          <span class="bucket-tag" :class="s.last_bucket" style="font-size: 0.72rem; padding: 4px 8px;">{{ s.last_bucket }}</span>
        </td>
        <td>{{ s.last_checked || "—" }}</td>
      </tr>
    </tbody>
  </table>
</template>
