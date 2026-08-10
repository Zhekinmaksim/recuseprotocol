"""
Integration tests for RecuseOracle.

Uses genlayer-test's direct mode. Each test deploys a fresh contract,
runs assess() against a known token, and asserts the verdict's bucket.

Calibration set:
  Clean (should be clear or watch):
    - USDC on ethereum: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
    - WETH on ethereum: 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2

  Rug / honeypot (should be flag or recuse):
    - SQUID on bsc:     0x87230146E138d3F296a9a77e497A2A83012e9Bc5
    - SafeMoon V1:      0x8076C74C5e3F5852037F31Ff0093Eeb8c8ADd8D3

We assert buckets, not exact scores: LLM scoring drifts within ±10.
"""

import pytest
from gltest import get_default_account
from gltest.gl import GenLayerClient

CLEAN_TOKENS = [
    ("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "ethereum", "USDC"),
    ("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "ethereum", "WETH"),
]

RUG_TOKENS = [
    ("0x87230146E138d3F296a9a77e497A2A83012e9Bc5", "bsc",      "SQUID"),
    ("0x8076C74C5e3F5852037F31Ff0093Eeb8c8ADd8D3", "ethereum", "SafeMoonV1"),
]


@pytest.fixture
def oracle(client: GenLayerClient):
    return client.deploy(
        contract_path="contracts/recuse_oracle.py",
        constructor_args=[],
    )


@pytest.mark.parametrize("token,chain,name", CLEAN_TOKENS)
def test_clean_token_does_not_trigger_recusal(oracle, token, chain, name):
    oracle.write.assess(token, chain).wait()
    v = oracle.view.get_verdict(token, chain)
    assert v.bucket in ("clear", "watch"), (
        f"{name} ({chain}) expected clear/watch, got {v.bucket}: {v.reasoning}"
    )
    assert oracle.view.should_recuse(token, chain) is False


@pytest.mark.parametrize("token,chain,name", RUG_TOKENS)
def test_known_rug_triggers_recusal_or_flag(oracle, token, chain, name):
    oracle.write.assess(token, chain).wait()
    v = oracle.view.get_verdict(token, chain)
    assert v.bucket in ("flag", "recuse"), (
        f"{name} ({chain}) expected flag/recuse, got {v.bucket}: {v.reasoning}"
    )


def test_should_recuse_strict_for_honeypot(oracle):
    # SQUID is a documented honeypot - sells revert
    oracle.write.assess(
        "0x87230146E138d3F296a9a77e497A2A83012e9Bc5", "bsc"
    ).wait()
    v = oracle.view.get_verdict(
        "0x87230146E138d3F296a9a77e497A2A83012e9Bc5", "bsc"
    )
    assert v.bucket == "recuse", f"honeypot must trigger full recusal, got {v.bucket}"
    assert oracle.view.should_recuse(
        "0x87230146E138d3F296a9a77e497A2A83012e9Bc5", "bsc"
    ) is True


def test_invalid_address_rejected(oracle):
    with pytest.raises(Exception) as ei:
        oracle.write.assess("0xnotanaddress", "ethereum").wait()
    assert "invalid address" in str(ei.value).lower()


def test_unsupported_chain_rejected(oracle):
    with pytest.raises(Exception) as ei:
        oracle.write.assess(
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "fakechain"
        ).wait()
    msg = str(ei.value).lower()
    assert "bad chain" in msg or "unsupported" in msg


def test_subscribe_is_idempotent(oracle):
    token = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    oracle.write.subscribe(token, "ethereum").wait()
    oracle.write.subscribe(token, "ethereum").wait()
    me = get_default_account().address
    subs = oracle.view.list_subscriptions(me)
    assert len(subs) == 1


def test_get_verdict_without_assess_raises(oracle):
    with pytest.raises(Exception) as ei:
        oracle.view.get_verdict(
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "ethereum"
        )
    assert "no verdict" in str(ei.value).lower()
