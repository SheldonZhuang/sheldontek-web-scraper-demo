"""TEST ONLY: books.toscrape.com is static, so a real second crawl shows 0 changes.
Here we edit a copy of a snapshot to prove the diff logic works."""
import pandas as pd

from bookscraper.storage import diff_snapshots, load_sqlite, rotate_snapshot, save_sqlite


def snap():
    return pd.DataFrame({"upc": ["a", "b", "c"], "title": ["A", "B", "C"], "category": ["X"] * 3,
                         "price_gbp": [10.0, 20.0, 30.0], "stock": [5, 6, 7], "rating": [1, 2, 3],
                         "url": ["u1", "u2", "u3"], "scraped_at": ["t"] * 3})


def test_no_changes_on_identical_snapshot():
    assert diff_snapshots(snap(), snap()).empty


def test_edited_copy_shows_price_stock_added_removed():
    new = snap()
    new.loc[new.upc == "a", "price_gbp"] = 12.5      # simulated price change
    new.loc[new.upc == "b", "stock"] = 0             # simulated sell-out
    new = new[new.upc != "c"]                        # simulated removal
    new = pd.concat([new, snap().assign(upc="d", title="D").head(1)])  # simulated new book
    d = diff_snapshots(snap(), new).set_index(["upc", "change"])
    assert set(d.index) == {("a", "price"), ("b", "stock"), ("c", "removed"), ("d", "added")}
    assert d.loc[("a", "price"), "old"] == 10.0 and d.loc[("a", "price"), "new"] == 12.5
    assert d.loc[("b", "stock"), "new"] == 0


def test_rotate_snapshot_and_sqlite_roundtrip(tmp_path):
    assert rotate_snapshot(snap(), tmp_path) is None   # first run = baseline
    edited = snap(); edited.loc[0, "price_gbp"] = 9.99
    changes = rotate_snapshot(edited, tmp_path)
    assert list(changes["change"]) == ["price"]
    assert save_sqlite(edited, tmp_path / "b.sqlite") == 3
    assert save_sqlite(edited, tmp_path / "b.sqlite") == 3  # upsert, no dupes
    assert load_sqlite(tmp_path / "b.sqlite").loc[0, "price_gbp"] == 9.99
