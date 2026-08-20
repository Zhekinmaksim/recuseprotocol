# Recuse Protocol

**The trustless DeFi verdict layer.** Recuse Protocol is a GenLayer Intelligent Contract that stores on-chain safety verdicts for ERC-20 tokens.

When a judge has a conflict of interest, they recuse themselves from the case. Recuse applies the same idea to DeFi: an integrating contract can consult `should_recuse(token, chain)` before touching an asset, and step aside when the token fails the integrity test.

## Production Status

- **Network:** GenLayer Bradbury Testnet
- **Contract:** `0xcFAFCd13B843bcA830b90B678D6bAA75335D6A5f`
- **Deploy tx:** `0xbf47ad996f5766cb7b3fe105c92e25948ff05c61dad8870db7ecf1a6db7471b7`
- **Verified smoke checks:**
  - USDC on Ethereum: `CLEAR`, score `12`, tx `0xc85a99aee2aefa465b9bf1ad84fc557073dca63367b5d67002a30eadae64d1f5`
  - SQUID on BSC: `RECUSE`, score `90`, tx `0x80168a740334733647389f74ac364849fc13f81da6edb6d21931f786e766a792`

## Verdicts

| Bucket | Action | Score |
|---|---|---|
| `CLEAR` | Proceed without restriction. | 0-29 |
| `WATCH` | Proceed but log and reassess sooner. | 30-59 |
| `FLAG` | Hold and require explicit user override. | 60-79 |
| `RECUSE` | Step aside from the transaction. | 80-100 |

The integration gate is:

```python
should_recuse(token: Address, chain: str) -> bool
```

It returns `True` only for the `RECUSE` bucket, so consumers can choose their own policy for `WATCH` and `FLAG`.

## How It Works

The production demo path is intentionally stable:

1. The Vue app fetches a fresh live snapshot from DexScreener and Honeypot.is through `/api/snapshot`.
2. The connected wallet signs a real Bradbury transaction to `assess_snapshot(token, chain, onchain, offchain)`.
3. `RecuseOracle` applies a deterministic risk rubric and stores the `Verdict` struct on-chain.
4. The frontend waits for an accepted transaction, then reads `get_verdict(token, chain)` and renders the stored report.

This means the frontend genuinely calls the contract and handles the write/read lifecycle. There is no private backend key and no centralized writer: the user's wallet submits the assessment transaction.

The contract also keeps an experimental `assess(token, chain)` path for GenVM-native web collection. The submission flow uses `assess_snapshot` because public token pages and explorers can block HTML renderers, while the API snapshot path is reliable for live demos.

## Contract Surface

```python
@gl.public.write
def assess_snapshot(token: Address, chain: str, onchain: dict, offchain: dict) -> None

@gl.public.write
def assess(token: Address, chain: str) -> None

@gl.public.view
def get_verdict(token: Address, chain: str) -> Verdict

@gl.public.view
def should_recuse(token: Address, chain: str) -> bool

@gl.public.write
def subscribe(token: Address, chain: str) -> None

@gl.public.write
def tick() -> None
```

## Signals

Current production signals:

- contract source status from Honeypot.is
- sell simulation / honeypot result
- buy and sell tax
- liquidity, market cap, pair metadata from DexScreener
- holder count from Honeypot.is
- website, X/Twitter, and GitHub links from DexScreener token profile metadata
- Honeypot risk level and risk flags

The rubric is deterministic: high risk levels, failed sell simulation, high taxes, closed source contracts, missing off-chain footprint, low liquidity, and young pairs move a token toward `FLAG` or `RECUSE`.

## Repository Layout

```text
contracts/                 GenLayer Intelligent Contract
contracts/prompts/          Prompts retained for the experimental native web path
app/                        Vue 3 + genlayer-js frontend
app/api/snapshot.ts         Vercel serverless live-data endpoint
landing/                    Static landing page
keeper/                     Node one-shot keeper for tick()
test/                       GenLayer Studio integration tests
docs/                       Submission checklist, notes, and launch thread
deploy.sh                   Bradbury deploy helper
DEPLOYED_ADDRESSES.md       Deploy and calibration proof
```

## Local Development

```bash
cd app
cp .env.example .env
npm install
npm run dev
```

The public frontend variables are:

```bash
VITE_ORACLE_ADDRESS=0xcFAFCd13B843bcA830b90B678D6bAA75335D6A5f
VITE_GENLAYER_RPC=https://rpc-bradbury.genlayer.com
```

## Deploy

Put the deployer key in a local `.env` file that is ignored by git:

```bash
GENLAYER_PRIVATE_KEY=0x...
GENLAYER_KEYSTORE_PASSWORD=...
```

Then deploy:

```bash
bash deploy.sh
```

`deploy.sh` reads `.env` or `../.env`, imports/unlocks the local GenLayer account, deploys to Bradbury, and never writes secrets into the repository.

## Verification

Commands run before publishing:

```bash
python3 -m py_compile contracts/recuse_oracle.py
cd app && npm run build
cd keeper && npx tsc --noEmit --target ES2022 --module NodeNext --moduleResolution NodeNext --types node --skipLibCheck tick.ts
cd app && npx tsc --noEmit --target ES2022 --module NodeNext --moduleResolution NodeNext --skipLibCheck api/snapshot.ts
```

Bradbury checks:

```bash
genlayer call 0xcFAFCd13B843bcA830b90B678D6bAA75335D6A5f get_verdict --args 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 ethereum
genlayer call 0xcFAFCd13B843bcA830b90B678D6bAA75335D6A5f get_verdict --args 0x87230146E138d3F296a9a77e497A2A83012e9Bc5 bsc
```

Expected results are `clear` score `12` for USDC and `recuse` score `90` for SQUID.
