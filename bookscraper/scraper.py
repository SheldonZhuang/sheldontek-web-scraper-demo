"""Polite crawler for books.toscrape.com: list pages -> book pages.

- 1 request/second max, descriptive User-Agent, retries with exponential backoff
- respects robots.txt (checked at start; the site serves 404 = no rules)
- resume from checkpoint: each finished book is appended to data/raw_books.jsonl
"""
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import robotparser

import requests

from .parsers import parse_book_page, parse_list_page

BASE = "https://books.toscrape.com/"
START = BASE + "catalogue/page-1.html"
USER_AGENT = "SheldonTek-DemoScraper/1.0 (portfolio demo on a scraping-practice site; 1 req/s)"
MIN_INTERVAL = 1.0  # seconds between requests
MAX_RETRIES = 4

log = logging.getLogger("scraper")


class PoliteClient:
    def __init__(self, min_interval: float = MIN_INTERVAL):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.min_interval = min_interval
        self._last = 0.0
        self.requests_made = 0
        self.retries = 0

    def get(self, url: str) -> str:
        for attempt in range(1, MAX_RETRIES + 1):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            self.requests_made += 1
            try:
                r = self.s.get(url, timeout=20)
                if r.status_code == 200:
                    r.encoding = "utf-8"  # site is UTF-8; avoids "Â£" mojibake
                    return r.text
                if r.status_code < 500 and r.status_code != 429:
                    r.raise_for_status()
                err = f"HTTP {r.status_code}"
            except requests.RequestException as e:
                if isinstance(e, requests.HTTPError):
                    raise
                err = repr(e)
            backoff = 2 ** attempt
            self.retries += 1
            log.warning("retry %d/%d %s (%s), sleeping %ds", attempt, MAX_RETRIES, url, err, backoff)
            time.sleep(backoff)
        raise RuntimeError(f"giving up on {url}")


def robots_allows(client: PoliteClient, url: str) -> bool:
    rp = robotparser.RobotFileParser()
    r = client.s.get(BASE + "robots.txt", timeout=20)
    client.requests_made += 1
    client._last = time.monotonic()
    if r.status_code == 404:
        log.info("robots.txt: 404 (no rules published) -> all allowed")
        return True
    rp.parse(r.text.splitlines())
    ok = rp.can_fetch(USER_AGENT, url)
    log.info("robots.txt: HTTP %d, can_fetch(%s)=%s", r.status_code, url, ok)
    return ok


def load_checkpoint(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            done.add(json.loads(line)["url"])
    return done


def crawl(data_dir: Path, max_pages: int | None = None) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)
    out = data_dir / "raw_books.jsonl"
    done = load_checkpoint(out)
    client = PoliteClient()
    t0 = time.monotonic()
    log.info("start crawl; checkpoint has %d books", len(done))
    if not robots_allows(client, START):
        raise SystemExit("robots.txt disallows the catalogue; stopping")

    pages, page_url, new, skipped = 0, START, 0, 0
    with out.open("a", encoding="utf-8") as fh:
        while page_url and (max_pages is None or pages < max_pages):
            links, next_url = parse_list_page(client.get(page_url), page_url)
            pages += 1
            log.info("list page %d: %d books (%s)", pages, len(links), page_url)
            for link in links:
                if link in done:
                    skipped += 1
                    continue
                rec = parse_book_page(client.get(link), link)
                rec["scraped_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
                done.add(link)
                new += 1
            page_url = next_url  # None on the last page = site's natural end
    stats = {"list_pages": pages, "new_books": new, "resumed_skipped": skipped,
             "total_in_checkpoint": len(done), "http_requests": client.requests_made,
             "retries": client.retries, "seconds": round(time.monotonic() - t0, 1)}
    log.info("done: %s", stats)
    return stats

