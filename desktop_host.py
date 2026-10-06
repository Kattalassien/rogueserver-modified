#!/usr/bin/env python3
"""Enhanced desktop control panel for hosting the local rogueserver stack.

The control panel intentionally uses only Python's standard library. It keeps
the dashboard alive even when Docker/Go or the database is unavailable, and
records all launch and request errors in host.log.

Features:
- Multi-window GUI with dashboard, live editor, mod manager, and settings
- Modular game configuration system (variables, catch counts, etc)
- Real-time modification of game settings
- Mod/hack/script manager interface
- Comprehensive error logging and recovery
- Support for iPhone access via LAN
"""

from __future__ import annotations

import configparser
import html
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
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("ROGUE_HOST_CONFIG", ROOT / "host.ini"))
VARIABLES_PATH = Path(os.environ.get("ROGUE_HOST_VARIABLES", ROOT / "game_variables.json"))
MODS_PATH = Path(os.environ.get("ROGUE_HOST_MODS", ROOT / "mods.json"))
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

DEFAULT_VARIABLES = {
    "pokemonCatchLimit": 999,
    "maxLevel": 100,
    "difficultyMultiplier": 1.0,
    "experienceMultiplier": 1.0,
    "enableRandomEvents": True,
    "enableTrainerScaling": True,
    "allowSwitching": True,
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


def load_variables() -> dict:
    """Load game variables from JSON file."""
    if VARIABLES_PATH.exists():
        try:
            with VARIABLES_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning("failed to load variables: %s", e)
    return DEFAULT_VARIABLES.copy()


def save_variables(variables: dict) -> None:
    """Save game variables to JSON file."""
    try:
        with VARIABLES_PATH.open("w", encoding="utf-8") as f:
            json.dump(variables, f, indent=2)
        log.info("saved game variables")
    except Exception as e:
        log.error("failed to save variables: %s", e)


def load_mods() -> dict:
    """Load mods configuration from JSON file."""
    default_mods = {
        "enabled": [],
        "disabled": [],
        "userScripts": [],
        "metadata": {}
    }
    if MODS_PATH.exists():
        try:
            with MODS_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning("failed to load mods: %s", e)
    return default_mods


def save_mods(mods: dict) -> None:
    """Save mods configuration to JSON file."""
    try:
        with MODS_PATH.open("w", encoding="utf-8") as f:
            json.dump(mods, f, indent=2)
        log.info("saved mods configuration")
    except Exception as e:
        log.error("failed to save mods: %s", e)



class HostState:
    def __init__(self) -> None:
        self.config = load_config()
        self.variables = load_variables()
        self.mods = load_mods()
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
                "editor_url": f"http://{self.public_host()}:{self.values['dashboard_port']}/editor",
                "variables_url": f"http://{self.public_host()}:{self.values['dashboard_port']}/variables",
                "mods_url": f"http://{self.public_host()}:{self.values['dashboard_port']}/mods",
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

    def update_variables(self, variables: dict) -> None:
        """Update and persist game variables."""
        with self.lock:
            self.variables.update(variables)
            save_variables(self.variables)
            log.info("updated game variables: %s", list(variables.keys()))

    def update_mods(self, mods: dict) -> None:
        """Update and persist mods configuration."""
        with self.lock:
            self.mods.update(mods)
            save_mods(self.mods)
            log.info("updated mods configuration")


def page(title: str, body: str) -> bytes:
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width">
<title>{title}</title><style>
body{{font:16px system-ui;max-width:900px;margin:2em auto;padding:0 1em}}
nav{{margin-bottom:2em}}nav a{{display:inline-block;padding:.5em 1em;margin-right:.5em;background:#f0f0f0;text-decoration:none;border-radius:4px}}
nav a:hover{{background:#e0e0e0}}
.section{{margin:2em 0}}
pre{{background:#f4f4f4;padding:1em;overflow:auto;border-radius:4px}}
input{{width:100%;padding:.5em;margin:.25em 0 1em;border:1px solid #ccc;border-radius:4px}}
input[type="checkbox"]{{width:auto}}
button{{padding:.6em 1em;background:#007bff;color:white;border:none;border-radius:4px;cursor:pointer}}
button:hover{{background:#0056b3}}
.status{{padding:1em;background:#e8f5e9;border-left:4px solid #4caf50;border-radius:4px}}
.error{{padding:1em;background:#ffebee;border-left:4px solid #f44336;border-radius:4px}}
label{{display:block;margin:1em 0;padding:.5em}}
</style></head>
<body>
<nav><a href="/">Dashboard</a><a href="/editor">Config</a><a href="/variables">Variables</a><a href="/mods">Mods</a></nav>
{body}</body></html>""".encode()


class ControlHandler(BaseHTTPRequestHandler):
    state: HostState

    def log_message(self, format: str, *args: object) -> None:
        log.info("http %s", format % args)

    def send(self, payload: bytes, status: int = HTTPStatus.OK, content_type: str = "text/html") -> None:
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/status":
                self.send(json.dumps(self.state.status()).encode(), content_type="application/json")
            elif path == "/api/config":
                public = {key: value for key, value in self.state.values.items() if key != "admin_token"}
                self.send(json.dumps(public, indent=2).encode(), content_type="application/json")
            elif path == "/api/variables":
                self.send(json.dumps(self.state.variables, indent=2).encode(), content_type="application/json")
            elif path == "/api/mods":
                self.send(json.dumps(self.state.mods, indent=2).encode(), content_type="application/json")
            elif path in ("/", "/dashboard"):
                status = json.dumps(self.state.status(), indent=2)
                self.send(page("RogueServer Dashboard", f"""
<h1>RogueServer Dashboard</h1>
<div class="section status">
<h2>Server Status</h2>
<pre>{status}</pre>
</div>
<div class="section">
<p><strong>Quick Links:</strong></p>
<ul>
<li><a href="/editor">Configuration Editor</a> - Modify server settings</li>
<li><a href="/variables">Game Variables</a> - Adjust game mechanics (catch limits, difficulty, etc.)</li>
<li><a href="/mods">Mod Manager</a> - Manage mods, hacks, and user scripts</li>
</ul>
</div>
"""))
            elif path == "/editor":
                values = {key: value for key, value in self.state.values.items() if key != "admin_token"}
                fields = "".join(
                    f'<label>{html.escape(key)}<input name="{html.escape(key)}" '
                    f'value="{html.escape(value, quote=True)}"></label>'
                    for key, value in values.items()
                )
                self.send(page("Live Configuration Editor", f"""
<h1>Server Configuration</h1>
<p><em>Changes affect the next launch. Set admin_token before exposing beyond your LAN.</em></p>
<form method="post" action="/editor">{fields}
<label>Admin Token<input type="password" name="token" placeholder="Required to save"></label>
<button type="submit">Save Configuration</button>
</form>
"""))
            elif path == "/variables":
                var_fields = "".join(
                    f'<label>{html.escape(str(key))}'
                    f'<input name="var_{html.escape(str(key))}" '
                    f'value="{html.escape(str(self.state.variables[key]), quote=True)}"></label>'
                    for key in self.state.variables.keys()
                )
                self.send(page("Game Variables Editor", f"""
<h1>Game Configuration Variables</h1>
<p><em>Modify game mechanics in real-time. Requires authentication.</em></p>
<form method="post" action="/variables">{var_fields}
<label>Admin Token<input type="password" name="token" placeholder="Required to save"></label>
<button type="submit">Save Variables</button>
</form>
<pre>{json.dumps(self.state.variables, indent=2)}</pre>
"""))
            elif path == "/mods":
                enabled = "<br>".join(self.state.mods.get("enabled", []))
                disabled = "<br>".join(self.state.mods.get("disabled", []))
                user_scripts = "<br>".join(self.state.mods.get("userScripts", []))
                self.send(page("Mod Manager", f"""
<h1>Mod & Script Manager</h1>
<div class="section">
<h2>Enabled Mods</h2>
<pre>{enabled if enabled else "(none)"}</pre>
</div>
<div class="section">
<h2>Disabled Mods</h2>
<pre>{disabled if disabled else "(none)"}</pre>
</div>
<div class="section">
<h2>User Scripts (from GreasyFork)</h2>
<pre>{user_scripts if user_scripts else "(none)"}</pre>
</div>
<div class="section">
<form method="post" action="/mods">
<h3>Add Mod</h3>
<label>Mod Name<input name="mod_name" placeholder="e.g., my-mod"></label>
<label>Mod URL<input name="mod_url" placeholder="GitHub URL or local path"></label>
<select name="mod_type">
  <option value="enabled">Enable</option>
  <option value="disabled">Disable</option>
</select>
<button type="submit">Add Mod</button>
</form>
</div>
<pre>{json.dumps(self.state.mods, indent=2)}</pre>
"""))
            else:
                self.send(b"not found", HTTPStatus.NOT_FOUND, "text/plain")
        except Exception as e:
            log.exception("error handling GET %s", path)
            self.send(f"error: {e}".encode(), HTTPStatus.INTERNAL_SERVER_ERROR, "text/plain")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            from urllib.parse import unquote_plus
            fields = dict(item.split("=", 1) for item in self.rfile.read(length).decode().split("&") if "=" in item)
            fields = {unquote_plus(k): unquote_plus(v) for k, v in fields.items()}
            
            expected = self.state.values.get("admin_token", "")
            if not expected or not secrets.compare_digest(fields.get("token", ""), expected):
                self.send(b"authentication required; set admin_token", HTTPStatus.FORBIDDEN, "text/plain")
                return
            
            if path == "/editor":
                self.state.update(fields)
                self.send(page("Saved", '<p>Configuration saved. <a href="/editor">Return to editor</a></p>'))
            elif path == "/variables":
                variables = {k.replace("var_", ""): v for k, v in fields.items() if k.startswith("var_")}
                if variables:
                    self.state.update_variables(variables)
                    self.send(page("Saved", '<p>Variables saved. <a href="/variables">Return to variables</a></p>'))
                else:
                    self.send(b"no variables provided", HTTPStatus.BAD_REQUEST, "text/plain")
            elif path == "/mods":
                mod_name = fields.get("mod_name", "").strip()
                mod_url = fields.get("mod_url", "").strip()
                mod_type = fields.get("mod_type", "enabled")
                if mod_name and mod_url:
                    if mod_type not in self.state.mods:
                        self.state.mods[mod_type] = []
                    self.state.mods[mod_type].append({"name": mod_name, "url": mod_url})
                    self.state.update_mods(self.state.mods)
                    self.send(page("Mod Added", f'<p>Mod "{mod_name}" added. <a href="/mods">Return to manager</a></p>'))
                else:
                    self.send(b"mod_name and mod_url required", HTTPStatus.BAD_REQUEST, "text/plain")
            else:
                self.send(b"not found", HTTPStatus.NOT_FOUND, "text/plain")
        except Exception as e:
            log.exception("error handling POST %s", path)
            self.send(f"error: {e}".encode(), HTTPStatus.INTERNAL_SERVER_ERROR, "text/plain")


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
    root.title("RogueServer Enhanced Host")
    root.geometry("500x400")
    
    status = StringVar(value="Dashboard is available")
    ttk.Label(root, textvariable=status, wraplength=450).pack(padx=16, pady=12)

    def refresh() -> None:
        try:
            status.set(json.dumps(state.status(), indent=2))
        except Exception as e:
            log.exception("refresh failed")
            status.set(f"Error refreshing status: {e}")

    ttk.Button(root, text="Launch Server", command=state.launch).pack(fill="x", padx=16, pady=3)
    ttk.Button(root, text="Stop Server", command=state.stop).pack(fill="x", padx=16, pady=3)
    ttk.Button(root, text="Open Dashboard", command=lambda: webbrowser.open(f"http://localhost:{state.values['dashboard_port']}/")).pack(fill="x", padx=16, pady=3)
    ttk.Button(root, text="Open Configuration Editor", command=lambda: webbrowser.open(f"http://localhost:{state.values['dashboard_port']}/editor")).pack(fill="x", padx=16, pady=3)
    ttk.Button(root, text="Open Variables Editor", command=lambda: webbrowser.open(f"http://localhost:{state.values['dashboard_port']}/variables")).pack(fill="x", padx=16, pady=3)
    ttk.Button(root, text="Open Mod Manager", command=lambda: webbrowser.open(f"http://localhost:{state.values['dashboard_port']}/mods")).pack(fill="x", padx=16, pady=3)
    ttk.Button(root, text="Refresh Status", command=refresh).pack(fill="x", padx=16, pady=3)
    ttk.Button(root, text="View Log File", command=lambda: webbrowser.open(f"file://{LOG_PATH}")).pack(fill="x", padx=16, pady=3)
    
    root.protocol("WM_DELETE_WINDOW", lambda: (state.stop(), server.shutdown(), root.destroy()))
    refresh()
    root.mainloop()


def main() -> int:
    try:
        log.info("=" * 60)
        log.info("RogueServer Enhanced Host Control Panel Started")
        log.info("=" * 60)
        
        state = HostState()
        
        if "--check" in sys.argv:
            print(json.dumps(state.status(), indent=2))
            return 0
        
        server = run_server(state)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        log.info("control panel started at http://%s:%s", state.values["host"], state.values["dashboard_port"])
        log.info("game variables: %s", json.dumps(state.variables))
        log.info("mods configuration: %s", json.dumps(state.mods))
        
        state.launch()
        try:
            gui(state, server)
        except Exception:
            log.exception("GUI failed; dashboard continues until process exits")
            server.serve_forever()
        return 0
    except Exception as e:
        log.exception("fatal error in main")
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
