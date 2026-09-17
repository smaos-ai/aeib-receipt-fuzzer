#!/usr/bin/env python3
"""AEIB Wire-Level Fault Proxy v0.2.0

Zero-dependency asyncio TCP/HTTP proxy that intercepts agent action
receipts and injects wire-level faults to test harness resilience.

Fault Modes:
    NONE             Forward unmodified (clean pass-through)
    TIMEOUT          HTTP 504 Gateway Timeout after configurable delay
    DROP             TCP connection drop before response
    CONFLICT         HTTP 409 state-version mismatch
    DROP_SIGNATURE   Strip ES256 / COSE_Sign1 signature envelope
    CORRUPT_JCS      Inject RFC 8785 canonicalization mismatch
    EXPIRE_TIMESTAMP Roll back SCITT sequence timestamp
    EDIT_AMOUNT      Silently edit numeric amount field in transit

Usage:
    python3 fuzzer.py [--port PORT] [--timeout-ms MS]
"""

import asyncio
import json
import sys

DEFAULT_PORT = 8080
DEFAULT_TIMEOUT_MS = 500  # Short for demo; production: 5000


class FaultProxy:
    """Asyncio-based wire-level fault injection proxy."""

    def __init__(self, port: int = DEFAULT_PORT, timeout_ms: int = DEFAULT_TIMEOUT_MS):
        self.port = port
        self.timeout_ms = timeout_ms
        self.request_count = 0
        self._server = None

    async def start(self):
        """Start the proxy server (blocks until cancelled)."""
        self._server = await asyncio.start_server(
            self._handle_client, "127.0.0.1", self.port,
        )
        print(
            f"🕷️  AEIB Wire-Level Fault Proxy v0.2.0 "
            f"listening on 127.0.0.1:{self.port}",
            flush=True,
        )
        async with self._server:
            await self._server.serve_forever()

    async def stop(self):
        """Stop the proxy server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    # ── HTTP Parsing ────────────────────────────────────────────

    async def _handle_client(self, reader, writer):
        try:
            request_line = await asyncio.wait_for(
                reader.readline(), timeout=5.0,
            )
            if not request_line:
                writer.close()
                return

            headers = {}
            while True:
                line = await reader.readline()
                if line in (b"\r\n", b"\n", b""):
                    break
                decoded = line.decode("utf-8", errors="replace").strip()
                if ": " in decoded:
                    key, value = decoded.split(": ", 1)
                    headers[key] = value

            content_length = int(headers.get("Content-Length", "0"))
            body = (
                await reader.readexactly(content_length)
                if content_length > 0
                else b"{}"
            )

            self.request_count += 1
            fault_mode = headers.get("X-Fault-Mode", "NONE")

            payload, status_code, status_text = await self._inject_fault(
                fault_mode, body, writer,
            )

            if payload is None:
                return  # Connection was dropped intentionally

            response_body = json.dumps(payload).encode("utf-8")
            response = (
                f"HTTP/1.1 {status_code} {status_text}\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            ).encode("utf-8") + response_body

            writer.write(response)
            await writer.drain()

        except (asyncio.IncompleteReadError, ConnectionResetError,
                asyncio.TimeoutError):
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    # ── Fault Injection Engine ──────────────────────────────────

    async def _inject_fault(self, fault_mode, body, writer):
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            payload = {"error": "invalid_payload"}

        tag = f"[FUZZER] #{self.request_count}"
        print(f"\n{tag} Intercepted POST → Fault: {fault_mode}", flush=True)

        if fault_mode == "TIMEOUT":
            delay_s = self.timeout_ms / 1000.0
            print(f"  → Injecting {self.timeout_ms}ms delay + HTTP 504", flush=True)
            await asyncio.sleep(delay_s)
            return (
                {"error": "gateway_timeout", "fault": "TIMEOUT"},
                504,
                "Gateway Timeout",
            )

        if fault_mode == "DROP":
            print("  → TCP RST: dropping connection", flush=True)
            writer.close()
            return None, None, None

        if fault_mode == "CONFLICT":
            print("  → HTTP 409: state-version mismatch", flush=True)
            payload["_conflict"] = True
            payload["error"] = "state_version_mismatch"
            return payload, 409, "Conflict"

        if fault_mode == "DROP_SIGNATURE":
            payload.pop("signature", None)
            payload.pop("cose_envelope", None)
            print("  → Stripped ES256 / COSE_Sign1 envelope", flush=True)
            return payload, 200, "OK"

        if fault_mode == "CORRUPT_JCS":
            payload["_jcs_tampered"] = True
            payload["__canonicalization_poison"] = "mutated"
            print("  → Injected RFC 8785 canonicalization poison", flush=True)
            return payload, 200, "OK"

        if fault_mode == "EXPIRE_TIMESTAMP":
            payload["timestamp"] = "2020-01-01T00:00:00Z"
            payload["scitt_sequence"] = 0
            print("  → Rolled back SCITT timestamp to 2020-01-01", flush=True)
            return payload, 200, "OK"

        if fault_mode == "EDIT_AMOUNT":
            original = payload.get("amount")
            if isinstance(original, (int, float)):
                tampered = original + 50000
                payload["amount"] = tampered
                print(
                    f"  → SILENT EDIT: €{original:,.2f} → €{tampered:,.2f}",
                    flush=True,
                )
            else:
                print("  → No numeric 'amount' field; forwarding as-is", flush=True)
            return payload, 200, "OK"

        # Default: clean pass-through
        print("  → Forwarding unmodified (CLEAN)", flush=True)
        return payload, 200, "OK"


def run_server(port: int = DEFAULT_PORT, timeout_ms: int = DEFAULT_TIMEOUT_MS):
    """Start the fault proxy server (blocking entry point)."""
    proxy = FaultProxy(port=port, timeout_ms=timeout_ms)
    try:
        asyncio.run(proxy.start())
    except KeyboardInterrupt:
        print("\n[FUZZER] Shutting down.", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AEIB Wire-Level Fault Proxy")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS)
    args = parser.parse_args()
    run_server(port=args.port, timeout_ms=args.timeout_ms)
