#!/usr/bin/env bash
set -euo pipefail

echo "======================================================================"
echo "🚀 AEIB RECEIPT FUZZER & DETECTOR DEMO"
echo "======================================================================"

python3 fuzzer.py > fuzzer_output.log 2>&1 &
FUZZER_PID=$!
sleep 1

echo ""
echo ">>> BASELINE: Generating a valid AEIB receipt..."
VALID_RECEIPT='{"id": "aeib-req-99", "status": "CONFIRMED", "timestamp": "2026-09-16T12:00:00Z", "signature": "eyJhbGciOiJFUzI1NiJ9..."}'

echo ">>> SCENARIO 1: Clean Pass-Through"
curl -s -X POST -H "Content-Type: application/json" -H "X-Fault-Mode: NONE" -d "$VALID_RECEIPT" http://127.0.0.1:8080 | python3 toxic_receipt_detector.py || true
sleep 0.5

echo ""
echo ">>> SCENARIO 2: Dropped Signature (Fault)"
curl -s -X POST -H "Content-Type: application/json" -H "X-Fault-Mode: DROP_SIGNATURE" -d "$VALID_RECEIPT" http://127.0.0.1:8080 | python3 toxic_receipt_detector.py || true
sleep 0.5

echo ""
echo ">>> SCENARIO 3: Tampered Payload (JCS Mismatch)"
curl -s -X POST -H "Content-Type: application/json" -H "X-Fault-Mode: CORRUPT_JCS" -d "$VALID_RECEIPT" http://127.0.0.1:8080 | python3 toxic_receipt_detector.py || true
sleep 0.5

echo ""
echo ">>> SCENARIO 4: Rollback Attack (Expired SCITT Timestamp)"
curl -s -X POST -H "Content-Type: application/json" -H "X-Fault-Mode: EXPIRE_TIMESTAMP" -d "$VALID_RECEIPT" http://127.0.0.1:8080 | python3 toxic_receipt_detector.py || true
sleep 0.5

echo ""
echo "======================================================================"
echo "🛑 Shutting down fuzzer (PID: $FUZZER_PID)..."
kill $FUZZER_PID
wait $FUZZER_PID 2>/dev/null || true
echo "--- Fuzzer Logs ---"
cat fuzzer_output.log
echo "✅ Demo completed."
