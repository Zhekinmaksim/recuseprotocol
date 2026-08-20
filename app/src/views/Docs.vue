<template>
  <article>
    <header class="report-head">
      <div>
        <h1 class="title">Docs</h1>
        <div class="subtitle">Bradbury integration</div>
      </div>
    </header>

    <div class="report-grid">
      <dl class="facts">
        <dt>Contract</dt>
        <dd>0xcFAFCd13B843bcA830b90B678D6bAA75335D6A5f</dd>

        <dt>Network</dt>
        <dd>GenLayer Bradbury Testnet</dd>

        <dt>Primary write</dt>
        <dd>assess_snapshot(token, chain, onchain_json, offchain_json)</dd>

        <dt>Primary read</dt>
        <dd>get_verdict(token, chain)</dd>

        <dt>Watchlist</dt>
        <dd>subscribe(token, chain), list_subscriptions(subscriber)</dd>
      </dl>

      <div>
        <p class="reasoning">
          Recuse writes a live token evidence snapshot to an Intelligent Contract, scores the token
          with a deterministic rubric, and returns CLEAR, WATCH, FLAG, or RECUSE for downstream DeFi
          integrations.
        </p>

        <div class="flags">
          <h3>Integration cycle</h3>
          <ul>
            <li class="green">Connect a wallet on Bradbury.</li>
            <li class="green">Request a verdict for an ERC-20 token.</li>
            <li class="green">Confirm the assess transaction.</li>
            <li class="green">Read the finalized verdict from contract storage.</li>
            <li class="green">Optionally subscribe the token to the wallet watchlist.</li>
          </ul>
        </div>
      </div>
    </div>
  </article>
</template>
