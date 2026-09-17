# AEIB Receipt Fuzzer — Limitations & Boundary Declarations

**Version:** 0.2.0  
**Last Updated:** 2026-09-17

---

## What This Tool IS

* A **deterministic local harness** for testing whether agent action
  receipts preserve uncertainty when downstream infrastructure fails.
* A **zero-dependency Python CLI** (3.12+ stdlib only) that runs
  entirely offline with no network egress.
* A **falsifiable demonstration** of wire-level evidence contamination
  that can be reproduced by any engineer with Python installed.

---

## What This Tool IS NOT

1. **Not a production WAF, IDS, or firewall.**  
   The asyncio proxy is a simulation-mode test harness.  It does not
   intercept real TLS traffic, perform deep packet inspection, or
   operate as a reverse proxy in any deployment topology.

2. **Not a cryptographic verification library.**  
   Signature envelope checks test for *field presence* (`signature`,
   `cose_envelope`), not for actual ECDSA P-256 curve point validation
   or COSE_Sign1 CBOR structure parsing.  Production systems MUST use
   a vetted cryptographic library (e.g., `python-jose`, `pycose`,
   `ring`, `openssl`).

3. **Not constant-time.**  
   All hash comparisons use standard Python string equality.  This is
   acceptable for a deterministic test harness but MUST NOT be used in
   security-critical hot paths where timing side-channels apply.

4. **Not a regulatory compliance certification.**  
   References to DORA Art. 17, EU AI Act Art. 12, and RFC 8785 are
   contextual citations indicating which standards the test methodology
   aligns with.  Running this tool does not certify compliance with
   any regulation or standard.

5. **Not a substitute for real reconciliation.**  
   The `SPEC.md` documents future reconciliation adapters (PostgreSQL
   `xid` probes, S3 ETag checks, Kafka offset queries, Stripe
   idempotency lookups).  None of these are implemented in v0.2.0.
   The tool operates entirely on synthetic, locally-generated payloads.

6. **Not production-safe.**  
   The asyncio proxy binds to `127.0.0.1` and is intended for
   single-developer local testing.  It has no authentication,
   rate-limiting, TLS termination, or resource bounds.

---

## Scope Boundary Summary

| Capability | Status |
|:-----------|:-------|
| Wire-level fault injection (7 modes) | ✅ Implemented |
| RFC 8785 JCS canonicalization (key sorting) | ✅ Implemented (subset) |
| ES256 signature field presence check | ✅ Implemented (field-level) |
| ECDSA P-256 curve point validation | ❌ Not implemented |
| COSE_Sign1 CBOR structure parsing | ❌ Not implemented |
| Constant-time hash comparison | ❌ Not implemented |
| Real TLS interception | ❌ Not implemented |
| Reconciliation adapters (PG, S3, Kafka, Stripe) | ❌ Not implemented |
| Regulatory compliance certification | ❌ Out of scope |
