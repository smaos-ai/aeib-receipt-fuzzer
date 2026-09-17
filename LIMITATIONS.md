# AEIB Receipt Fuzzer — Operational & Legal Boundaries

**Standard:** Agent-Effect Integrity Benchmark (AEIB) v0.2.0  
**Scope:** Wire-Level Fault Proxy & Offline Evidence Contamination Detection

---

## 🎯 Purpose & Operating Scope

`aeib-receipt-fuzzer` is a deterministic, offline test harness designed to verify whether an AI agent preserves uncertainty (`verdict: UNKNOWN`) when downstream network operations fail.

* **Simulation-Mode Harness**: Runs locally (`127.0.0.1`) to inject wire faults (HTTP 504 timeouts, TCP RST, JCS digest tampering) into development and CI test pipelines.
* **Zero Dependencies**: Pure Python 3.12+ standard library with no external wheels, no network egress, and no telemetry tax.
* **Offline Trace Scanning**: Analyzes historical JSONL staging logs to identify Toxic Receipts (`CONFIRMED` logged under transport failure).

---

## ⚖️ Operational & Legal Disclaimers

1. **Not a Legal Opinion or Compliance Certification**:  
   Citations to DORA Article 17 and EU AI Act Article 12 define the operational failure modes this benchmark addresses. Using this tool does not confer, imply, or substitute for formal regulatory compliance or statutory certification under European supervisory frameworks.

2. **Simulation vs. Production Topology**:  
   This harness is designed for local test suites and staging trace analysis. It is not an inline production Web Application Firewall (WAF), reverse proxy, or network intrusion detection system (IDS).

3. **Cryptographic Validation**:  
   This tool validates evidence envelope structure and RFC 8785 canonical digest integrity for benchmark evaluation. Production key management and hardware attestation should integrate with audited cryptographic modules (e.g., PKCS#11, HSMs, or STAR Protocol).

4. **Synthetic Baselines**:  
   The open-source suite evaluates synthetic fault vectors and local traces. Live database reconciliation (PostgreSQL transaction verification, Kafka offset tracking, payment gateway idempotency lookups) is provided in dedicated staging forensic engagements.
