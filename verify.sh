#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo "🕷️  AEIB Receipt Fuzzer v0.2.0 — Verification"
echo "=================================================="

cd "$(dirname "$0")"

echo ""
echo ">>> Step 1: Running demo_killshot.py (5 scenarios)..."
python3 demo_killshot.py
EXIT_CODE=$?

if [ "$EXIT_CODE" -ne 0 ]; then
    echo ""
    echo "❌ VERIFICATION FAILED: demo_killshot.py exited with code $EXIT_CODE"
    exit 1
fi

echo ""
echo ">>> Step 2: Testing Offline Audit Log Scanner (diff.py) on Conformance Vectors..."
python3 -c '
import glob, json
files = sorted(glob.glob("conformance_vectors/*.json"))
assert len(files) == 10, f"Expected 10 vectors, found {len(files)}"
with open("sample_traces.jsonl", "w") as out:
    for f in files:
        out.write(json.dumps(json.load(open(f))) + "\n")
print(f"  ✓ Packed {len(files)} conformance vectors into sample_traces.jsonl")
'

# Run diff.py (expects exit 1 because toxic receipts are deliberately present)
set +e
python3 diff.py sample_traces.jsonl --patch-out fix.patch > diff_output.log 2>&1
DIFF_EXIT=$?
set -e

if [ "$DIFF_EXIT" -eq 1 ] && grep -q "EVIDENCE CONTAMINATION DETECTED" diff_output.log; then
    echo "  ✓ diff.py correctly flagged evidence contamination and generated fix.patch"
else
    echo "❌ VERIFICATION FAILED: diff.py failed unexpectedly (code $DIFF_EXIT)"
    cat diff_output.log
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ All aeib-receipt-fuzzer verification passed (5 scenarios + 10 vectors + diff.py)."
echo "=================================================="
