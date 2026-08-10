# Recuse Protocol - Submission Checklist

## Ready Items

- [x] Contract deployed to Bradbury.
- [x] Frontend connects a wallet and submits a real contract transaction.
- [x] USDC positive calibration returns `CLEAR`, score `12`.
- [x] SQUID negative calibration returns `RECUSE`, score `90`.
- [x] Contract Python syntax check passes.
- [x] Vue production build passes.
- [x] Keeper TypeScript check passes.
- [x] Vercel serverless snapshot endpoint TypeScript check passes.
- [ ] Production app URL confirmed.
- [ ] Production landing URL confirmed.
- [ ] 60-second demo video recorded and linked.
- [ ] Builder Program form submitted as **Intelligent Contract**.

## Contract

- **Network:** Bradbury Testnet
- **Address:** `0xf7149EB915b7D0F0AD5068a73b5d05197F66f884`
- **Deploy tx:** `0xbf47ad996f5766cb7b3fe105c92e25948ff05c61dad8870db7ecf1a6db7471b7`

## Calibration Transactions

### USDC on Ethereum

- **Expected:** `CLEAR`
- **Actual:** `clear`, score `12`
- **Token:** `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`
- **Tx:** `0xc85a99aee2aefa465b9bf1ad84fc557073dca63367b5d67002a30eadae64d1f5`
- **Execution hash:** `0x8449a4ac7805ae8ad3e3bd56b64869ef0cfb7ee078c15a602b74e72d7a4c0a53`
- **Trace:** `result_code: 0`

### SQUID on BSC

- **Expected:** `RECUSE`
- **Actual:** `recuse`, score `90`
- **Token:** `0x87230146E138d3F296a9a77e497A2A83012e9Bc5`
- **Tx:** `0x80168a740334733647389f74ac364849fc13f81da6edb6d21931f786e766a792`
- **Execution hash:** `0x7315b888bdc5e5849d07b6250aac3032470bea7d888b8995d24809d4508cd1d1`
- **Trace:** `result_code: 0`

## Production Deploy Steps

### App

```bash
cd app
cp .env.example .env
npm install
npm run build
vercel --prod
```

Required Vercel environment variables:

```bash
VITE_ORACLE_ADDRESS=0xf7149EB915b7D0F0AD5068a73b5d05197F66f884
VITE_GENLAYER_RPC=https://rpc-bradbury.genlayer.com
```

### Landing

```bash
cd landing
vercel --prod
```

Point domains after deploy:

- `recuse.xyz` -> landing
- `app.recuse.xyz` -> app

## Demo Script

Keep it under 60 seconds:

1. Open `recuse.xyz`.
2. Open the app.
3. Connect MetaMask on Bradbury.
4. Paste SQUID `0x87230146E138d3F296a9a77e497A2A83012e9Bc5`, choose `bsc`, request verdict.
5. Show wallet transaction, accepted state, and Verdict page with `RECUSE`.
6. Open USDC verdict and show `CLEAR`.

## Security Notes

- `.env` is ignored by git.
- `deploy.sh` reads `.env` or `../.env` without printing private keys.
- The frontend uses only public `VITE_*` variables.
- No backend private key is used for assessments; users sign their own `assess_snapshot` transactions.

After this one-time deployment, remove or rotate the local deploy private key.
