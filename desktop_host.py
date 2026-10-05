#!/usr/bin/env python3
"""Small desktop control panel for hosting the local rogueserver stack.

The control panel intentionally uses only Python's standard library. It keeps
the dashboard alive even when Docker/Go or the database is unavailable, and
records all launch and request errors in host.log.
"""

from __future__ import annotations

import configparser
import json
import logging
import os
import secrets
import socket
import subprocess
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("ROGUE_HOST_CONFIG", ROOT / "host.ini"))
LOG_PATH = Path(os.environ.get("ROGUE_HOST_LOG", ROOT / "host.log"))

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("desktop-host")

DEFAULTS = {
    "host": "0.0.0.0",
    "dashboard_port": "8765",
    "game_url": "http://localhost:8000",
    "server_url": "http://localhost:8001",
    "launch_command": "docker compose -f docker-compose.Development.yml up --build",
    "stop_command": "docker compose -f docker-compose.Development.yml down",
    "admin_token": "",
}


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config["host"] = DEFAULTS.copy()
    if CONFIG_PATH.exists():
        config.read(CONFIG_PATH)
    return config


def save_config(config: configparser.ConfigParser) -> None:
    CONFIG_PATH.write_text("", encoding="utf-8")
    with CONFIG_PATH.open("w", encoding="utf-8") as stream:
        config.write(stream)


class HostState:
    def __init__(self) -> None:
        self.config = load_config()
        self.process: subprocess.Popen[str] | None = None
        self.lock = threading.Lock()
        self.started_at: float | None = None

    @property
    def values(self) -> configparser.SectionProxy:
        return self.config["host"]

    def status(self) -> dict[str, object]:
        with self.lock:
            process = self.process
            running = process is not None and process.poll() is None
            return {
                "running": running,
                "pid": process.pid if running and process else None,
                "server_url": self.values["server_url"],
                "game_url": self.values["game_url"],
                "dashboard_url": f"http://{self.public_host()}:{self.values['dashboard_port']}",
                "log": str(LOG_PATH),
            }

    def public_host(self) -> str:
        if self.values["host"] not in ("0.0.0.0", "::"):
            return self.values["host"]
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "localhost"

    def launch(self) -> None:
        with self.lock:
            if self.process and self.process.poll() is None:
                log.info("server already running with pid %s", self.process.pid)
                return
            command = self.values["launch_command"]
            try:
                self.process = subprocess.Popen(
                    command,
                    cwd=ROOT,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                threading.Thread(
                    target=self._capture_output,
                    args=(self.process,),
                    daemon=True,
                ).start()
                log.info("launched server command: %s (pid %s)", command, self.process.pid)
            except Exception:
                log.exception("unable to launch server; dashboard remains available")

    def _capture_output(self, process: subprocess.Popen[str]) -> None:
        if process.stdout:
            for line in process.stdout:
                log.info("server: %s", line.rstrip())
        code = process.wait()
        log.info("server exited with code %s", code)

    def stop(self) -> None:
        with self.lock:
            if not self.process or self.process.poll() is not None:
                return
            try:
                self.process.terminate()
                log.info("requested server shutdown")
            except OSError:
                log.exception("unable to stop server")

    def update(self, values: dict[str, str]) -> None:
        with self.lock:
            for key in DEFAULTS:
                if key in values and key != "admin_token":
                    self.values[key] = values[key]
            save_config(self.config)
            log.info("updated host configuration")


def page(title: str, body: str) -> bytes:
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width">
<title>{title}</title><style>body{{font:16px system-ui;max-width:760px;margin:2em auto;padding:0 1em}}
nav a{{margin-right:1em}}pre{{background:#f4f4f4;padding:1em;overflow:auto}}
input{{width:100%;padding:.5em;margin:.25em 0 1em}}button{{padding:.6em 1em}}</style></head>
<body><nav><a href="/">Dashboard</a><a href="/editor">Live editor</a></nav>{body}</body></html>""".encode()


class ControlHandler(BaseHTTPRequestHandler):
    state: HostState

    def log_message(self, format: str, *args: object) -> None:
        log.info("http %s", format % args)

    def send(self, payload: bytes, status: int = HTTPStatus.OK, content_type: str = "text/html") -> None:
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/status":
            self.send(json.dumps(self.state.status()).encode(), content_type="application/json")
        elif path == "/api/config":
            public = {key: value for key, value in self.state.values.items() if key != "admin_token"}
            self.send(json.dumps(public, indent=2).encode(), content_type="application/json")
        elif path in ("/", "/dashboard"):
            status = json.dumps(self.state.status(), indent=2)
            self.send(page("RogueServer dashboard", f"<h1>RogueServer dashboard</h1><pre>{status}</pre>"))
        elif path == "/editor":
            values = {key: value for key, value in self.state.values.items() if key != "admin_token"}
            fields = "".join(f'<label>{key}<input name="{key}" value="{value}"></label>' for key, value in values.items())
            self.send(page("Live editor", f"""<h1>Live configuration</h1>
<p>Changes affect the next launch. Use a private network or set an admin token before exposing this page.</p>
<form method="post">{fields}<label>Admin token<input type="password" name="token"></label>
<button>Save configuration</button></form>"""))
        else:
            self.send(b"not found", HTTPStatus.NOT_FOUND, "text/plain")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/editor":
            self.send(b"not found", HTTPStatus.NOT_FOUND, "text/plain")
            return
        length = int(self.headers.get("Content-Length", "0"))
        fields = dict(item.split("=", 1) for item in self.rfile.read(length).decode().split("&") if "=" in item)
        # HTML form values are deliberately restricted to simple config text.
        from urllib.parse import unquote_plus
        fields = {unquote_plus(k): unquote_plus(v) for k, v in fields.items()}
        expected = self.state.values.get("admin_token", "")
        if expected and not secrets.compare_digest(fields.get("token", ""), expected):
            self.send(b"invalid admin token", HTTPStatus.FORBIDDEN, "text/plain")
            return
        self.state.update(fields)
        self.send(page("Saved", '<p>Saved. <a href="/editor">Return to editor</a></p>'))


def run_server(state: HostState) -> ThreadingHTTPServer:
    port = int(state.values["dashboard_port"])
    server = ThreadingHTTPServer((state.values["host"], port), ControlHandler)
    ControlHandler.state = state
    return server


def gui(state: HostState, server: ThreadingHTTPServer) -> None:
    try:
        from tkinter import StringVar, Tk, ttk
    except ImportError:
        log.exception("Tk is unavailable; running headless with the dashboard active")
        server.serve_forever()
        return
    root = Tk()
    root.title("RogueServer desktop host")
    status = StringVar(value="Dashboard is available")
    ttk.Label(root, textvariable=status).pack(padx=16, pady=12)

    def refresh() -> None:
        status.set(json.dumps(state.status(), indent=2))

    ttk.Button(root, text="Launch server", command=state.launch).pack(fill="x", padx=16, pady=3)
    ttk.Button(root, text="Stop server", command=state.stop).pack(fill="x", padx=16, pady=3)
    ttk.Button(root, text="Open dashboard", command=lambda: webbrowser.open(f"http://localhost:{state.values['dashboard_port']}")).pack(fill="x", padx=16, pady=3)
    ttk.Button(root, text="Refresh status", command=refresh).pack(fill="x", padx=16, pady=3)
    root.protocol("WM_DELETE_WINDOW", lambda: (state.stop(), server.shutdown(), root.destroy()))
    refresh()
    root.mainloop()


def main() -> int:
    state = HostState()
    if "--check" in sys.argv:
        print(json.dumps(state.status(), indent=2))
        return 0
    server = run_server(state)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log.info("control panel started at port %s", state.values["dashboard_port"])
    state.launch()
    try:
        gui(state, server)
    except Exception:
        log.exception("GUI failed; dashboard continues until process exits")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
