import pandas as pd
import pytest

from bookscraper.cleaning import clean, parse_price, parse_rating, parse_stock


@pytest.mark.parametrize("text,val", [("£51.77", 51.77), ("Â£10.00", 10.0), ("£1,234.50", 1234.5)],
                         ids=["gbp", "mojibake", "thousands"])
def test_parse_price(text, val):
    assert parse_price(text) == val


def test_parse_price_bad():
    with pytest.raises(ValueError):
        parse_price("free")


@pytest.mark.parametrize("w,n", [("One", 1), ("Three", 3), ("Five", 5)])
def test_parse_rating(w, n):
    assert parse_rating(w) == n


def test_parse_rating_bad():
    with pytest.raises(ValueError):
        parse_rating("Zero")


@pytest.mark.parametrize("t,n", [("In stock (22 available)", 22), ("In stock (1 available)", 1), ("Out of stock", 0)])
def test_parse_stock(t, n):
    assert parse_stock(t) == n


def test_parse_stock_bad():
    with pytest.raises(ValueError):
        parse_stock("Ask us")


def raw(upc, price="£10.00", stock="In stock (3 available)", rating="Two", url=None):
    return {"title": f"T{upc}", "price_raw": price, "availability_raw": stock, "rating_raw": rating,
            "category": "Poetry", "upc": upc, "url": url or f"u/{upc}", "scraped_at": "2026-10-24T00:00:00+00:00"}


def test_clean_types_dedupe_and_count():
    df, anomalies = clean(pd.DataFrame([raw("a"), raw("b"), raw("a", price="£11.00")]), expected=2)
    assert list(df["upc"]) == ["a", "b"]
    assert df.loc[df.upc == "a", "price_gbp"].item() == 11.0  # last copy wins
    assert str(df["price_gbp"].dtype) == "float64" and str(df["stock"].dtype) == "int64"
    assert anomalies == ["1 duplicate UPC rows removed"]


def test_clean_reports_bad_rows_and_count_mismatch():
    df, anomalies = clean(pd.DataFrame([raw("a"), raw("b", rating="Many")]), expected=1000)
    assert len(df) == 1
    assert any("unparseable row u/b" in a for a in anomalies)
    assert "row count 1 != expected 1000" in anomalies
