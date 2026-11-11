#!/usr/bin/env python3
"""Generate crawler-readable Open Graph HTML for each publicly visible ぜんにゅー article."""
from __future__ import annotations

import html
import json
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = "https://zen.nyu-net.jp"
TARGET = ROOT / "story"
PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
CONFIG = (ROOT / "config.js").read_text(encoding="utf-8")


def config_value(key: str) -> str:
    match = re.search(r"\b" + re.escape(key) + r"\s*:\s*['\"]([^'\"]+)['\"]", CONFIG)
    if not match:
        raise RuntimeError(f"Cannot find {key} in public config.js")
    return match.group(1)


def load_articles() -> list[dict]:
    url = config_value("supabaseUrl").rstrip("/") + "/rest/v1/nyu_public_articles"
    key = config_value("publishableKey")
    rows = []
    for offset in range(0, 100000, 500):
        params = urllib.parse.urlencode({
            "select": "public_id,title,summary,image_url,published_at",
            "brand_slug": "eq.zen",
            "order": "published_at.desc.nullslast",
            "limit": "500",
            "offset": str(offset),
        })
        req = urllib.request.Request(url + "?" + params, headers={
            "apikey": key,
            "Accept": "application/json",
            "User-Agent": "NYU-Network-OpenGraph-Builder/1.0",
        })
        with urllib.request.urlopen(req, timeout=25) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected Supabase response format")
        rows.extend(batch)
        if len(batch) < 500:
            break
    else:
        raise RuntimeError("Refusing to generate an unbounded number of pages")
    if not rows:
        raise RuntimeError("No published articles received; keep existing OGP pages")
    return rows


def clean_text(value, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def attr(value) -> str:
    return html.escape(str(value), quote=True)


def image_url_for(row: dict) -> tuple[str, bool]:
    original = str(row.get("image_url") or "").strip()
    url = urllib.parse.urlsplit(original)
    if url.scheme == "https" and url.hostname and not url.username and not url.password:
        return original, False
    return SITE + "/og-default.png", True


def make_html(template: str, row: dict) -> tuple[str, str]:
    public_id = str(row.get("public_id") or "")
    if not PUBLIC_ID_RE.fullmatch(public_id):
        raise RuntimeError("Unexpected public_id in published article response")
    title = clean_text(row.get("title"), 210)
    summary = clean_text(row.get("summary"), 210)
    if not title:
        raise RuntimeError("Published article missing a title")
    if not summary:
        summary = "ぜんにゅーは、世の中の「ちょっと良くなった」を集めています。"
    url = SITE + "/story/" + urllib.parse.quote(public_id, safe="") + "/"
    img, fallback = image_url_for(row)
    meta = [
        f'<meta name="nyu-public-id" content="{attr(public_id)}">',
        f'<meta name="description" content="{attr(summary)}">',
        '<meta name="robots" content="index,follow">',
        f'<link rel="canonical" href="{attr(url)}">',
        '<meta property="og:type" content="article">',
        '<meta property="og:site_name" content="ぜんにゅー">',
        '<meta property="og:locale" content="ja_JP">',
        f'<meta property="og:url" content="{attr(url)}">',
        f'<meta property="og:title" content="{attr(title)}｜ぜんにゅー">',
        f'<meta property="og:description" content="{attr(summary)}">',
        f'<meta property="og:image" content="{attr(img)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{attr(title)}｜ぜんにゅー">',
        f'<meta name="twitter:description" content="{attr(summary)}">',
        f'<meta name="twitter:image" content="{attr(img)}">',
    ]
    if fallback:
        meta.extend([
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
        ])
    published_at = str(row.get("published_at") or "").strip()
    if published_at:
        try:
            stamp = datetime.fromisoformat(published_at.replace("Z", "+00:00")).isoformat()
            meta.append(f'<meta property="article:published_time" content="{attr(stamp)}">')
        except ValueError:
            pass

    # Remove generic article.html tags to avoid conflicting social metadata.
    doc = "".join(
        line for line in template.splitlines(keepends=True)
        if "data-ogp-generic" not in line
        and '<meta name="description"' not in line
    )
    charset = '<meta charset="utf-8">'
    marker = "<title>記事｜ぜんにゅー</title>"
    if charset not in doc or marker not in doc:
        raise RuntimeError("article.html is missing expected insertion markers")
    doc = doc.replace(charset, charset + '\n<base href="' + SITE + '/">', 1)
    doc = doc.replace(marker, '<title>' + attr(title) + '｜ぜんにゅー</title>\n' + '\n'.join(meta), 1)
    return public_id, doc


def main() -> None:
    template = (ROOT / "article.html").read_text(encoding="utf-8")
    rows = load_articles()
    prepared: dict[str, str] = {}
    for row in rows:
        public_id, page = make_html(template, row)
        if public_id in prepared:
            raise RuntimeError("Duplicate public_id in public article feed")
        prepared[public_id] = page

    # Pages removed from the public view are also removed on the next successful sync.
    if TARGET.exists():
        shutil.rmtree(TARGET)
    for public_id, page in prepared.items():
        directory = TARGET / public_id
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(page, encoding="utf-8")
    print(f"Generated {len(prepared)} public article Open Graph pages")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"OGP generation failed: {exc}", file=sys.stderr)
        sys.exit(1)
