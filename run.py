"""End-to-end pipeline: crawl -> clean -> store -> diff -> report.

Usage:  python run.py              # full crawl (resumes from data/raw_books.jsonl)
        python run.py --max-pages 2
        python run.py --skip-crawl # rebuild outputs from the checkpoint only
"""
import argparse
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from bookscraper import cleaning, report, scraper, storage

ROOT = Path(__file__).resolve().parent
DATA, OUT, LOGS = ROOT / "data", ROOT / "output", ROOT / "logs"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=None)
    ap.add_argument("--skip-crawl", action="store_true")
    a = ap.parse_args()
    LOGS.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
    logfile = LOGS / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        handlers=[logging.FileHandler(logfile, encoding="utf-8"), logging.StreamHandler()])
    log = logging.getLogger("pipeline")

    if not a.skip_crawl:
        scraper.crawl(DATA, max_pages=a.max_pages)
    raw = pd.read_json(DATA / "raw_books.jsonl", lines=True, dtype={"upc": str}, convert_dates=False)
    log.info("raw records: %d", len(raw))
    df, anomalies = cleaning.clean(raw)
    log.info("clean rows: %d; anomalies: %s", len(df), anomalies or "none")

    n = storage.save_sqlite(df, DATA / "books.sqlite")
    df.to_csv(OUT / "books.csv", index=False, encoding="utf-8-sig")
    log.info("sqlite rows: %d; csv: %s", n, OUT.joinpath("books.csv").relative_to(ROOT))

    changes = storage.rotate_snapshot(df, DATA)
    if changes is None:
        log.info("change detection: no previous snapshot; baseline saved")
    else:
        changes.to_csv(OUT / "changes.csv", index=False, encoding="utf-8-sig")
        log.info("change detection: %d changes vs previous snapshot", len(changes))

    tables = report.write_excel(df, OUT / "summary_report.xlsx", anomalies)
    for p in report.make_charts(df, tables, OUT):
        log.info("chart: %s", p.name)
    log.info("report: %s", OUT.joinpath("summary_report.xlsx").relative_to(ROOT))


if __name__ == "__main__":
    main()
