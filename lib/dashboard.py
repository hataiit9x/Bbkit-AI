#!/usr/bin/env python3
"""BBKit lightweight dashboard — list recon reports + engagements (stdlib only)."""

from __future__ import annotations

import html
import json
import os
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

BB_ROOT = Path(os.environ.get("BB_ROOT", Path.home() / "BugBounty")).expanduser()
OUTPUT = Path(os.environ.get("BB_OUTPUT", BB_ROOT / "output")).expanduser()
ENGAGEMENTS = Path(os.environ.get("BB_ENGAGEMENTS", BB_ROOT / "engagements")).expanduser()
HOST = os.environ.get("BB_DASH_HOST", "127.0.0.1")
PORT = int(os.environ.get("BB_DASH_PORT", "8787"))


def count_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def list_targets() -> list[dict]:
    rows = []
    if not OUTPUT.is_dir():
        return rows
    for d in sorted(OUTPUT.iterdir(), key=lambda p: p.name.lower()):
        if not d.is_dir():
            continue
        report = d / "report.html"
        rows.append(
            {
                "name": d.name,
                "path": str(d),
                "has_report": report.is_file(),
                "report_url": f"/output/{d.name}/report.html" if report.is_file() else "",
                "subs": count_lines(d / "subs" / "resolved.txt"),
                "alive": count_lines(d / "alive" / "alive.txt"),
                "urls": count_lines(d / "urls" / "all_urls.txt"),
                "nuclei": count_lines(d / "nuclei" / "nuclei.txt"),
            }
        )
    return rows


def list_engagements() -> list[dict]:
    rows = []
    if not ENGAGEMENTS.is_dir():
        return rows
    for d in sorted(ENGAGEMENTS.iterdir(), key=lambda p: p.name.lower()):
        if not d.is_dir():
            continue
        scope = d / "scope.md"
        rows.append(
            {
                "name": d.name,
                "has_scope": scope.is_file(),
                "scope_url": f"/engagements/{d.name}/scope.md" if scope.is_file() else "",
            }
        )
    return rows


def page_index() -> str:
    targets = list_targets()
    engs = list_engagements()
    t_rows = []
    for t in targets:
        link = (
            f'<a href="{html.escape(t["report_url"])}">report</a>'
            if t["has_report"]
            else "<span class='muted'>—</span>"
        )
        t_rows.append(
            "<tr>"
            f"<td><code>{html.escape(t['name'])}</code></td>"
            f"<td>{t['subs']}</td><td>{t['alive']}</td>"
            f"<td>{t['urls']}</td><td>{t['nuclei']}</td>"
            f"<td>{link}</td>"
            "</tr>"
        )
    e_rows = []
    for e in engs:
        link = (
            f'<a href="{html.escape(e["scope_url"])}">scope.md</a>'
            if e["has_scope"]
            else "<span class='muted'>—</span>"
        )
        e_rows.append(f"<tr><td><code>{html.escape(e['name'])}</code></td><td>{link}</td></tr>")

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BBKit Dashboard</title>
<style>
:root {{ --bg:#0f1419; --card:#1a2332; --text:#e7ecf3; --muted:#8b9bb4; --accent:#3d8bfd; }}
body{{font-family:system-ui,sans-serif;margin:0;padding:28px;background:var(--bg);color:var(--text)}}
h1{{margin:0 0 6px}} .meta{{color:var(--muted);margin-bottom:22px}}
.card{{background:var(--card);border-radius:12px;padding:18px;margin-bottom:18px;border:1px solid #2a3548}}
table{{width:100%;border-collapse:collapse}} th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid #2a3548}}
th{{color:var(--muted);font-size:.85rem}} a{{color:var(--accent)}} code{{background:#0c1017;padding:2px 6px;border-radius:4px}}
.muted{{color:var(--muted)}}
</style></head><body>
<h1>BBKit Dashboard</h1>
<p class="meta">BB_ROOT=<code>{html.escape(str(BB_ROOT))}</code> · output=<code>{html.escape(str(OUTPUT))}</code></p>
<div class="card">
<h2>Recon targets ({len(targets)})</h2>
<table>
<thead><tr><th>Target</th><th>Subs</th><th>Alive</th><th>URLs</th><th>Nuclei</th><th>Report</th></tr></thead>
<tbody>
{''.join(t_rows) if t_rows else '<tr><td colspan="6" class="muted">No output yet — run bb full &lt;domain&gt;</td></tr>'}
</tbody></table>
</div>
<div class="card">
<h2>Engagements ({len(engs)})</h2>
<table>
<thead><tr><th>Slug</th><th>Scope</th></tr></thead>
<tbody>
{''.join(e_rows) if e_rows else '<tr><td colspan="2" class="muted">None — bb scope new &lt;slug&gt;</td></tr>'}
</tbody></table>
</div>
<p class="meta">API: <a href="/api/targets">/api/targets</a> · <a href="/api/engagements">/api/engagements</a> · authorized use only</p>
</body></html>"""


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print(f"[dash] {self.address_string()} {fmt % args}")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path in ("/", "/index.html"):
            body = page_index().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/targets":
            self._json(list_targets())
            return
        if path == "/api/engagements":
            self._json(list_engagements())
            return

        # Serve files under output/ and engagements/ only
        if path.startswith("/output/"):
            rel = path[len("/output/") :]
            full = (OUTPUT / rel).resolve()
            if not str(full).startswith(str(OUTPUT.resolve())):
                self.send_error(403)
                return
            return self._file(full)

        if path.startswith("/engagements/"):
            rel = path[len("/engagements/") :]
            full = (ENGAGEMENTS / rel).resolve()
            if not str(full).startswith(str(ENGAGEMENTS.resolve())):
                self.send_error(403)
                return
            return self._file(full)

        self.send_error(404)

    def _json(self, data) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, full: Path) -> None:
        if not full.is_file():
            self.send_error(404)
            return
        data = full.read_bytes()
        ctype = "text/plain; charset=utf-8"
        if full.suffix == ".html":
            ctype = "text/html; charset=utf-8"
        elif full.suffix == ".md":
            ctype = "text/markdown; charset=utf-8"
        elif full.suffix == ".json":
            ctype = "application/json"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    # Bind
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[+] BBKit dashboard http://{HOST}:{PORT}/")
    print(f"[+] OUTPUT={OUTPUT}")
    print(f"[+] ENGAGEMENTS={ENGAGEMENTS}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] stopped")


if __name__ == "__main__":
    main()
