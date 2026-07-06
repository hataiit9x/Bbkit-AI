#!/usr/bin/env python3
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned or "page"


def strip_html_text(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def render_page(
    url: str,
    timeout: int = 20,
    headless: bool = True,
    screenshot_path: str | None = None,
) -> tuple[str, str | None, dict]:
    try:
        from cloakbrowser import launch
    except Exception as exc:
        return "", f"cloakbrowser unavailable: {exc}", {}

    browser = None
    try:
        browser = launch(headless=headless)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
        html = page.content()
        title = page.title() or ""
        final_url = page.url
        if screenshot_path:
            page.screenshot(path=screenshot_path, full_page=True)
        return html, None, {"title": title, "final_url": final_url}
    except Exception as exc:
        return "", f"cloakbrowser render failed: {exc}", {}
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a page with CloakBrowser and persist the output.")
    parser.add_argument("url")
    parser.add_argument("--output-dir")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--no-screenshot", action="store_true")
    args = parser.parse_args()

    host = urlparse(args.url).hostname or "page"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd() / "output" / "browser" / f"{slugify(host)}-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    screenshot_path = None if args.no_screenshot else str(output_dir / "page.png")
    html, error, meta = render_page(
        args.url,
        timeout=args.timeout,
        headless=not args.headed,
        screenshot_path=screenshot_path,
    )
    if error:
        print(error)
        return 1

    (output_dir / "page.html").write_text(html, encoding="utf-8")
    (output_dir / "page.txt").write_text(strip_html_text(html), encoding="utf-8")
    (output_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Workspace: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
