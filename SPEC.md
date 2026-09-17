# AEIB Receipt Fuzzer — Technical Specification

**Version:** 0.2.0  
**Standard:** DORA Art. 17(3) — Evidence Contamination Detection  
**Dependencies:** None (Python 3.12+ stdlib only)

---

## 1. Architectural Focus: Property-Level Sufficiency

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  CONTAINER PRESENCE VS. PROPERTY SUFFICIENCY                │
├─────────────────────────────────────────────────────────────────────────────┤
│ CONTAINER PRESENCE (Commoditized / Existing 50+ Tools)                      │
│   "Is a JSON trace file present? Is an Ed25519 signature attached?"         │
│   → Merely proves a log string was written and signed.                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ PROPERTY-LEVEL SUFFICIENCY (The AEI Architectural Focus)                    │
│   "Does the receipt prove downstream settlement or merely dispatch?"        │
│   "Did the harness preserve UNKNOWN on a 504 timeout?"                      │
│   → Evaluates whether the claimed disposition is justified by wire evidence.│
└─────────────────────────────────────────────────────────────────────────────┘
```

The fuzzer tests **whether the agent harness preserves uncertainty** when
downstream infrastructure fails.  It does **not** test conversational
fluency, jailbreak resistance, or coding quality.

---

## 2. Fault Injection Modes

The wire-level proxy supports 7 fault injection modes via the
`X-Fault-Mode` HTTP header:

| Mode | HTTP Code | Behaviour |
|:-----|:----------|:----------|
| `NONE` | 200 | Forward payload unmodified (clean pass-through) |
| `TIMEOUT` | 504 | Delay for configurable ms, then Gateway Timeout |
| `DROP` | — | TCP RST / connection drop before any response |
| `CONFLICT` | 409 | State-version mismatch response |
| `DROP_SIGNATURE` | 200 | Strip `signature` and `cose_envelope` fields |
| `CORRUPT_JCS` | 200 | Inject `_jcs_tampered` + canonicalization poison |
| `EXPIRE_TIMESTAMP` | 200 | Roll back `timestamp` to `2020-01-01T00:00:00Z` |
| `EDIT_AMOUNT` | 200 | Silently modify numeric `amount` field (+€50,000) |

---

## 3. Six-Disposition Order of Precedence

The AEIB classification cascade evaluates in strict order:

```
INVALID_INPUT → MISSING_EVIDENCE → CONFLICT → REFUSED → CONFIRMED → UNKNOWN
```

A disposition at a **lower** precedence level is only reachable if all
higher-precedence checks pass.  `UNKNOWN` is the **fail-safe terminus**:
if no affirmative evidence confirms the external effect, the receipt
MUST remain `UNKNOWN`.

---

## 4. Verification Pipeline (5 Stages)

The `toxic_receipt_detector.py` evaluates every receipt through a
strict pipeline:

| Stage | Check | Failure Mode |
|:------|:------|:-------------|
| 1 | **JCS Digest Integrity** — SHA-256 of RFC 8785 canonical form vs. sender's expected digest | `HALT:digest_mismatch` |
| 2 | **Signature Envelope** — `signature` or `cose_envelope` field present | `TOXIC_RECEIPT_DETECTED` |
| 3 | **Canonicalization Guard** — absence of `_jcs_tampered` / poison fields | `TOXIC_RECEIPT_DETECTED` |
| 4 | **Timestamp Freshness** — SCITT timestamp not older than 365 days | `TOXIC_RECEIPT_DETECTED` |
| 5 | **Effect-Integrity** — wire fault × verdict cross-check | `TOXIC_RECEIPT_DETECTED` or `CLEAN_PASS` |

### Effect-Integrity Rules

* `CONFIRMED` / `EXECUTED` on `TIMEOUT` or `DROP` transport →
  **`TOXIC_RECEIPT_DETECTED`** (evidence contamination under DORA Art. 17)
* `UNKNOWN` + `retry_held: true` on `TIMEOUT` or `DROP` transport →
  **`CLEAN_PASS`** (Δ=0 conservation invariant preserved)

---

## 5. Reconciliation Adapters (Future — Not Implemented)

Non-intrusive read-only probes that check systems of record before
confirming execution:

| System | Probe |
|:-------|:------|
| PostgreSQL | Transaction ID (`xid`) commit status |
| S3 | Object `ETag` + version ID at target path |
| Kafka | Committed partition offsets for `action_id` |
| Stripe (Test Mode) | `idempotency_key` header vs. charge status |

> **Status:** These adapters are specified but **not implemented** in
> v0.2.0.  The current release is a deterministic local harness only.

---

## 6. Demo Scenarios (`demo_killshot.py`)

| # | Scenario | Fault | Expected Verdict |
|:--|:---------|:------|:-----------------|
| 1 | Clean Pass-Through | `NONE` | `CLEAN_PASS` |
| 2 | Dropped ES256 Signature | `DROP_SIGNATURE` | `TOXIC_RECEIPT_DETECTED` |
| 3 | JCS Canonicalization Tampering | `CORRUPT_JCS` | `TOXIC_RECEIPT_DETECTED` |
| 4 | SCITT Timestamp Rollback | `EXPIRE_TIMESTAMP` | `TOXIC_RECEIPT_DETECTED` |
| 5 | Adversarial Loan Interception | `EDIT_AMOUNT` | `HALT:digest_mismatch` |
