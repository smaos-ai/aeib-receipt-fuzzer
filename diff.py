#!/usr/bin/env python3
"""AEIB Offline Audit Log Scanner (diff.py) v0.2.0

Ingests staging JSONL/OpenTelemetry action traces under NDA, cross-references
claimed dispositions against wire-level transport evidence, and generates
a unified git-diff patch showing where the harness fabricated confirmation.

Produces:
    1. Toxic Receipt Index (TRI %)
    2. Evidence Contamination Breakdown (DORA Art. 17 / EU AI Act Art. 12)
    3. Remediation unified diff (fix.patch) converting toxic claims to fail-closed UNKNOWN

Usage:
    python3 diff.py <traces.jsonl> [--patch-out fix.patch] [--threshold 0.0]
"""

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

from toxic_receipt_detector import (
    ReceiptVerdict,
    verify_receipt,
    jcs_canonicalize,
    jcs_digest,
)


class AuditLogScanner:
    """Scans client staging traces and audits claimed vs evidence dispositions."""

    def __init__(self, trace_file: str):
        self.trace_file = Path(trace_file)
        self.records: List[Dict[str, Any]] = []
        self.audit_results: List[Tuple[Dict[str, Any], ReceiptVerdict, Dict[str, Any]]] = []

    def load_traces(self):
        """Loads traces from JSONL file."""
        if not self.trace_file.exists():
            raise FileNotFoundError(f"Trace file not found: {self.trace_file}")

        with open(self.trace_file, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    record = json.loads(line)
                    record["_line_no"] = line_no
                    self.records.append(record)
                except json.JSONDecodeError as e:
                    print(f"⚠️  Warning: Line {line_no} malformed JSON: {e}", file=sys.stderr)

    def scan(self) -> Dict[str, Any]:
        """Audits all ingested records against Six-Disposition Precedence."""
        total = len(self.records)
        toxic_count = 0
        clean_count = 0
        halt_count = 0

        for record in self.records:
            # Wire-level transport fact observed by gateway/proxy
            wire_fault = record.get("wire_fault", record.get("transport_fault", "NONE"))
            claimed_verdict = record.get("verdict", record.get("status", "UNKNOWN"))
            expected_digest = record.get("expected_digest", None)

            verdict_obj = verify_receipt(
                record,
                expected_digest=expected_digest,
                wire_fault=wire_fault,
            )

            # Determine remediation target
            remediated = dict(record)
            remediated.pop("_line_no", None)

            if not verdict_obj.is_clean:
                toxic_count += 1
                if verdict_obj.verdict == ReceiptVerdict.HALT_DIGEST_MISMATCH:
                    halt_count += 1
                # Fail-closed remediation invariant:
                remediated["verdict"] = "UNKNOWN"
                remediated["status"] = "UNKNOWN"
                remediated["retry_held"] = True
                remediated["remediation_reason"] = verdict_obj.reason
                remediated["evidence_disposition"] = "DORA_ART_17_UNCERTAINTY_HELD"
            else:
                clean_count += 1
                remediated["evidence_disposition"] = "CONFIRMED_SETTLED"

            self.audit_results.append((record, verdict_obj, remediated))

        tri_percentage = (toxic_count / total * 100.0) if total > 0 else 0.0

        return {
            "total_records": total,
            "clean_records": clean_count,
            "toxic_records": toxic_count,
            "halt_records": halt_count,
            "toxic_receipt_index_pct": round(tri_percentage, 2),
        }

    def generate_diff(self) -> str:
        """Generates a unified git diff comparing claimed vs evidence states."""
        original_lines = []
        remediated_lines = []

        for record, verdict_obj, remediated in self.audit_results:
            clean_rec = {k: v for k, v in record.items() if not k.startswith("_")}
            original_lines.append(json.dumps(clean_rec, indent=2))
            remediated_lines.append(json.dumps(remediated, indent=2))

        orig_str = "\n".join(original_lines).splitlines(keepends=True)
        rem_str = "\n".join(remediated_lines).splitlines(keepends=True)

        diff = difflib.unified_diff(
            orig_str,
            rem_str,
            fromfile=f"a/{self.trace_file.name} (Claimed Harness Dispositions)",
            tofile=f"b/{self.trace_file.name} (Evidence-Supported Dispositions)",
            n=2,
        )
        return "".join(diff)


def print_banner(text: str):
    print("\n" + "═" * 74)
    print(f"  {text}")
    print("═" * 74)


def main():
    parser = argparse.ArgumentParser(
        description="AEIB Offline Audit Log Scanner — Ingests staging logs and generates remediation patch."
    )
    parser.add_argument("traces", help="Path to input JSONL trace file")
    parser.add_argument("--patch-out", help="Path to output unified diff patch", default=None)
    args = parser.parse_args()

    print_banner("🔍 AEIB OFFLINE AUDIT LOG SCANNER (diff.py)")
    print("  Enterprise Staging Trace & OpenTelemetry Evidence Interrogator")
    print(f"  Target Log: {args.traces}")

    scanner = AuditLogScanner(args.traces)
    try:
        scanner.load_traces()
    except Exception as e:
        print(f"\n❌ Failed to load traces: {e}", file=sys.stderr)
        sys.exit(1)

    metrics = scanner.scan()

    print("\n" + "─" * 74)
    print(f"  Total Ingested Traces : {metrics['total_records']}")
    print(f"  Clean Receipts (Δ=0)  : {metrics['clean_records']}")
    print(f"  Toxic Receipts        : {metrics['toxic_records']}")
    print(f"  Tampered / Halts      : {metrics['halt_records']}")
    print(f"  Toxic Receipt Index   : {metrics['toxic_receipt_index_pct']}%")
    print("─" * 74)

    if metrics["toxic_records"] > 0:
        print("\n  ⚠️  EVIDENCE CONTAMINATION DETECTED under DORA Art. 17(3)!")
        print("     Harness claimed CONFIRMED on ambiguous wire events.")
    else:
        print("\n  ✅ Zero evidence contamination detected. Harness preserved uncertainty.")

    diff_text = scanner.generate_diff()

    if args.patch_out and diff_text:
        with open(args.patch_out, "w", encoding="utf-8") as f:
            f.write(diff_text)
        print(f"\n  💾 Remediation patch saved to: {args.patch_out}")
        print("     Apply with: git apply " + args.patch_out)
    elif diff_text:
        print("\n--- Unified Diff Sample (First 35 lines) ---")
        preview = "\n".join(diff_text.splitlines()[:35])
        print(preview)

    sys.exit(0 if metrics["toxic_records"] == 0 else 1)


if __name__ == "__main__":
    main()
