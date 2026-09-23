import json
import pytest
from pathlib import Path
from toxic_receipt_detector import (
    ReceiptVerdict,
    verify_receipt,
    jcs_canonicalize,
    jcs_digest,
)
from diff import AuditLogScanner

REPO_ROOT = Path(__file__).resolve().parent.parent

def test_jcs_canonicalize_determinism():
    obj1 = {"b": 2, "a": 1, "nested": {"z": 26, "y": 25}}
    obj2 = {"nested": {"y": 25, "z": 26}, "a": 1, "b": 2}
    assert jcs_canonicalize(obj1) == jcs_canonicalize(obj2)
    assert jcs_digest(obj1) == jcs_digest(obj2)

def test_conformance_vectors():
    vectors_dir = REPO_ROOT / "conformance_vectors"
    vector_files = sorted(vectors_dir.glob("*.json"))
    assert len(vector_files) >= 10

    for vf in vector_files:
        with open(vf, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        verdict = verify_receipt(
            receipt=data.get("receipt", {}),
            expected_digest=data.get("expected_digest"),
            wire_fault=data.get("wire_fault", "NONE"),
        )
        assert isinstance(verdict, ReceiptVerdict)
        assert isinstance(verdict.verdict, str)
        assert verdict.reason != ""

def test_diff_scanner_on_conformance_vectors(tmp_path):
    vectors_dir = REPO_ROOT / "conformance_vectors"
    sample_trace = tmp_path / "traces.jsonl"
    
    with open(sample_trace, "w", encoding="utf-8") as out:
        for vf in sorted(vectors_dir.glob("*.json")):
            with open(vf, "r", encoding="utf-8") as f:
                data = json.load(f)
            rec = {
                "action_id": data.get("vector_id", "act_001"),
                "status": data.get("claimed_verdict", "CONFIRMED"),
                "verdict": data.get("claimed_verdict", "CONFIRMED"),
                "wire_fault": data.get("wire_fault", "NONE"),
                "expected_digest": data.get("expected_digest"),
                "receipt": data.get("receipt", {}),
            }
            out.write(json.dumps(rec) + "\n")
            
    scanner = AuditLogScanner(str(sample_trace))
    scanner.load_traces()
    metrics = scanner.scan()
    assert metrics["total_records"] >= 10
    assert metrics["toxic_records"] > 0
    assert metrics["toxic_receipt_index_pct"] > 0
    
    diff_patch = scanner.generate_diff()
    assert "---" in diff_patch
    assert "+++" in diff_patch
    assert "UNKNOWN" in diff_patch
