#!/usr/bin/env python3
"""Integration checks for mcp_stdio_http.py using an in-process fake MCP peer."""
import concurrent.futures
import http.client
import json
import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent

FAKE = r'''import json, sys, time
initializes = 0
max_active = 0
active = 0
for line in sys.stdin:
    m = json.loads(line)
    method = m.get("method")
    if method == "initialize":
        initializes += 1
        out = {"jsonrpc":"2.0", "id":m["id"], "result":{"protocolVersion":"2025-03-26","capabilities":{"tools":{}},"serverInfo":{"name":"fake","version":"1"}}}
        print(json.dumps(out), flush=True)
    elif method == "notifications/initialized":
        pass
    elif method == "tools/list":
        print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"tools":[{"name":"echo"}]}}), flush=True)
    elif method == "tools/call":
        active += 1
        max_active = max(max_active, active)
        time.sleep(0.025)
        result = {"content":[{"type":"text","text":m.get("params",{}).get("arguments",{}).get("value","")}]}
        print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":result}), flush=True)
        active -= 1
    elif method == "test/delay":
        time.sleep(0.15)
        print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"late":True}}), flush=True)
    elif method == "test/server-request":
        print(json.dumps({"jsonrpc":"2.0","id":"server-originated-1","method":"sampling/createMessage","params":{}}), flush=True)
        reply = json.loads(sys.stdin.readline())
        print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"serverReply":reply}}), flush=True)
    else:
        if "id" in m:
            print(json.dumps({"jsonrpc":"2.0","id":m["id"],"error":{"code":-32601,"message":"method not found"}}), flush=True)
'''


def request(port, payload, path="/mcp"):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    raw = json.dumps(payload).encode()
    conn.request("POST", path, raw, {"Content-Type": "application/json"})
    resp = conn.getresponse()
    data = resp.read()
    status = resp.status
    conn.close()
    return status, json.loads(data) if data else None


def main():
    with tempfile.TemporaryDirectory() as td:
        fake_path = pathlib.Path(td) / "fake_backend.py"
        fake_path.write_text(FAKE, encoding="utf-8")
        sys.path.insert(0, str(HERE))
        import mcp_stdio_http as bridge

        backend = bridge.Backend(sys.executable, [str(fake_path)], td, td, 2.0)
        server = bridge.ThreadingHTTPServer(("127.0.0.1", 0), bridge.Handler)
        server.allow_ips = {"127.0.0.1"}
        server.backend = backend
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]
        try:
            # Health is available before any MCP handshake.
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
            conn.request("GET", "/health")
            health = conn.getresponse()
            assert health.status == 200 and json.loads(health.read())["status"] == "ok"
            conn.close()

            status, init1 = request(port, {"jsonrpc":"2.0","id":"client-A","method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1"}}})
            assert status == 200 and init1["id"] == "client-A" and init1["result"]["protocolVersion"] == "2025-03-26"
            _, init2 = request(port, {"jsonrpc":"2.0","id":77,"method":"initialize","params":{}})
            assert init2["id"] == 77 and init2["result"] == init1["result"]
            assert request(port, {"jsonrpc":"2.0","method":"notifications/initialized"})[0] == 204
            _, listed = request(port, {"jsonrpc":"2.0","id":"list-id","method":"tools/list"})
            assert listed["id"] == "list-id" and listed["result"]["tools"][0]["name"] == "echo"

            def call(i):
                return request(port, {"jsonrpc":"2.0","id":"id-%d" % i,"method":"tools/call","params":{"name":"echo","arguments":{"value":str(i)}}})
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(call, range(12)))
            for i, (st, value) in enumerate(results):
                assert st == 200 and value["id"] == "id-%d" % i
                assert value["result"]["content"][0]["text"] == str(i)

            _, unknown = request(port, {"jsonrpc":"2.0","id":"bad","method":"not/a/method"})
            assert unknown["error"]["code"] == -32601
            _, rejected = request(port, {"jsonrpc":"2.0","id":"srv","method":"test/server-request"})
            assert rejected["result"]["serverReply"]["error"]["code"] == -32601

            # A late reply after timeout must be discarded, not answered as a
            # server request. The following real request must still succeed.
            backend.timeout = 0.05
            _, timed_out = request(port, {"jsonrpc":"2.0","id":"slow","method":"test/delay"})
            assert timed_out["error"]["code"] == -32001
            backend.timeout = 2.0
            _, after_timeout = request(port, {"jsonrpc":"2.0","id":"after","method":"tools/list"})
            assert after_timeout["id"] == "after" and after_timeout["result"]["tools"][0]["name"] == "echo"

            # Peer allowlist is enforced against the actual TCP peer address.
            server.allow_ips = {"10.0.2.2"}
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
            conn.request("GET", "/health")
            assert conn.getresponse().status == 403
            conn.close()
            print("protocol bridge checks passed")
        finally:
            server.shutdown()
            server.server_close()
            # Close only test resources; bridge production deliberately leaves backend alive.
            backend.proc.terminate()
            backend.proc.wait(timeout=3)
            backend._stderr.close()


if __name__ == "__main__":
    main()
