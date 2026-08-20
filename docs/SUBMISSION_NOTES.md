# Submission Notes - Recuse Protocol

## Category

Intelligent Contract (standalone reusable contract).

## One-line description

Recuse Protocol is a GenLayer Intelligent Contract that stores on-chain DeFi token safety verdicts so wallets, DEXes, and vaults can decide when to step aside from risky assets.

## Deployed address

- **Contract:** `0xcFAFCd13B843bcA830b90B678D6bAA75335D6A5f` on Bradbury Testnet
- **Deploy tx:** `0xbf47ad996f5766cb7b3fe105c92e25948ff05c61dad8870db7ecf1a6db7471b7`
- **RPC:** `https://rpc-bradbury.genlayer.com`

## Live artifacts

- **App:** https://app.recuse.xyz
- **Landing:** https://recuse.xyz
- **GitHub:** https://github.com/Zhekinmaksim/recuseprotocol
- **Demo video:** TODO_LOOM_OR_YOUTUBE_URL

## Calibration proof

- **USDC on Ethereum:** `CLEAR`, score `12`
  - token: `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`
  - tx: `0xc85a99aee2aefa465b9bf1ad84fc557073dca63367b5d67002a30eadae64d1f5`
  - execution hash: `0x8449a4ac7805ae8ad3e3bd56b64869ef0cfb7ee078c15a602b74e72d7a4c0a53`
  - trace result: `result_code: 0`
- **SQUID on BSC:** `RECUSE`, score `90`
  - token: `0x87230146E138d3F296a9a77e497A2A83012e9Bc5`
  - tx: `0x80168a740334733647389f74ac364849fc13f81da6edb6d21931f786e766a792`
  - execution hash: `0x7315b888bdc5e5849d07b6250aac3032470bea7d888b8995d24809d4508cd1d1`
  - trace result: `result_code: 0`

## What it does

Recuse Protocol is a decentralized safety verdict layer for ERC-20 tokens. Any dApp that routes user funds through arbitrary tokens needs to answer a trust question before executing: should this asset be allowed through, warned, held, or blocked?

The contract stores a `Verdict` struct with one of four buckets:

- `CLEAR` - proceed without restriction
- `WATCH` - proceed but log and reassess sooner
- `FLAG` - hold and require explicit user override
- `RECUSE` - step aside from the transaction

The headline integration function is `should_recuse(token, chain) -> bool`, which returns true only for the strongest bucket.

## Why GenLayer specifically

This is an intelligent-oracle use case: the useful output is not another text answer, but a reusable on-chain decision that other contracts and apps can consume.

The production flow uses live DexScreener and Honeypot.is data gathered at request time, then writes the evidence snapshot into a GenLayer transaction. RecuseOracle applies a deterministic rubric and persists the verdict on Bradbury. The frontend waits for the transaction to be accepted, reads `get_verdict`, and renders the stored result.

An experimental native GenVM web-collection path remains in `assess(token, chain)`, but the submitted demo uses `assess_snapshot` because it is more reliable against public explorer anti-bot pages while still using live authoritative data and a real contract write.

## Quality bar mapping

- **Solves a real trust problem:** DeFi safety verdicts are normally delegated to centralized vendors. Recuse makes the verdict an on-chain reusable primitive.
- **Uses live or authoritative data:** Each assessment snapshot is built from live DexScreener and Honeypot.is responses at request time.
- **Complete source and accurate docs:** Contract, frontend, landing, keeper, deploy script, and submission docs are included.
- **Frontend genuinely calls the contract:** The app connects MetaMask, switches to Bradbury, submits `assess_snapshot`, waits for `ACCEPTED`, then reads `get_verdict`.
- **Meaningfully different from boilerplate:** It is a persistent, subscribable, cache-aware DeFi verdict oracle with positive and negative calibration transactions.

## Full source code

- `contracts/recuse_oracle.py` - main Intelligent Contract
- `app/` - Vue 3 + genlayer-js frontend with wallet connection
- `app/api/snapshot.ts` - Vercel serverless live-data endpoint
- `keeper/tick.ts` - one-shot keeper for watchlist refresh
- `landing/index.html` - static landing page
- `deploy.sh` - Bradbury deploy helper
- `DEPLOYED_ADDRESSES.md` - deployment and calibration proof

## Builder

@0maxxdev on X. Zhekinmaksim on GitHub.
