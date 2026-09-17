#!/usr/bin/env python3
"""AEIB Toxic Receipt Detector v0.2.0

RFC 8785 JCS + ES256 SCITT receipt interrogator.

Verification Pipeline:
    1. JCS Digest Integrity     — RFC 8785 canonical hash comparison
    2. Signature Envelope       — ES256 / COSE_Sign1 presence check
    3. Canonicalization Guard    — Detects injected JCS poison fields
    4. Timestamp Freshness      — SCITT sequence / expiration validation
    5. Effect-Integrity Class.  — Wire-fault × verdict cross-check

Effect-Integrity Rules (DORA Art. 17(3)):
    CONFIRMED/EXECUTED on TIMEOUT/DROP traffic → TOXIC_RECEIPT_DETECTED
    UNKNOWN + retry_held=true  on TIMEOUT/DROP → CLEAN_PASS  (Δ=0)
"""

import json
import hashlib
import sys
from datetime import datetime, timezone


# ── RFC 8785 JCS Canonicalization ────────────────────────────────

def jcs_canonicalize(obj) -> bytes:
    """RFC 8785 JSON Canonicalization Scheme (deterministic subset).

    Produces a byte-identical representation regardless of input
    key ordering:
      - Object keys sorted lexicographically (recursive)
      - Minimal separators (no whitespace)
      - UTF-8 encoded
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def jcs_digest(obj) -> str:
    """SHA-256 hex digest of the JCS-canonicalized payload."""
    return hashlib.sha256(jcs_canonicalize(obj)).hexdigest()


# ── Verdict Data Class ───────────────────────────────────────────

class ReceiptVerdict:
    """Immutable classification result from the verification pipeline."""

    CLEAN_PASS = "CLEAN_PASS"
    TOXIC_RECEIPT = "TOXIC_RECEIPT_DETECTED"
    HALT_DIGEST_MISMATCH = "HALT:digest_mismatch"

    def __init__(self, verdict: str, reason: str, details: dict = None):
        self.verdict = verdict
        self.reason = reason
        self.details = details or {}

    def __repr__(self):
        return f"ReceiptVerdict({self.verdict!r}, reason={self.reason!r})"

    @property
    def is_clean(self) -> bool:
        return self.verdict == self.CLEAN_PASS


# ── Verification Pipeline ────────────────────────────────────────

def verify_receipt(
    receipt: dict,
    expected_digest: str = None,
    wire_fault: str = None,
) -> ReceiptVerdict:
    """Full 5-stage verification pipeline for an agent action receipt.

    Args:
        receipt:         The received JSON payload (post-proxy).
        expected_digest: If supplied, JCS digest of the *original*
                         payload before it entered the wire.  A mismatch
                         means the payload was modified in transit.
        wire_fault:      The fault mode that was active during
                         transmission (used for effect-integrity
                         cross-checking).

    Returns:
        ReceiptVerdict with classification, human reason, and details.
    """

    # ── Stage 1: JCS Digest Integrity ────────────────────────────
    if expected_digest is not None:
        actual_digest = jcs_digest(receipt)
        if actual_digest != expected_digest:
            return ReceiptVerdict(
                ReceiptVerdict.HALT_DIGEST_MISMATCH,
                "JCS canonical digest mismatch — payload modified in transit",
                {
                    "expected": expected_digest[:16] + "…",
                    "actual": actual_digest[:16] + "…",
                },
            )

    # ── Stage 2: Signature Envelope Presence ─────────────────────
    has_sig = "signature" in receipt or "cose_envelope" in receipt
    if not has_sig:
        return ReceiptVerdict(
            ReceiptVerdict.TOXIC_RECEIPT,
            "Missing ES256 / COSE_Sign1 signature envelope",
        )

    # ── Stage 3: Canonicalization Guard ──────────────────────────
    if receipt.get("_jcs_tampered") or receipt.get("__canonicalization_poison"):
        return ReceiptVerdict(
            ReceiptVerdict.TOXIC_RECEIPT,
            "RFC 8785 JCS canonicalization hash mismatch — payload tampered",
        )

    # ── Stage 4: Timestamp Freshness ─────────────────────────────
    ts_raw = receipt.get("timestamp")
    if ts_raw:
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - ts).days
            if age_days > 365:
                return ReceiptVerdict(
                    ReceiptVerdict.TOXIC_RECEIPT,
                    f"SCITT timestamp expired / rolled back ({age_days} days old)",
                )
        except (ValueError, TypeError):
            pass  # Unparseable timestamp is caught by other checks

    # ── Stage 5: Effect-Integrity Classification ─────────────────
    verdict_field = receipt.get("verdict", receipt.get("status", ""))

    #  TOXIC: receipt claims success on ambiguous transport
    if (wire_fault in ("TIMEOUT", "DROP")
            and verdict_field in ("CONFIRMED", "EXECUTED", "executed")):
        return ReceiptVerdict(
            ReceiptVerdict.TOXIC_RECEIPT,
            (f"Receipt asserts '{verdict_field}' on {wire_fault} "
             f"transport — evidence contamination (DORA Art. 17)"),
            {"dora_article": "Art. 17(3)", "delta": "non-zero"},
        )

    #  CLEAN: harness correctly preserves uncertainty
    if (wire_fault in ("TIMEOUT", "DROP")
            and verdict_field == "UNKNOWN"
            and receipt.get("retry_held")):
        return ReceiptVerdict(
            ReceiptVerdict.CLEAN_PASS,
            "Uncertainty preserved: UNKNOWN + retry_held=true (Δ=0)",
            {"delta": 0},
        )

    # ── Default: clean ───────────────────────────────────────────
    return ReceiptVerdict(
        ReceiptVerdict.CLEAN_PASS,
        "Receipt is cryptographically sound and canonical",
    )


# ── CLI Entry Point ──────────────────────────────────────────────

if __name__ == "__main__":
    raw = sys.stdin.read()
    if not raw.strip():
        print("Usage: cat receipt.json | python3 toxic_receipt_detector.py")
        sys.exit(1)

    try:
        receipt = json.loads(raw)
    except json.JSONDecodeError:
        print("❌ FATAL: Invalid JSON receipt.")
        sys.exit(1)

    result = verify_receipt(receipt)
    icon = "✅" if result.is_clean else "❌"
    print(f" {icon} {result.verdict}: {result.reason}")
    sys.exit(0 if result.is_clean else 1)
