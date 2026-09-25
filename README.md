# 🏛️ SovereignNexus / SMAOS

> **Sovereign Multi-Agent Operating System (SMAOS)**  
> *Deterministic, Zero-Egress Wire-Truth Verification & Governance Substrate for Autonomous Agent Swarms.*
> 
> **Bring Your Own Harness (BYOH):** Works with your existing harness. No new SDKs. We observe the wire.

[![CI](https://github.com/smaos-ai/aeib-receipt-fuzzer/actions/workflows/ci.yml/badge.svg)](https://github.com/smaos-ai/aeib-receipt-fuzzer/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/smaos-ai/aeib-receipt-fuzzer/badge)](https://securityscorecards.dev/viewer/?uri=github.com/smaos-ai/aeib-receipt-fuzzer)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev/)
[![Zero Egress](https://img.shields.io/badge/Egress-0_Bytes_(127.0.0.1)-brightgreen.svg)](#zero-egress-guarantee)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![DEMM-Bench](https://img.shields.io/badge/DEMM--Bench-75%25_Overclaim_Rate-red.svg)](https://arxiv.org/abs/2606.20634)
[![EU DORA](https://img.shields.io/badge/EU_DORA-RTS_2024%2F1772_Ready-orange.svg)](docs/DORA_ARTICLE_17_COMPLIANCE.md)
[![IETF](https://img.shields.io/badge/IETF-AAT_draft--04-green.svg)](docs/CRYPTOGRAPHY.md)

---

## 🧭 Who Are You? (Find Your Solution)
We built **SMAOS** to bridge the gap between engineering reality and regulatory mandates. Find your role below to see how our open-core verifier solves your exact operational bottleneck without exposing private data or IP.

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             SELECT YOUR PERSPECTIVE                              │
├───────────────────────────┬────────────────────────────┬─────────────────────────┤
│   🛠️ CTO & ARCHITECTS      │     🔒 CISO & SECOPS       │  ⚖️ RISK & COMPLIANCE   │
│   • Stopping Ledger Drift │     • Zero-Egress Proofs   │  • DORA RTS 2024/1772   │
│   • Eliminating 504 Flaws │     • Anti-Replay Testing  │  • ISO 42001 Clause 9   │
└───────────────────────────┴────────────────────────────┴─────────────────────────┘
```

---

### 🛠️ For the CTO & Lead Architect: Stopping Silent Ledger Drift
* **Your Pain**: Agent SDKs swallow `HTTP 504 Gateway Timeouts` and falsely log `CONFIRMED`. Your databases fall out of sync with payment gateways, causing silent ledger drift and 4:00 AM reconciliation failures.
* **The Ground Truth**: **DEMM-Bench (arXiv:2606.20634)** proves that across 64 cases and eight evidence regimes, "full traces" and "schema validation" overclaim on **75% of dropped wire cases** (*The Container Fallacy*). The records look complete, but cannot prove what actually occurred on the wire.
* **Our Verifiable Proof**: `aeib-receipt-fuzzer` simulates local wire faults (`504_timeout`, `tcp_reset`). While standard agent SDKs swallow exceptions, SMAOS intercepts the wire state, redacts PII in-memory, and records the discrepancy as **`dispatched_unconfirmed`**.
* **The Drop-In Patch**: You receive a 15-line Java filter (`ProofOrStopFilter.java`) to immediately patch Spring Boot backends and fail closed.
* **Explore**: [smaos-ai/aeib-receipt-fuzzer](https://github.com/smaos-ai/aeib-receipt-fuzzer) · [fixtures/504_timeout.json](https://github.com/smaos-ai/aeib-receipt-fuzzer/blob/main/fixtures/504_timeout.json)

---

### 🔒 For the CISO & SecOps: Zero-Egress Wire-Truth Verification
* **Your Pain**: You cannot send staging traces, PII, or financial payloads to third-party SaaS logging clouds. Text-based logs can be forged, and standard observability tools record whatever status the agent harness claims rather than testing socket-level reality.
* **The Ground Truth**: Standard observability tools (LangSmith, Datadog LLM Observability, Braintrust) record what the agent harness reports. They answer "what did the SDK log?"—not "was uncertainty preserved on wire fault?"
* **Our Verifiable Proof**: SMAOS operates 100% air-gapped on loopback (`127.0.0.1`) under `network_mode: "none"` with active in-memory regex scrubbing for IBANs (`[REDACTED_IBAN]`), PANs, and JWTs before disk writes.
* **Deliverable**: An executable local test suite and CISO-defensible evidence package—not another cloud dashboard.
* **Explore**: [ghost_audit_scanner.py](https://github.com/smaos-ai/aeib-receipt-fuzzer/blob/main/ghost_audit_scanner.py) · [docs/CRYPTOGRAPHY.md](https://github.com/smaos-ai/aeib-receipt-fuzzer/blob/main/docs/CRYPTOGRAPHY.md)

---

### ⚖️ For Risk & Compliance Officers: Defending DORA Art. 17 & ISO 42001
* **Your Pain**: An agent logging a false payment confirmation during a gateway timeout is an unclassified major ICT incident. Under **EBA DORA RTS 2024/1772 Article 17**, reporting failures carry daily periodic penalties up to **1% of average daily worldwide turnover**.
* **Reporting Timeline Mandate**: Initial notification required within 4 to 24 hours of detection; intermediate report within 72 hours; final report within 1 month.
* **Our Verifiable Proof**: SMAOS auto-formats wire evidence into machine-readable dossiers (`dora_art17_gap_report.json`) and visual sequence diagrams (`audit_trace.mermaid`) required for DORA Article 28(3) and ISO 42001 Clause 9 Statement of Applicability (SoA) sign-offs.
* **Explore**: [standards_mapping/EU_DORA_ART_17.md](https://github.com/smaos-ai/aeib-receipt-fuzzer/blob/main/standards_mapping/EU_DORA_ART_17.md) · [validate_dora_register.py](https://github.com/smaos-ai/aeib-receipt-fuzzer/blob/main/validate_dora_register.py)

---

### 🏗️ For the Lead Architect: Standardized Transport & Negative Controls
* **Your Pain**: Writing brittle, custom retry logic for every agent workflow because LLM frameworks lack standardized state handling.
* **The Ground Truth**: The **IETF Agent Action Capsule draft** standardizes transport effects into three values: `confirmed`, `dispatched_unconfirmed`, and `not_applicable`.
* **Our Verifiable Proof**: Test our logic on local metal with zero trust:

```bash
# Run local zero-egress fault injection — no external registry required
git clone https://github.com/smaos-ai/aeib-receipt-fuzzer
cd aeib-receipt-fuzzer
python3 run.py --scenario 504_timeout --export-dir ./audit_out
# Optional: build and run local container (builds from source, no Docker Hub pull)
docker build -t smaos-demo:0.4.0 .
docker run --rm -p 127.0.0.1:8765:8765 --network none smaos-demo:0.4.0
```

#### Scenario Disposition & NIST AI RMF 1.0 Conformance Matrix (9 Vectors)
| Canonical ID | Risk-Prevention UX Alias | NIST AI RMF | Wire Event | SDK Claim | SMAOS Disposition | Risk Mitigated |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `504_timeout` | **`prevent_silent_double_spend_on_504`** | **MEASURE 2.1** | HTTP 504 Gateway Timeout | `CONFIRMED` | **`dispatched_unconfirmed`** | Silent timeout drop & double spend |
| `tcp_reset` | **`prevent_unconfirmed_settlement_on_reset`** | **MEASURE 2.7** | TCP RST mid-transmission | `CONFIRMED` | **`dispatched_unconfirmed`** | Mid-stream connection severance |
| `confirmed` | **`confirmed_settlement_baseline`** | **GOVERN 1.2** | HTTP 200 Settlement | `CONFIRMED` | **`CONFIRMED`** | Clean settlement baseline (Negative Control) |
| `refused` | **`policy_refusal_baseline`** | **MANAGE 1.3** | HTTP 403 Gateway Refusal | `REFUSED` | **`REFUSED`** | Downstream policy refusal (Negative Control) |
| `delayed_confirmation` | **`prevent_stale_state_override_on_late_ack`** | **MEASURE 2.1** | HTTP 200 arrived post-deadline (t+65s) | `CONFIRMED` | **`dispatched_unconfirmed`** | Late-arriving orphan settlement |
| `duplicate_retry_same_payload` | **`prevent_duplicate_execution_on_retry`** | **MANAGE 1.3** | HTTP 409 duplicate retry in-flight | `RETRY_DISPATCH` | **`CONFLICT`** | Unverified duplicate retry storm |
| `payload_mutation_on_retry` | **`prevent_unauthorized_payload_mutation`** | **MAP 1.5** | HTTP 409 payload hash mismatch | `CONFIRMED` | **`CONFLICT`** | Mutation under reused idempotency key |
| `malformed_response` | **`prevent_invalid_schema_ingestion`** | **MEASURE 2.6** | HTTP 200 with corrupted JSON | `CONFIRMED` | **`INVALID_INPUT`** | Downstream schema contract violation |
| `unauthorized_handoff` | **`prevent_unauthorized_handoff_escalation`** | **GOVERN 1.2** | HTTP 403 Forbidden - Delegation Ceiling Exceeded | `REFUSED` | **`REFUSED`** | Unauthorized capability escalation |

*The `confirmed` and `refused` controls are essential: they prove the engine accurately distinguishes verified settlement from unconfirmed drops.*

* **CLI Execution**: Run any scenario by canonical ID or alias: `python3 run.py --scenario prevent_silent_double_spend_on_504 --export-dir ./audit_out`
* **NIST & Risk Matrix**: [`scenarios.md`](scenarios.md) (Full control mappings, failure modes, and scoring rubrics).
* **Offline Verification Guide**: [`VERIFY_OFFLINE.md`](VERIFY_OFFLINE.md) (Step-by-step air-gap auditing via browser, WASM, or CLI).

### 🔐 Air-Gapped & Offline Verification (Browser & WebAssembly)

For air-gapped auditor reviews and zero-egress compliance inspections:
* **Drag-and-Drop Browser Verifier (`smaos_verify/verify_offline.html`)**: Open directly via `file://` in Chrome, Firefox, or Safari. Drag and drop any `disposition_report.json` onto the window to instantly recompute the RFC 8785 (JCS) canonical SHA-256 digest via native Web Crypto, check Ed25519 signature fields, and verify EU AI Act Article 14 human oversight status. **0 external network requests, 0 dependencies, runs 100% client-side.**
* **Pure Rust WebAssembly Binary (`smaos_verify/smaos_verify.wasm`)**: 167 KB standalone WASM binary compiled for zero-trust pipelines and sandboxed enclaves.

---

## ⚠️ What This Solution Does & Does Not Claim

### What It Does:
* Injects controlled wire faults on `127.0.0.1` to test harness uncertainty preservation.
* Scrubs PII/PCI in-memory prior to local file writes (0 byte cloud egress).
* Enforces EU AI Act Article 14 human oversight gates (`awaiting_human_validation`) across all receipts.
* Emits executive `trust_passport.json` summaries, machine-readable DORA Art. 17 dossiers, and ISO 42001 sequence traces.
* Delivers drop-in Java (`ProofOrStopFilter.java`) and Python (`@proof_or_stop`) remediation patches.
* Ships an offline WebAssembly verifier (`smaos_verify.wasm`) and browser verifier (`verify_offline.html`) for air-gapped auditing.
* Delivers a permanent, re-runnable local regression test suite for your engineering team.

### What It Does NOT Claim:
* Does **not** certify DORA, ISO 42001, or EU AI Act compliance.
* Does **not** prove external system truth (proves whether harness claims are supported by wire evidence).
* Does **not** detect prompt injection, model drift, or memory poisoning outside the wire-fault scenario.
* Does **not** replace internal audit, risk, or compliance reviews.

---

## 🏛️ The Open-Core Model: One Core, Two Doors
```text
┌──────────────────────────────────────────────────┐      ┌──────────────────────────────────────────────────┐
│             DOOR 1: PUBLIC TRUST                 │      │            DOOR 2: PRIVATE IP (COMMERCIAL)       │
│              (Apache License 2.0)                │      │               (Closed Source)                    │
├──────────────────────────────────────────────────┤      ├──────────────────────────────────────────────────┤
│ • Local Wire Engine (`run.py`)                   │      │ • Continuous eBPF Kernel Event Drivers           │
│ • GII Audit Scanner (`ghost_audit_scanner.py`)   │      │ • Real-time Neural Routing & Context Compaction  │
│ • DORA Register xBRL-CSV Validator               │  ──► │ • Multi-Node Enterprise Consensus Engine         │
│ • Drop-in Remediation (`ProofOrStopFilter.java`) │      │ • Automated State-Machine Recovery & Synthesis   │
│ • 15 IETF Conformance Test Vectors               │      │ • Enterprise Governance Platform (SMAOS)         │
└──────────────────────────────────────────────────┘      └──────────────────────────────────────────────────┘
```

---

---

## 🔬 What Others Test vs. What SMAOS Tests

| What standard observability tools test | What SMAOS tests |
|:---------------------------------------|:-----------------|
| What the agent/SDK **reports** happened | What the **wire transport** actually delivered |
| Whether a tool call was made | Whether the call's outcome was confirmed by the socket |
| Records the SDK's `CONFIRMED` log faithfully | Tests whether `CONFIRMED` is justified by wire evidence |
| Model reasoning and task output | System behavior at the transport boundary |

SMAOS does not measure model intelligence, prompt safety, or general agent capability.  
It measures one thing: **does the harness preserve uncertainty when the wire does not confirm completion?**

See [`scenarios.md`](scenarios.md), [`METHODOLOGY.md`](METHODOLOGY.md), and [`LIMITATIONS.md`](LIMITATIONS.md) for the full scope.

---

## 🚀 Roadmap: Beyond v0.4.0

The following capabilities are under active development and scheduled for subsequent releases:

* **IETF AAT Draft-04 Digests**: Binding 5 decision-reproducibility digests (`model_weights`, `tokenizer`, `chat_template`, `engine_build`, `numeric_environment`) into every receipt.
* **Post-Quantum Cryptography**: ML-DSA-65 (FIPS 204) dual-signing capability.
* **Continuous eBPF Kernel Probes**: Non-invasive kernel-level socket capture for high-throughput production clusters (Door 2).

---

## 🏛️ Enterprise Support & Research Inquiries

* **Open-Source Testing**: Run `docker run --network none` locally to evaluate your agent harness against simulated HTTP 504 transport drops on your own hardware with zero data egress.
* **Architecture & Governance Inquiries**: For enterprise pilot integrations, regulatory sandbox participation, or technical inquiries regarding DORA Article 17 and EU AI Act Article 14 controls:
  * **Contact**: `andrejlo123@gmail.com` | **SovereignNexus s.r.o.**, Prague, Czech Republic.

---
*One command. Eight scenarios. Zero egress. The truth is on the wire.*
