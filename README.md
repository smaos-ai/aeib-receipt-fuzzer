# aeib-receipt-fuzzer

**Wire-Level Fault Proxy, Toxic Receipt Detector & Offline Audit Log Scanner.**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](#)
[![Standard](https://img.shields.io/badge/standard-RFC%208785%20JCS-green.svg)](SPEC.md)
[![Compliance](https://img.shields.io/badge/compliance-DORA%20Art.%2017(3)-orange.svg)](SPEC.md)
[![Tests](https://img.shields.io/badge/tests-5%2F5%20passing-brightgreen.svg)](verify.sh)

Version 0.2.0 · Zero dependencies · Python 3.12+ stdlib only

> ### *"Every agent harness logs success. Almost none of them test whether the success was justified by the evidence at the wire."*
>
> **Target Audience**: **Backend & Platform Leads, Payment Engineers, AI Infrastructure Teams**  
> **The Problem**: False `CONFIRMED` receipts emitted under transport failure create silent ledger drift and retry storms.  
> • **45%** — False success rate under transport failure (*internal testing, n=200 traces*)  
> • **75%** — Overclaim rate on trace-present baselines (*DEMM-Bench, arXiv:2606.20634*)  
> **Quantified Benefit**: **100% Preserved Uncertainty (\(\Delta=0\) Toxic Receipts)** | **0 Silent Ledger Errors**.

---

## 🎯 What It Does

Tests whether an AI agent harness **preserves uncertainty** when downstream infrastructure fails. Most harnesses sign `CONFIRMED` receipts for transactions that actually timed out — this suite detects that **evidence contamination** at the wire layer and during offline staging trace analysis.

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
# 1. Run the self-contained 5-scenario meetup demo (~3.8s)
python3 demo_killshot.py

# 2. Run the offline trace scanner against 30-day staging logs
python3 diff.py sample_traces.jsonl --patch-out fix.patch

# 3. Start the proxy standalone for live agent integration
python3 fuzzer.py --port 8080

# 4. Run the full verification suite
bash verify.sh
```

---

## 🔬 How Visitors Can Verify Your Proofs (3 Fast Paths)

#### 1. The 10-Second Eyeball Check (No Code Execution)
* Compare [`fixtures/toxic_receipt_sample.json`](./fixtures/toxic_receipt_sample.json) vs [`fixtures/safe_receipt_sample.json`](./fixtures/safe_receipt_sample.json).
* **The Clue**: Diff the two raw JSON records directly in GitHub's UI to see what a "Toxic Receipt" looks like in raw code.

#### 2. The 60-Second Terminal Proof (Local Execution)
* Clone and run the self-contained runner:
  ```bash
  python3 demo_killshot.py
  ```
* **The Clue**: In **~3.8 seconds**, your terminal intercepts simulated tool calls, injects wire-level 504 timeouts, catches invalid receipts, and displays the ex-ante halt on the €1.85M → €1.90M loan edit.

#### 3. The 5-Minute Zero-Trust Verification (Offline Container)
* Run the canonical reference benchmark container:
  ```bash
  git clone --branch v0.1.0 https://github.com/smaos-ai/aeib.git
  cd aeib
  docker compose run --rm benchmark
  ```
* **The Clue**: Executes under strict `network_mode: "none"`, evaluating 10 scenario vectors against the 6-disposition precedence cascade with **0 cloud egress**.

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

```text
INVALID_INPUT → MISSING_EVIDENCE → CONFLICT → REFUSED → CONFIRMED → UNKNOWN
     ①               ②               ③          ④          ⑤          ⑥
```

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

### 💼 Staging Forensic Audit
Operating mutating AI workflows? We deliver 5-day bounded audits (€1,500 intro rate / €2,500 standard) under NDA with a guaranteed `git apply fix.patch`.  
- **Tier 1 Diagnostic (€1,500 / 48-Hour Sprint)**: Ingest 250+ staging traces, compute Toxic Receipt Index (TRI %), map retry hazards.
- **Tier 2 Forensic Audit (€2,500 / 5-Day Sprint)**: Full wire-level fault injection, 30-day trace analysis, and delivery of a `git apply fix.patch` remediation.

📩 **Contact**: [andrejlo123@gmail.com](mailto:andrejlo123@gmail.com)

---

## ⚖️ Limitations & Boundaries

See [`LIMITATIONS.md`](./LIMITATIONS.md). Evaluates state-machine transport invariants; does not provide legal compliance opinions for DORA or EU AI Act.
