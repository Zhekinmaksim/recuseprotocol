<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute } from "vue-router";
import { connectWallet, getConnectedWallet } from "./lib/genlayer";

const route = useRoute();
const today = new Date().toISOString().slice(0, 10);
const wallet = ref("");
const walletError = ref("");
const connecting = ref(false);

const shortWallet = computed(() => {
  if (!wallet.value) return "";
  return `${wallet.value.slice(0, 6)}...${wallet.value.slice(-4)}`;
});

async function refreshWallet() {
  wallet.value = (await getConnectedWallet()) ?? "";
}

async function connect() {
  walletError.value = "";
  connecting.value = true;
  try {
    wallet.value = await connectWallet();
  } catch (e: any) {
    walletError.value = e?.message || String(e);
  } finally {
    connecting.value = false;
  }
}

function onAccountsChanged(accounts: string[]) {
  wallet.value = accounts[0] ?? "";
}

onMounted(async () => {
  await refreshWallet();
  window.ethereum?.on?.("accountsChanged", onAccountsChanged);
});

onUnmounted(() => {
  window.ethereum?.removeListener?.("accountsChanged", onAccountsChanged);
});
</script>

<template>
  <div class="shell">
    <header class="masthead">
      <div class="lockup">
        <img src="/recuse-mark.svg" alt="Recuse Protocol mark" />
        <div>
          <div class="wordmark">Recuse</div>
          <div class="sub">PROTOCOL</div>
        </div>
      </div>
      <div class="masthead-actions">
        <nav>
          <router-link to="/" :class="{ active: route.path === '/' }">Check</router-link>
          <router-link to="/watchlist" :class="{ active: route.path === '/watchlist' }">Watchlist</router-link>
          <router-link to="/docs" :class="{ active: route.path === '/docs' }">Docs</router-link>
          <a href="https://github.com/Zhekinmaksim/recuseprotocol" target="_blank">GitHub</a>
        </nav>
        <div class="wallet-bar">
          <span v-if="wallet" class="wallet-pill">{{ shortWallet }}</span>
          <button class="wallet-button" @click="connect" :disabled="connecting">
            <span v-if="wallet">Connected</span>
            <span v-else-if="connecting">Connecting</span>
            <span v-else>Connect Wallet</span>
          </button>
        </div>
      </div>
    </header>
    <div v-if="walletError" class="notice error wallet-error">{{ walletError }}</div>
    <div class="tagline">
      <span>The Trustless DeFi Verdict Layer</span>
      <span>{{ today }} · GENLAYER BRADBURY TESTNET</span>
    </div>

    <main>
      <router-view />
    </main>
  </div>
</template>
