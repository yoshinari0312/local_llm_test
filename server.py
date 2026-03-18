#!/usr/bin/env python3
"""
LAN向けの簡易Webサーバー + Ollamaプロキシ。

- 静的ファイル: index.html / app.js / style.css を配信
- APIプロキシ:
  - GET  /api/tags -> Ollama /api/tags
  - POST /api/chat -> Ollama /api/chat（ストリーミング透過）

環境変数:
- HOST: バインド先（既定: 0.0.0.0）
- PORT: 待受ポート（既定: 8080）
- OLLAMA_BASE_URL: Ollama URL（既定: http://127.0.0.1:11434）
"""

from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


class QuietThreadingHTTPServer(ThreadingHTTPServer):
    """接続リセット等の想定内エラーでスタックトレースを出さない。"""

    def handle_error(self, request, client_address) -> None:  # type: ignore[override]
        exc_type, _, _ = sys.exc_info()
        if exc_type and issubclass(exc_type, (ConnectionResetError, BrokenPipeError, socket.timeout)):
            return
        super().handle_error(request, client_address)


class AppHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def end_headers(self) -> None:
        # 同一オリジン利用が前提だが、LAN検証で困らないようCORSヘッダを付与
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        path = urllib.parse.urlsplit(self.path).path
        if path == "/favicon.ico":
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if path == "/api/tags":
            self._proxy_get("/api/tags")
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urllib.parse.urlsplit(self.path).path
        if path == "/api/chat":
            self._proxy_post_stream("/api/chat")
            return

        self._send_json(404, {"error": "Not Found"})

    def _proxy_get(self, upstream_path: str) -> None:
        url = f"{OLLAMA_BASE_URL}{upstream_path}"
        req = urllib.request.Request(url=url, method="GET")
        self._proxy_once(req)

    def _proxy_post_stream(self, upstream_path: str) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        url = f"{OLLAMA_BASE_URL}{upstream_path}"
        req = urllib.request.Request(
            url=url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=600) as upstream:
                self.send_response(upstream.status)
                self.send_header(
                    "Content-Type",
                    upstream.headers.get("Content-Type", "application/x-ndjson"),
                )
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()

                while True:
                    chunk = upstream.read(1024)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    except (ConnectionResetError, BrokenPipeError):
                        # クライアント切断（ページ遷移/タブクローズ等）は想定内
                        return
        except urllib.error.HTTPError as e:
            self._forward_http_error(e)
        except Exception as e:
            self._send_json(502, {"error": f"Bad Gateway: {e}"})

    def _proxy_once(self, req: urllib.request.Request) -> None:
        try:
            with urllib.request.urlopen(req, timeout=30) as upstream:
                data = upstream.read()
                self.send_response(upstream.status)
                self.send_header(
                    "Content-Type", upstream.headers.get("Content-Type", "application/json")
                )
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                try:
                    self.wfile.write(data)
                except (ConnectionResetError, BrokenPipeError):
                    return
        except urllib.error.HTTPError as e:
            self._forward_http_error(e)
        except Exception as e:
            self._send_json(502, {"error": f"Bad Gateway: {e}"})

    def _forward_http_error(self, e: urllib.error.HTTPError) -> None:
        body = e.read() if hasattr(e, "read") else b""
        self.send_response(e.code)
        self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            try:
                self.wfile.write(body)
            except (ConnectionResetError, BrokenPipeError):
                return

    def _send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (ConnectionResetError, BrokenPipeError):
            return


def main() -> None:
    # このファイルがあるディレクトリを配信ルートにする
    os.chdir(Path(__file__).resolve().parent)

    server = QuietThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"[local_llm_test] Web server: http://{HOST}:{PORT}")
    print(f"[local_llm_test] Ollama upstream: {OLLAMA_BASE_URL}")
    server.serve_forever()


if __name__ == "__main__":
    main()
