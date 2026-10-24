"""SQLite storage + CSV export + snapshot-based change detection."""
import sqlite3
from pathlib import Path

import pandas as pd

SCHEMA = """CREATE TABLE IF NOT EXISTS books (
    upc TEXT PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL,
    price_gbp REAL NOT NULL, stock INTEGER NOT NULL, rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    url TEXT NOT NULL, scraped_at TEXT NOT NULL)"""


def save_sqlite(df: pd.DataFrame, db: Path) -> int:
    with sqlite3.connect(db) as con:
        con.execute(SCHEMA)
        con.executemany(
            "INSERT OR REPLACE INTO books VALUES (?,?,?,?,?,?,?,?)",
            df[["upc", "title", "category", "price_gbp", "stock", "rating", "url", "scraped_at"]]
            .itertuples(index=False, name=None))
        return con.execute("SELECT COUNT(*) FROM books").fetchone()[0]


def load_sqlite(db: Path) -> pd.DataFrame:
    with sqlite3.connect(db) as con:
        return pd.read_sql("SELECT * FROM books ORDER BY upc", con)


def diff_snapshots(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    """Rows whose price or stock changed, plus added/removed books."""
    m = old.merge(new, on="upc", how="outer", suffixes=("_old", "_new"), indicator="status")
    out = []
    for r in m.itertuples(index=False):
        title = r.title_new if isinstance(r.title_new, str) else r.title_old
        if r.status == "left_only":
            out.append({"upc": r.upc, "title": title, "change": "removed"})
            continue
        if r.status == "right_only":
            out.append({"upc": r.upc, "title": title, "change": "added"})
            continue
        if r.price_gbp_old != r.price_gbp_new:
            out.append({"upc": r.upc, "title": title, "change": "price",
                        "old": r.price_gbp_old, "new": r.price_gbp_new})
        if r.stock_old != r.stock_new:
            out.append({"upc": r.upc, "title": title, "change": "stock",
                        "old": r.stock_old, "new": r.stock_new})
    return pd.DataFrame(out, columns=["upc", "title", "change", "old", "new"])


def rotate_snapshot(df: pd.DataFrame, snap_dir: Path) -> pd.DataFrame | None:
    """Compare against data/snapshot_prev.csv (if any), then make df the new snapshot."""
    snap_dir.mkdir(parents=True, exist_ok=True)
    prev = snap_dir / "snapshot_prev.csv"
    changes = None
    if prev.exists():
        changes = diff_snapshots(pd.read_csv(prev, dtype={"upc": str}), df)
    df.to_csv(prev, index=False, encoding="utf-8")
    return changes
