#!/usr/bin/env python3
"""AEIB Killshot Demo — Node5 Prague Meetup Edition

Self-contained demo: starts the asyncio fault proxy in a background
thread, fires 5 adversarial scenarios through the toxic receipt
detector, prints falsifiable results, and shuts down cleanly.

Zero dependencies.  Python 3.12+ stdlib only.

Optimised for dark-mode, 18pt high-contrast terminal presentations.

Usage:
    python3 demo_killshot.py
"""

import asyncio
import http.client
import json
import sys
import threading
import time

from fuzzer import FaultProxy
from toxic_receipt_detector import (
    ReceiptVerdict,
    jcs_digest,
    verify_receipt,
)

# ── Layout Constants ─────────────────────────────────────────────

W = 72                       # banner width
PROXY_PORT = 8079            # avoid conflict with anything on 8080
STARTUP_WAIT = 0.6           # seconds to let the proxy bind
SCENARIO_GAP = 0.35          # pause between scenarios for readability


# ── Display Helpers ──────────────────────────────────────────────

def banner(text: str, char: str = "═"):
    print(f"\n{char * W}")
    print(f"  {text}")
    print(f"{char * W}")


def scenario_header(num: int, title: str):
    print(f"\n{'─' * W}")
    print(f"  SCENARIO {num}: {title}")
    print(f"{'─' * W}")


def verdict_line(result: ReceiptVerdict):
    if result.verdict == ReceiptVerdict.CLEAN_PASS:
        print(f"\n  ✅ Verdict: {result.verdict}")
    elif result.verdict == ReceiptVerdict.HALT_DIGEST_MISMATCH:
        print(f"\n  🛑 {result.verdict}")
    else:
        print(f"\n  ❌ Verdict: {result.verdict}")
    print(f"     Reason:  {result.reason}")


# ── HTTP Client ──────────────────────────────────────────────────

def send_through_proxy(payload: dict, fault_mode: str):
    """POST *payload* through the local fault proxy.

    Returns the parsed JSON response, or ``None`` when the proxy
    intentionally drops the connection (fault mode ``DROP``).
    """
    body = json.dumps(payload).encode("utf-8")
    try:
        conn = http.client.HTTPConnection("127.0.0.1", PROXY_PORT, timeout=4)
        conn.request(
            "POST",
            "/",
            body=body,
            headers={
                "Content-Type": "application/json",
                "X-Fault-Mode": fault_mode,
            },
        )
        resp = conn.getresponse()
        data = resp.read()
        conn.close()
        return json.loads(data.decode("utf-8"))
    except (PermissionError, OSError):
        # Under strict sandboxing where TCP loopback is forbidden,
        # evaluate through the fault injection engine directly.
        proxy = FaultProxy(port=PROXY_PORT, timeout_ms=500)
        loop = asyncio.new_event_loop()
        try:
            res, _, _ = loop.run_until_complete(
                proxy._inject_fault(fault_mode, body, None)
            )
            return res
        finally:
            loop.close()
    except Exception:
        return None


# ── Baseline Receipt ─────────────────────────────────────────────

BASE_RECEIPT = {
    "id": "aeib-action-2026-0917",
    "type": "CREDIT_TRANSFER",
    "status": "CONFIRMED",
    "timestamp": "2026-09-17T08:30:00Z",
    "amount": 1850000,
    "currency": "EUR",
    "counterparty": "DE89370400440532013000",
    "signature": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkNPU0VfU2lnbjEifQ...",
    "verdict": "CONFIRMED",
}


# ── Scenario Runners ─────────────────────────────────────────────

def _s1_clean_pass(results: list):
    scenario_header(1, "Clean Pass-Through (Valid Receipt)")
    print(f"  Payload: €{BASE_RECEIPT['amount']:,.2f} credit transfer")
    print(f"  Fault:   NONE (forwarded unmodified)")

    received = send_through_proxy(BASE_RECEIPT, "NONE")
    if received is None:
        results.append(("Clean Pass-Through", "NO_RESPONSE", "FAIL"))
        return
    result = verify_receipt(received)
    verdict_line(result)
    expected = ReceiptVerdict.CLEAN_PASS
    results.append((
        "Clean Pass-Through",
        result.verdict,
        "PASS" if result.verdict == expected else "FAIL",
    ))


def _s2_dropped_signature(results: list):
    scenario_header(2, "Dropped ES256 Signature")
    print(f"  Payload: €{BASE_RECEIPT['amount']:,.2f} credit transfer")
    print(f"  Fault:   DROP_SIGNATURE (strip COSE_Sign1 envelope)")

    received = send_through_proxy(BASE_RECEIPT, "DROP_SIGNATURE")
    if received is None:
        results.append(("Dropped Signature", "NO_RESPONSE", "FAIL"))
        return
    result = verify_receipt(received)
    verdict_line(result)
    expected = ReceiptVerdict.TOXIC_RECEIPT
    results.append((
        "Dropped Signature",
        result.verdict,
        "PASS" if result.verdict == expected else "FAIL",
    ))


def _s3_jcs_tampering(results: list):
    scenario_header(3, "JCS Canonicalization Tampering")
    print(f"  Payload: €{BASE_RECEIPT['amount']:,.2f} credit transfer")
    print(f"  Fault:   CORRUPT_JCS (inject canonicalization poison)")

    received = send_through_proxy(BASE_RECEIPT, "CORRUPT_JCS")
    if received is None:
        results.append(("JCS Tampering", "NO_RESPONSE", "FAIL"))
        return
    result = verify_receipt(received)
    verdict_line(result)
    expected = ReceiptVerdict.TOXIC_RECEIPT
    results.append((
        "JCS Tampering",
        result.verdict,
        "PASS" if result.verdict == expected else "FAIL",
    ))


def _s4_rollback(results: list):
    scenario_header(4, "SCITT Timestamp Rollback Attack")
    print(f"  Payload: €{BASE_RECEIPT['amount']:,.2f} credit transfer")
    print(f"  Fault:   EXPIRE_TIMESTAMP (roll back to 2020-01-01)")

    received = send_through_proxy(BASE_RECEIPT, "EXPIRE_TIMESTAMP")
    if received is None:
        results.append(("Rollback Attack", "NO_RESPONSE", "FAIL"))
        return
    result = verify_receipt(received)
    verdict_line(result)
    expected = ReceiptVerdict.TOXIC_RECEIPT
    results.append((
        "Rollback Attack",
        result.verdict,
        "PASS" if result.verdict == expected else "FAIL",
    ))


def _s5_adversarial_loan(results: list):
    scenario_header(5, "⚡ ADVERSARIAL LOAN INTERCEPTION ⚡")

    original_amount = BASE_RECEIPT["amount"]       # 1 850 000
    tampered_amount = original_amount + 50000      # 1 900 000

    print(f"  Original: €{original_amount:,.2f} loan approval")
    print(f"  Attack:   Silent in-transit edit → €{tampered_amount:,.2f}")
    print(f"  Fault:    EDIT_AMOUNT (+€{tampered_amount - original_amount:,.2f} skimming)")

    # Digest of the payload the sender *intended* to transmit
    original_digest = jcs_digest(BASE_RECEIPT)
    print(f"\n  [SENDER]   JCS digest: {original_digest[:32]}…")

    received = send_through_proxy(BASE_RECEIPT, "EDIT_AMOUNT")
    if received is None:
        results.append(("Adversarial Loan Interception", "NO_RESPONSE", "FAIL"))
        return

    received_digest = jcs_digest(received)
    print(f"  [RECEIVER] JCS digest: {received_digest[:32]}…")

    result = verify_receipt(received, expected_digest=original_digest)

    if result.verdict == ReceiptVerdict.HALT_DIGEST_MISMATCH:
        print(f"\n  🛑 HALT: {result.reason}")
        print(f"     Expected: {result.details.get('expected', 'N/A')}")
        print(f"     Actual:   {result.details.get('actual', 'N/A')}")
        print()
        print(f"  → Agent execution HALTED ex-ante.")
        print(f"  → €{tampered_amount - original_amount:,.2f} skimming attack PREVENTED.")
        results.append(("Adversarial Loan Interception", result.verdict, "PASS"))
    else:
        verdict_line(result)
        results.append(("Adversarial Loan Interception", result.verdict, "FAIL"))


# ── Orchestrator ─────────────────────────────────────────────────

def run_scenarios() -> list:
    results: list = []
    for fn in (_s1_clean_pass, _s2_dropped_signature, _s3_jcs_tampering,
               _s4_rollback, _s5_adversarial_loan):
        fn(results)
        time.sleep(SCENARIO_GAP)
    return results


# ── Main ─────────────────────────────────────────────────────────

def main() -> int:
    banner("🕷️  AEIB RECEIPT FUZZER — KILLSHOT DEMO")
    print("  Wire-Level Fault Proxy + RFC 8785 JCS + ES256 SCITT Interrogator")
    print(f"  Python {sys.version.split()[0]} · Zero dependencies · Offline")
    print("  DORA Art. 17(3) — Evidence Contamination Detection")

    # ── Start proxy in a daemon thread ───────────────────────────
    proxy = FaultProxy(port=PROXY_PORT, timeout_ms=500)

    def _run():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(proxy.start())
        except Exception:
            pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    time.sleep(STARTUP_WAIT)

    # ── Execute scenarios ────────────────────────────────────────
    results = run_scenarios()

    # ── Summary table ────────────────────────────────────────────
    banner("📊 RESULTS SUMMARY")
    passed = 0
    for name, verdict, status in results:
        icon = "✅" if status == "PASS" else "❌"
        print(f"  {icon} {name:<40s} {verdict}")
        if status == "PASS":
            passed += 1

    total = len(results)
    print(f"\n  {passed}/{total} scenarios verified correctly.")

    if passed == total:
        print("\n  🎯 ALL SCENARIOS PASSED — Harness preserves uncertainty.")
    else:
        print(f"\n  ⚠️  {total - passed} scenario(s) failed verification.")

    banner("", char="═")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
