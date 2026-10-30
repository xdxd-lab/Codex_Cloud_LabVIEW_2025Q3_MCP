#!/usr/bin/env python3
"""Private HTTP-to-stdio transport for a reviewed MCP server binary.

This is a local testing bridge, not a public production ChatGPT connector.
"""
import argparse
import collections
import http.server
import itertools
import json
import logging
import os
import queue
import socket
import subprocess
import sys
import threading
import time

MAX_BODY = 8 * 1024 * 1024
DEFAULT_ALLOW = ("127.0.0.1", "10.0.2.2")


def rpc_error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id,
            "error": {"code": code, "message": message}}


class Backend:
    def __init__(self, command, args, cwd, log_dir, timeout):
        os.makedirs(log_dir, exist_ok=True)
        err_path = os.path.join(log_dir, "backend.stderr.log")
        self._stderr = open(err_path, "ab", buffering=0)
        self.proc = subprocess.Popen(
            [command] + args, cwd=cwd, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=self._stderr, bufsize=0)
        self.timeout = timeout
        self.lines = queue.Queue()
        self.write_lock = threading.Lock()
        self.request_lock = threading.RLock()
        self.ids = itertools.count(1)
        self.pending = {}
        self.pending_lock = threading.Lock()
        self.initialized = False
        self.initialize_result = None
        self.initialized_notification_sent = False
        self.protocol_version = None
        self.log = logging.getLogger("mcp_bridge")
        self.reader = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader.start()

    def _read_stdout(self):
        try:
            while True:
                line = self.proc.stdout.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line.decode("utf-8"))
                except Exception:
                    self.log.warning("backend emitted invalid JSON frame")
                    continue
                if isinstance(msg, dict) and "id" in msg:
                    with self.pending_lock:
                        waiter = self.pending.get(str(msg["id"]))
                    if waiter is not None:
                        waiter.put(msg)
                    elif "method" in msg:
                        # The MCP server can issue requests (for example sampling or
                        # elicitation). This HTTP bridge has no client callback path,
                        # so answer promptly instead of leaving the server blocked.
                        self.log.info("rejected backend-initiated request method=%s",
                                      msg.get("method", "<unknown>"))
                        self._send(rpc_error(msg.get("id"), -32601,
                                             "Client-initiated requests are unsupported by this bridge"))
                    else:
                        # A timed-out operation can still complete. Its late response
                        # is not a new server request and must not trigger an error loop.
                        self.log.info("discarded late backend response")
                else:
                    # Server notifications are intentionally not exposed over HTTP.
                    self.log.info("ignored backend notification")
        finally:
            with self.pending_lock:
                waiters = list(self.pending.values())
            for waiter in waiters:
                try:
                    waiter.put_nowait(None)
                except queue.Full:
                    pass
            self.lines.put(None)

    def _send(self, message):
        payload = (json.dumps(message, separators=(",", ":"),
                              ensure_ascii=False) + "\n").encode("utf-8")
        with self.write_lock:
            if self.proc.poll() is not None:
                raise RuntimeError("backend process exited")
            self.proc.stdin.write(payload)
            self.proc.stdin.flush()

    def _request(self, method, params=None):
        internal_id = "bridge-%d" % next(self.ids)
        waiter = queue.Queue(maxsize=1)
        with self.pending_lock:
            self.pending[internal_id] = waiter
        req = {"jsonrpc": "2.0", "id": internal_id, "method": method}
        if params is not None:
            req["params"] = params
        try:
            self._send(req)
            response = waiter.get(timeout=self.timeout)
        except queue.Empty:
            raise TimeoutError("backend request timed out; mutation state is unknown")
        finally:
            with self.pending_lock:
                self.pending.pop(internal_id, None)
        if response is None:
            raise RuntimeError("backend process exited")
        return response

    def _notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)

    def handle(self, request):
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
            return rpc_error(request.get("id") if isinstance(request, dict) else None,
                             -32600, "Invalid Request"), False
        method = request.get("method")
        if not isinstance(method, str):
            return rpc_error(request.get("id"), -32600, "Invalid Request"), False
        has_id = "id" in request
        request_id = request.get("id")
        params = request.get("params")
        if not has_id:
            if method == "notifications/initialized":
                if not self.initialized_notification_sent:
                    self._notify(method, params)
                    self.initialized_notification_sent = True
                return None, True
            # Unknown notifications have no response by JSON-RPC definition.
            return None, True
        if method == "initialize":
            if self.initialize_result is None:
                response = self._request(method, params)
                # Cache a successful handshake so reconnecting HTTP clients do
                # not initialize the same process twice. Errors remain retryable.
                if "result" in response:
                    self.initialize_result = response
                    result = response["result"]
                    if isinstance(result, dict):
                        self.protocol_version = result.get("protocolVersion")
                    self.initialized = True
                    if self.initialized_notification_sent is False:
                        # Client notification may follow later; do not synthesize it.
                        pass
                return self._restore_id(response, request_id), False
            cached = dict(self.initialize_result)
            cached["id"] = request_id
            return cached, False
        if not self.initialized:
            return rpc_error(request_id, -32000, "Initialize the MCP session first"), False
        if method == "sampling/createMessage" or method.startswith("elicitation/"):
            return rpc_error(request_id, -32601,
                             "Server-initiated requests are unsupported by this bridge"), False
        if method == "notifications/initialized":
            if not self.initialized_notification_sent:
                self._notify(method, params)
                self.initialized_notification_sent = True
            return rpc_error(request_id, -32600, "Notification must not include an id"), False
        try:
            response = self._request(method, params)
            return self._restore_id(response, request_id), False
        except TimeoutError as exc:
            return rpc_error(request_id, -32001, str(exc)), False
        except (BrokenPipeError, OSError, RuntimeError) as exc:
            return rpc_error(request_id, -32002, "backend unavailable: %s" % exc), False

    @staticmethod
    def _restore_id(response, original_id):
        result = dict(response)
        result["id"] = original_id
        return result


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "PrivateMCPBridge/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        # Avoid default request-line logging, which can contain sensitive query text.
        return

    def _send_bytes(self, status, body=b"", content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        if body:
            self.wfile.write(body)
        self.close_connection = True

    def _peer_allowed(self):
        return self.client_address[0] in self.server.allow_ips

    def do_GET(self):
        if not self._peer_allowed():
            self._send_bytes(403, b'{"error":"forbidden"}')
            return
        if self.path == "/mcp":
            self._send_bytes(405, b'{"error":"SSE GET is not supported; use JSON POST"}')
            return
        if self.path != "/health":
            self._send_bytes(404, b'{"error":"not found"}')
            return
        # Intentionally independent of MCP initialization and COM state.
        proc = self.server.backend.proc
        healthy = proc.poll() is None
        body = json.dumps({"status": "ok" if healthy else "backend_exited"}).encode()
        self._send_bytes(200 if healthy else 502, body)

    def do_POST(self):
        if not self._peer_allowed():
            self._send_bytes(403, b'{"error":"forbidden"}')
            return
        if self.path != "/mcp":
            self._send_bytes(404, b'{"error":"not found"}')
            return
        if self.headers.get_content_type() != "application/json":
            self._send_bytes(415, b'{"error":"application/json required"}')
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0:
            self._send_bytes(411, b'{"error":"Content-Length required"}')
            return
        if length > MAX_BODY:
            self._send_bytes(413, b'{"error":"request too large"}')
            return
        raw = self.rfile.read(length)
        if len(raw) != length:
            self._send_bytes(400, b'{"error":"incomplete request body"}')
            return
        try:
            request = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send_bytes(400, b'{"error":"invalid JSON"}')
            return
        backend = self.server.backend
        start = time.time()
        method = request.get("method", "<batch>") if isinstance(request, dict) else "<invalid>"
        # One lock around all client protocol work, including initialize cache.
        with backend.request_lock:
            try:
                response, notification = backend.handle(request)
                status = 204 if notification else 200
                body = b"" if notification else json.dumps(
                    response, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            except TimeoutError as exc:
                status = 200
                body = json.dumps(rpc_error(request.get("id") if isinstance(request, dict) else None,
                                            -32001, str(exc))).encode()
            except (BrokenPipeError, OSError, RuntimeError) as exc:
                status = 502
                body = json.dumps({"error": "backend unavailable: %s" % exc}).encode()
        backend.log.info("http method=%s elapsed_ms=%d status=%d",
                         method if method in ("initialize", "tools/list", "tools/call", "ping") else "other",
                         int((time.time() - start) * 1000), status)
        self._send_bytes(status, body)


class ThreadingHTTPServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True, help="reviewed MCP server executable")
    parser.add_argument("--backend-arg", action="append", default=[])
    parser.add_argument("--cwd")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=36988)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--log-dir", default=".")
    parser.add_argument("--allow-ip", action="append", default=None,
                        help="allowed peer IP; repeat to add. Defaults to 127.0.0.1 and 10.0.2.2")
    args = parser.parse_args(argv)
    os.makedirs(args.log_dir, exist_ok=True)
    logging.basicConfig(filename=os.path.join(args.log_dir, "bridge.log"),
                        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    backend = Backend(args.command, args.backend_arg, args.cwd, args.log_dir, args.timeout)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.allow_ips = set(args.allow_ip if args.allow_ip is not None else DEFAULT_ALLOW)
    server.backend = backend
    logging.getLogger("mcp_bridge").info("bridge listening host=%s port=%d", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        # Intentionally do not terminate the MCP backend or LabVIEW on bridge shutdown.
        backend._stderr.close()


if __name__ == "__main__":
    main()
