/**
 * Recuse Protocol keeper.
 *
 * Calls tick() on the RecuseOracle to refresh stale verdicts for
 * subscribed tokens. Runs on:
 *   - Vercel cron
 *   - GitHub Actions (./.github/workflows/keeper.yml, every 6h)
 *   - Any standard cron host
 *
 * Required env:
 *   GENLAYER_RPC       - testnet RPC endpoint
 *   ORACLE_ADDRESS     - 0x… deployed RecuseOracle address
 *   KEEPER_PRIVATE_KEY - keeper account with gas
 */

import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";
import { privateKeyToAccount } from "viem/accounts";

const rpc = process.env.GENLAYER_RPC || "https://rpc-bradbury.genlayer.com";
const oracle = process.env.ORACLE_ADDRESS as `0x${string}`;
const pk = process.env.KEEPER_PRIVATE_KEY as `0x${string}`;

if (!oracle || !pk) {
  console.error("Missing ORACLE_ADDRESS / KEEPER_PRIVATE_KEY");
  process.exit(1);
}

const account = privateKeyToAccount(pk);
const client = createClient({ chain: testnetBradbury, endpoint: rpc, account });

async function main() {
  const started = Date.now();
  console.log(`[recuse-keeper] tick start ${new Date().toISOString()}`);
  console.log(`[recuse-keeper] oracle=${oracle} from=${account.address}`);

  try {
    const tx = await client.writeContract({
      address: oracle,
      functionName: "tick",
      args: [],
      value: 0n,
    });
    console.log(`[recuse-keeper] tx submitted: ${tx}`);
    const receipt = await client.waitForTransactionReceipt({
      hash: tx,
      status: TransactionStatus.ACCEPTED,
    });
    console.log(`[recuse-keeper] finalized in ${Date.now() - started}ms`);
    console.log(`[recuse-keeper] status=${receipt.statusName ?? receipt.status}`);
  } catch (e: any) {
    console.error(`[recuse-keeper] FAILED: ${e?.message || e}`);
    process.exit(2);
  }
}

main();
