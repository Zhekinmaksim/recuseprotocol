# Deployed Addresses

## Contract

**Chain:** Bradbury Testnet
**Address:** `0xcFAFCd13B843bcA830b90B678D6bAA75335D6A5f`
**Deploy tx:** `0xcee1dae2284a2eb8eecac8cfc8aff94967bb4bdf7fb3f1ff0e22d4a6a09f7aca`
**RPC:** `https://rpc-bradbury.genlayer.com`

### Failed deploy audit trail

Do not use this address in production:

- **Address:** `0x33bE56010624692a61d0a15C877F2419eeB560a3`
- **Deploy tx:** `0x16fc05723fa77ff0cd73d248fc276881fa12d70fc0488a8ec89317d53a82cbb0`
- **Reason:** GenVM trace returned `invalid_contract` because the contract used `py-genlayer:test`; this has been fixed in `contracts/recuse_oracle.py` with pinned runner `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.

Other failed/deprecated deploys during Bradbury compatibility work:

- `0x354E62ea15968d655C0f6866B5912a429fc92DC1` - storage classes needed `@allow_storage`
- `0x62aaf6E3BCdf339942851151088Bb299BbFA3DeF` - sender field changed to `gl.message.sender_address`
- `0x7a4B543F736088F7A0Cb5e5FDFe97Ee732cA94C0` - CLI address args needed normalization
- `0x6ea5dc6bE865BFC8b7C5eafb52cad94deDF60Ef9` - Etherscan HTML path blocked by Cloudflare
- `0x1D8A6E71D93e2d736AAda1eF52a72e96715247bB` - runtime timestamp field unavailable
- `0x84CCe5E68A9e19291898a05B77Ff623F97b8C339` - API wrapper returned an execution error
- `0xDD3eb8A16F7b69c9fA0b22306556c85f8d505f86` - `gl.message.block_timestamp` unavailable
- `0x76563700c88188F9d94Fb66262CBC56cc73370C7` - pre-snapshot production path
- `0x4db52BBd0554B3789f7412433384452D55d0E8D5` - pre-`@dataclass` storage shape

## Frontend

**Landing:** https://recuse.xyz (or TODO_VERCEL_URL)
**App:** https://app.recuse.xyz (or TODO_VERCEL_URL)

## Calibration test transactions

### USDC on ethereum (expected CLEAR)

**Address:** 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
**Assess tx:** `0xc85a99aee2aefa465b9bf1ad84fc557073dca63367b5d67002a30eadae64d1f5`
**Execution hash:** `0x8449a4ac7805ae8ad3e3bd56b64869ef0cfb7ee078c15a602b74e72d7a4c0a53`
**Actual verdict:** `clear`
**Score:** `12`
**Trace:** `result_code: 0`

### SQUID on bsc (expected RECUSE)

**Address:** 0x87230146E138d3F296a9a77e497A2A83012e9Bc5
**Assess tx:** `0x80168a740334733647389f74ac364849fc13f81da6edb6d21931f786e766a792`
**Execution hash:** `0x7315b888bdc5e5849d07b6250aac3032470bea7d888b8995d24809d4508cd1d1`
**Actual verdict:** `recuse`
**Score:** `90`
**Trace:** `result_code: 0`

## Keeper

**GitHub Actions workflow:** https://github.com/Zhekinmaksim/recuseprotocol/actions
**Cron schedule:** every 6 hours (`0 */6 * * *`)
**Last tick tx:** `TODO_TX_HASH`

## Demo

**Video:** `TODO_LOOM_OR_YOUTUBE`
**Landing screenshot:** `TODO_LINK`
**App verdict page screenshot (SQUID):** `TODO_LINK`
