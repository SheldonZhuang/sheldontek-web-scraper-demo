"""Excel summary report and charts."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BLUE = "#2F6DB5"


def summary_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    overview = pd.DataFrame([
        ("Books", int(len(df))), ("Categories", int(df["category"].nunique())),
        ("Min price (GBP)", round(df["price_gbp"].min(), 2)),
        ("Median price (GBP)", round(df["price_gbp"].median(), 2)),
        ("Mean price (GBP)", round(df["price_gbp"].mean(), 2)),
        ("Max price (GBP)", round(df["price_gbp"].max(), 2)),
        ("Total units in stock", int(df["stock"].sum())),
        ("Mean rating (1-5)", round(df["rating"].mean(), 2)),
        ("Price-rating correlation", round(df["price_gbp"].corr(df["rating"]), 3)),
    ], columns=["Metric", "Value"], dtype=object)  # object keeps ints as ints in Excel
    by_cat = (df.groupby("category").agg(books=("upc", "count"), avg_price_gbp=("price_gbp", "mean"),
                                         avg_rating=("rating", "mean"), units_in_stock=("stock", "sum"))
              .round(2).sort_values("books", ascending=False).reset_index())
    bins = [0, 20, 30, 40, 50, 60]
    price_dist = (pd.cut(df["price_gbp"], bins=bins, right=False).value_counts().sort_index()
                  .rename_axis("price_band_gbp").reset_index(name="books"))
    price_dist["price_band_gbp"] = price_dist["price_band_gbp"].astype(str)
    by_rating = (df.groupby("rating").agg(books=("upc", "count"), avg_price_gbp=("price_gbp", "mean"),
                                          median_price_gbp=("price_gbp", "median"))
                 .round(2).reset_index())
    return {"Summary": overview, "By category": by_cat, "Price distribution": price_dist,
            "Rating vs price": by_rating}


def write_excel(df: pd.DataFrame, path: Path, anomalies: list[str]) -> dict[str, pd.DataFrame]:
    tables = summary_tables(df)
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for name, t in tables.items():
            t.to_excel(xw, sheet_name=name, index=False)
        pd.DataFrame({"anomaly": anomalies or ["none"]}).to_excel(xw, sheet_name="Anomalies", index=False)
        df.to_excel(xw, sheet_name="Books", index=False)
        for ws in xw.book.worksheets:
            for col in ws.columns:
                width = max(len(str(c.value)) if c.value is not None else 0 for c in col[:200])
                ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 60)
            ws.freeze_panes = "A2"
    return tables


def make_charts(df: pd.DataFrame, tables: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False})
    paths = []

    top = tables["By category"].head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh(top["category"], top["books"], color=BLUE)
    for y, v in enumerate(top["books"]):
        ax.text(v + 1, y, str(v), va="center", fontsize=11)
    ax.set_title("Books per category (top 12 of %d)" % len(tables["By category"]), loc="left")
    ax.set_xlabel("Books")
    paths.append(out_dir / "chart_books_by_category.png")

    fig2, ax2 = plt.subplots(figsize=(10, 6.5))
    ax2.hist(df["price_gbp"], bins=20, color=BLUE, edgecolor="white")
    ax2.axvline(df["price_gbp"].median(), color="#333", ls="--", lw=1.2)
    ax2.text(df["price_gbp"].median() + 0.5, ax2.get_ylim()[1] * 0.92,
             f"median £{df['price_gbp'].median():.2f}", fontsize=11)
    ax2.set_title(f"Price distribution ({len(df)} books)", loc="left")
    ax2.set_xlabel("Price (GBP)"); ax2.set_ylabel("Books")
    paths.append(out_dir / "chart_price_distribution.png")

    fig3, ax3 = plt.subplots(figsize=(10, 6.5))
    data = [df.loc[df["rating"] == r, "price_gbp"] for r in range(1, 6)]
    ax3.boxplot(data, tick_labels=[f"{r}★\n(n={len(d)})" for r, d in zip(range(1, 6), data)],
                patch_artist=True, boxprops={"facecolor": "#CFE0F5"}, medianprops={"color": BLUE, "lw": 2})
    ax3.set_title("Price by star rating (corr = %.3f)" % df["price_gbp"].corr(df["rating"]), loc="left")
    ax3.set_ylabel("Price (GBP)")
    paths.append(out_dir / "chart_rating_vs_price.png")

    for f, p in zip((fig, fig2, fig3), paths):
        f.tight_layout(); f.savefig(p, dpi=150); plt.close(f)
    return paths
