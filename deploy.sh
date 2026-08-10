#!/usr/bin/env bash
# Deploy RecuseOracle to GenLayer Bradbury testnet.
#
# Prereqs:
#   - genlayer CLI installed (genlayer config set network bradbury)
#   - keeper account funded via faucet

set -euo pipefail

CONTRACT="contracts/recuse_oracle.py"

dotenv_get() {
  local file="$1"
  local key="$2"
  local line=""
  if [ -f "$file" ]; then
    line=$(grep -m1 -E "^${key}=" "$file" || true)
  fi
  if [ -n "$line" ]; then
    printf "%s" "${line#*=}" | tr -d '\r'
  fi
}

dotenv_get_any() {
  local key="$1"
  local value=""
  value=$(dotenv_get ".env" "$key")
  if [ -z "$value" ]; then
    value=$(dotenv_get "../.env" "$key")
  fi
  printf "%s" "$value"
}

ACCOUNT_NAME="${GENLAYER_ACCOUNT_NAME:-$(dotenv_get_any GENLAYER_ACCOUNT_NAME)}"
ACCOUNT_NAME="${ACCOUNT_NAME:-recuse-deployer}"
DEPLOYER_KEY="${GENLAYER_PRIVATE_KEY:-$(dotenv_get_any GENLAYER_PRIVATE_KEY)}"
if [ -z "$DEPLOYER_KEY" ]; then
  DEPLOYER_KEY="${DEPLOYER_PRIVATE_KEY:-$(dotenv_get_any DEPLOYER_PRIVATE_KEY)}"
fi
if [ -z "$DEPLOYER_KEY" ]; then
  DEPLOYER_KEY="${PRIVATE_KEY:-$(dotenv_get_any PRIVATE_KEY)}"
fi
KEYSTORE_PASSWORD="${GENLAYER_KEYSTORE_PASSWORD:-$(dotenv_get_any GENLAYER_KEYSTORE_PASSWORD)}"
if [ -z "$KEYSTORE_PASSWORD" ]; then
  KEYSTORE_PASSWORD="${DEPLOYER_KEYSTORE_PASSWORD:-$(dotenv_get_any DEPLOYER_KEYSTORE_PASSWORD)}"
fi
RPC_ARG=()

GENLAYER_RPC_VALUE="${GENLAYER_RPC:-$(dotenv_get_any GENLAYER_RPC)}"
if [ -n "$GENLAYER_RPC_VALUE" ]; then
  RPC_ARG=(--rpc "$GENLAYER_RPC_VALUE")
fi

if [ -n "$DEPLOYER_KEY" ]; then
  if [ -z "$KEYSTORE_PASSWORD" ]; then
    echo "[recuse] GENLAYER_PRIVATE_KEY is set, but GENLAYER_KEYSTORE_PASSWORD is missing"
    echo "[recuse] add GENLAYER_KEYSTORE_PASSWORD to .env so the CLI can import/unlock non-interactively"
    exit 1
  fi

  echo "[recuse] importing deployer account from env as $ACCOUNT_NAME"
  genlayer account import \
    --name "$ACCOUNT_NAME" \
    --private-key "$DEPLOYER_KEY" \
    --password "$KEYSTORE_PASSWORD" \
    --overwrite

  echo "[recuse] unlocking deployer account"
  genlayer account unlock --account "$ACCOUNT_NAME" --password "$KEYSTORE_PASSWORD"
  genlayer account use "$ACCOUNT_NAME"
elif [ -n "$KEYSTORE_PASSWORD" ]; then
  echo "[recuse] unlocking existing account $ACCOUNT_NAME"
  genlayer account unlock --account "$ACCOUNT_NAME" --password "$KEYSTORE_PASSWORD"
  genlayer account use "$ACCOUNT_NAME"
fi

echo "[recuse] linting"
if command -v genlayer-linter >/dev/null 2>&1; then
  genlayer-linter "$CONTRACT" || true
else
  python3 -m py_compile "$CONTRACT"
fi

echo "[recuse] deploying to bradbury"
OUT=$(genlayer deploy --contract "$CONTRACT" "${RPC_ARG[@]}" | tee /dev/stderr)
TX=$(printf "%s\n" "$OUT" | grep -E "Transaction Hash" | tail -n1 | sed -E "s/.*'(Transaction Hash|Deploy tx)': '?//; s/'.*//; s/.*: //")

echo "[recuse] tx=$TX"
if [ "${WAIT_FINALIZED:-0}" = "1" ]; then
  echo "[recuse] waiting for finalization"
  genlayer receipt "$TX" || true
else
  echo "[recuse] skipping finalization wait; verify with genlayer trace/call"
fi

ADDR=$(printf "%s\n" "$OUT" | grep -E "Contract Address" | tail -n1 | sed -E "s/.*'Contract Address': '?//; s/'.*//; s/.*: //")
echo ""
echo "============================================================"
echo "  RecuseOracle deployed at: $ADDR"
echo "============================================================"
echo ""
echo "Next: set this in two places:"
echo "  app/.env             VITE_ORACLE_ADDRESS=$ADDR"
echo "  keeper env / secrets ORACLE_ADDRESS=$ADDR"
