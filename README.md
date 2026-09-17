# aeib-receipt-fuzzer

**Wire-Level Fault Proxy, Toxic Receipt Detector & Offline Audit Log Scanner.**

Version 0.2.0 · Zero dependencies · Python 3.12+ stdlib only

---

## 🎯 What It Does

Tests whether an AI agent harness **preserves uncertainty** when
downstream infrastructure fails. Most harnesses sign `CONFIRMED`
receipts for transactions that actually timed out — this suite
detects that **evidence contamination** at the wire layer and during
offline staging trace analysis.

```
Agent ──► [fuzzer.py (localhost:8080)] ──► Downstream Gateway
                 │
                 ├──► Injects wire-level faults (504, drop, conflict, JCS poison)
                 │
                 └──► [toxic_receipt_detector.py]
                             │
                             ├──► CLEAN_PASS (Δ=0 uncertainty held)
                             └──► TOXIC_RECEIPT_DETECTED (DORA Art. 17 breach)
```

---

## 🚀 Quickstart

```bash
# 1. Run the self-contained 5-scenario meetup demo
python3 demo_killshot.py

# 2. Run the offline trace scanner against 30-day staging logs
python3 diff.py sample_traces.jsonl --patch-out fix.patch

# 3. Start the proxy standalone for live agent integration
python3 fuzzer.py --port 8080

# 4. Run the full verification suite
bash verify.sh
```

---

## 📦 Four Core Modules

| Module | Role | Description |
|:-------|:-----|:------------|
| `fuzzer.py` | Asyncio Wire-Fault Proxy | Non-blocking proxy on `localhost:8080` injecting 6 wire-fault modes. |
| `toxic_receipt_detector.py` | Classification Engine | Evaluates receipts against Six-Disposition Precedence via RFC 8785 JCS. |
| `diff.py` | Offline Audit Log Scanner | Ingests client staging JSONL logs and emits a unified diff remediation patch. |
| `demo_killshot.py` | Local Meetup Terminal Demo | 5 high-contrast CLI scenarios with the €1.85M → €1.90M loan edit killshot. |

---

## 🕷️ 6 Wire-Fault Modes

| Mode | Wire Observation | Fault Effect |
|:-----|:-----------------|:-------------|
| `TIMEOUT` | HTTP 504 Gateway Timeout | Delayed response (>5000ms in production, 500ms in demo). |
| `DROP` | TCP RST | Abrupt socket closure mid-flight before response. |
| `CONFLICT` | HTTP 409 Conflict | State-version mismatch or duplicate payload collisions. |
| `DROP_SIGNATURE` | Stripped Envelope | Missing ES256 / COSE_Sign1 authorization headers. |
| `CORRUPT_JCS` | Mutated Canonical Digest | RFC 8785 key-sorting or whitespace tampering. |
| `EXPIRE_TIMESTAMP` | Replayed Timestamp | Stale SCITT sequence timestamp rollback. |

---

## 🔬 Six-Disposition Precedence Cascade

$$\text{INVALID\_INPUT} \longrightarrow \text{MISSING\_EVIDENCE} \longrightarrow \text{CONFLICT} \longrightarrow \text{REFUSED} \longrightarrow \text{CONFIRMED} \longrightarrow \text{UNKNOWN}$$

* **`TOXIC_RECEIPT_DETECTED`**: Emitted when wire observes `TIMEOUT` or `DROP`, but harness logs `CONFIRMED` or `EXECUTED`.
* **`CLEAN_PASS`**: Emitted when harness preserves uncertainty (`verdict: UNKNOWN`, `retry_held: true`).

---

## 📁 10 Open Conformance Vectors (`conformance_vectors/`)

Deterministic test fixtures covering every state machine transition:
1. `001_timeout_unknown.json`: Baseline clean pass (uncertainty preserved on timeout).
2. `002_dropped_signature.json`: Toxic receipt with missing cryptographic envelope.
3. `003_jcs_poison.json`: Toxic receipt with mutated canonical digest.
4. `004_expired_timestamp.json`: Toxic receipt with replayed stale timestamp.
5. `005_amount_tamper_killshot.json`: Adversarial loan edit (€1.85M → €1.90M) triggering `HALT:digest_mismatch`.
6. `006_conflict_version_mismatch.json`: HTTP 409 conflict handling.
7. `007_tcp_rst_drop.json`: Toxic receipt claiming execution despite TCP RST.
8. `008_clean_confirmed_with_xid.json`: Confirmed settlement with PostgreSQL `xid` anchor.
9. `009_missing_action_id.json`: Structural schema validation failure (`INVALID_INPUT`).
10. `010_refused_downstream_403.json`: Explicit downstream policy rejection (`REFUSED`).

---

## 💼 Commercial Offer: Staging Forensic Audit

* **Tier 1 Diagnostic (€1,500 / 48-Hour Sprint)**: Ingest 250 staging traces, compute Toxic Receipt Index (TRI), deliver executive summary.
* **Tier 2 Forensic Audit (€2,500 / 5-Day Sprint)**: Full wire-level fuzzing, adversarial interception analysis, and `git apply fix.patch` remediation.

Contact: [andrejlo123@gmail.com](mailto:andrejlo123@gmail.com)

---

## ⚖️ Limitations & Boundaries

See [`LIMITATIONS.md`](./LIMITATIONS.md). This tool is a deterministic local test harness in simulation mode; it does not replace hardware HSMs, TLS termination, or certified compliance filings.
