"""Turn raw page text into a typed table and report anomalies."""
import re

import pandas as pd

RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
EXPECTED_BOOKS = 1000  # the site states "1000 results"


def parse_price(text: str) -> float:
    """'£51.77' (or mojibake 'Â£51.77') -> 51.77"""
    m = re.search(r"(\d+(?:\.\d+)?)", (text or "").replace(",", ""))
    if not m:
        raise ValueError(f"bad price: {text!r}")
    return float(m.group(1))


def parse_rating(word: str) -> int:
    if word not in RATING_WORDS:
        raise ValueError(f"bad rating: {word!r}")
    return RATING_WORDS[word]


def parse_stock(text: str) -> int:
    """'In stock (22 available)' -> 22; 'Out of stock' -> 0"""
    t = (text or "").strip()
    m = re.search(r"\((\d+) available\)", t)
    if m:
        return int(m.group(1))
    if t.lower().startswith("out of stock"):
        return 0
    raise ValueError(f"bad availability: {text!r}")


def clean(raw: pd.DataFrame, expected: int = EXPECTED_BOOKS) -> tuple[pd.DataFrame, list[str]]:
    anomalies: list[str] = []
    rows = []
    for rec in raw.to_dict("records"):
        try:
            rows.append({
                "upc": rec["upc"].strip(),
                "title": rec["title"].strip(),
                "category": rec["category"].strip(),
                "price_gbp": parse_price(rec["price_raw"]),
                "stock": parse_stock(rec["availability_raw"]),
                "rating": parse_rating(rec["rating_raw"]),
                "url": rec["url"],
                "scraped_at": rec["scraped_at"],
            })
        except (ValueError, KeyError, AttributeError) as e:
            anomalies.append(f"unparseable row {rec.get('url')}: {e}")
    df = pd.DataFrame(rows, columns=["upc", "title", "category", "price_gbp", "stock",
                                     "rating", "url", "scraped_at"])
    dupes = int(df.duplicated("upc").sum())
    if dupes:
        anomalies.append(f"{dupes} duplicate UPC rows removed")
    df = df.drop_duplicates("upc", keep="last").sort_values("upc").reset_index(drop=True)

    # validation
    if (df["upc"] == "").any():
        anomalies.append(f"{int((df['upc'] == '').sum())} rows with empty UPC")
    if (df["category"] == "").any():
        anomalies.append(f"{int((df['category'] == '').sum())} rows with empty category")
    if (df["price_gbp"] <= 0).any():
        anomalies.append(f"{int((df['price_gbp'] <= 0).sum())} rows with non-positive price")
    if len(df) != expected:
        anomalies.append(f"row count {len(df)} != expected {expected}")
    df = df.astype({"price_gbp": "float64", "stock": "int64", "rating": "int64"})
    return df, anomalies
