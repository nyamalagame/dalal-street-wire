#!/usr/bin/env python3
"""Fetch every RSS feed listed in index.html and write a compact snapshot.

The dashboard (index.html) reads data/feeds.json from its own address, so
browsers never have to contact the news sites or a CORS proxy themselves.
The feed list lives in one place, the FEEDS array in index.html; this
script reads the id and url of each entry from there.

Output shape:
  {
    "generated": "2026-10-18T09:30:00+00:00",
    "feeds": {
      "<feed id>": {
        "ok": true,
        "error": "",
        "items": [{"t": title, "l": link, "d": date, "s": summary, "i": image}]
      }
    }
  }
"""
import calendar
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import feedparser

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "index.html"
# Output path can be given as the first argument (the workflow writes into _site/)
OUTPUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "data" / "feeds.json"

MAX_ITEMS = 60          # newest items kept per feed
SUMMARY_CHARS = 160     # keep only a short teaser: the first sentence, at most this long
TIMEOUT = 25            # seconds per request
WORKERS = 8             # sites fetched in parallel
SAME_SITE_GAP = 1.5     # seconds between two requests to the same site
RETRY_PAUSE = 5         # seconds before retrying a reset or timed-out request
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def read_feed_list():
    text = SOURCE.read_text(encoding="utf-8")
    start = text.index("var FEEDS = [")
    end = text.index("];", start)
    feeds = re.findall(r'\{id:"([^"]+)"[^{}]*?url:"([^"]+)"\}', text[start:end])
    if not feeds:
        sys.exit("No feeds found in index.html; has the FEEDS array changed shape?")
    return feeds


SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'‘“₹(])")


def clean(value, limit=None):
    if not value:
        return ""
    value = SPACE_RE.sub(" ", html.unescape(TAG_RE.sub(" ", str(value)))).strip()
    if limit and len(value) > limit:
        value = value[: limit - 1].rsplit(" ", 1)[0] + "…"
    return value


def teaser(value):
    """First sentence of a summary, capped at SUMMARY_CHARS, so the snapshot holds
    a short pointer to each story rather than a copy of the publisher's text."""
    text = clean(value)
    if not text:
        return ""
    text = SENTENCE_END_RE.split(text, maxsplit=1)[0]
    return clean(text, SUMMARY_CHARS)


def image_for(entry):
    for key in ("media_content", "media_thumbnail"):
        for media in entry.get(key) or []:
            url = media.get("url")
            if url and url.startswith("http"):
                return url
    for link in entry.get("links") or []:
        if link.get("rel") == "enclosure" and "image" in (link.get("type") or "image"):
            href = link.get("href")
            if href and href.startswith("http"):
                return href
    return ""


def date_for(entry):
    # Prefer a parsed timestamp (always UTC); otherwise pass the raw string through
    # so the page can read formats feedparser doesn't know, such as NSE's
    # "17-Oct-2026 00:41:51" (IST).
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc).isoformat()
    for key in ("published", "updated", "dc_date", "date"):
        if entry.get(key):
            return str(entry[key]).strip()
    return ""


def download(url):
    """GET the URL, retrying once after a pause on connection resets and timeouts."""
    for attempt in (1, 2):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except urllib.error.HTTPError:
            raise  # a 403 or 404 won't change on retry
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 2:
                raise
            time.sleep(RETRY_PAUSE)


def describe_empty(body, content_type, parsed):
    """Explain why a response had no items, e.g. an empty feed or an HTML block page."""
    start = body[:300].decode("utf-8", "replace").strip().lower()
    if "html" in content_type.lower() or start.startswith("<!doctype html") or start.startswith("<html"):
        return f"Site returned a web page, not a feed (likely blocked) [{content_type or 'no content type'}]"
    if parsed.get("feed", {}).get("title") is not None or "<channel" in start or "<rss" in start:
        return "Feed is valid but currently has no items"
    reason = str(getattr(parsed, "bozo_exception", "")) or "Feed returned no items"
    return f"{reason} [{content_type or 'no content type'}, {len(body)} bytes]"


def fetch(feed):
    feed_id, url = feed
    try:
        body, content_type = download(url)
        parsed = feedparser.parse(body)
        items = []
        for entry in parsed.entries[:MAX_ITEMS]:
            title = clean(entry.get("title"))
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue
            items.append({
                "t": title,
                "l": link,
                "d": date_for(entry),
                "s": teaser(entry.get("summary") or entry.get("description")),
                "i": image_for(entry),
            })
        if not items:
            return feed_id, {"ok": False, "error": describe_empty(body, content_type, parsed)[:200], "items": []}
        return feed_id, {"ok": True, "error": "", "items": items}
    except Exception as exc:  # network errors, HTTP errors, bad payloads
        return feed_id, {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:200], "items": []}


def fetch_site(site_feeds):
    """Fetch one site's feeds one after another, with a short gap between them.

    Several sites (Economic Times, for one) reset connections when many
    requests arrive from the same machine at once.
    """
    results = []
    for index, feed in enumerate(site_feeds):
        if index:
            time.sleep(SAME_SITE_GAP)
        results.append(fetch(feed))
    return results


def main():
    feeds = read_feed_list()
    by_site = {}
    for feed in feeds:
        by_site.setdefault(urllib.parse.urlsplit(feed[1]).hostname, []).append(feed)
    results = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for site_results in pool.map(fetch_site, by_site.values()):
            results.update(site_results)
    results = {feed_id: results[feed_id] for feed_id, _ in feeds}  # keep page order

    snapshot = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "feeds": results,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    ok = sum(1 for r in results.values() if r["ok"])
    print(f"{ok}/{len(feeds)} feeds fetched; wrote {OUTPUT} "
          f"({OUTPUT.stat().st_size // 1024} KB)")
    for feed_id, result in sorted(results.items()):
        if not result["ok"]:
            print(f"  FAILED {feed_id}: {result['error']}")


if __name__ == "__main__":
    main()
