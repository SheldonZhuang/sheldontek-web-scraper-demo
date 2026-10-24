"""Render 1600x1200 portfolio PNGs from the REAL outputs of this project.
Usage: python tools/make_portfolio_assets.py <out_dir> <pytest_output.txt>"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1600, 1200
F = "C:/Windows/Fonts/"
BG, INK, MUTED, BLUE, LINE, CARD = "#FFFFFF", "#1E2430", "#5B6475", "#2F6DB5", "#D5DCE6", "#F4F7FB"
BANNER = "DEMO project on books.toscrape.com, a public web-scraping practice site"


def font(name, size):
    return ImageFont.truetype(F + name, size)


def canvas(title, subtitle=None):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((70, 52), title, font=font("seguisb.ttf", 46), fill=INK)
    if subtitle:
        d.text((70, 118), subtitle, font=font("segoeui.ttf", 26), fill=MUTED)
    d.rectangle((0, H - 56, W, H), fill=CARD)
    d.text((70, H - 44), BANNER, font=font("segoeui.ttf", 22), fill=MUTED)
    return im, d


def box(d, xy, title, lines, accent=BLUE):
    x0, y0, x1, y1 = xy
    d.rounded_rectangle(xy, 18, fill=CARD, outline=LINE, width=2)
    d.rounded_rectangle((x0, y0, x0 + 10, y1), 5, fill=accent)
    d.text((x0 + 34, y0 + 22), title, font=font("seguisb.ttf", 30), fill=INK)
    for i, ln in enumerate(lines):
        d.text((x0 + 34, y0 + 72 + i * 34), ln, font=font("segoeui.ttf", 23), fill=MUTED)


def arrow(d, x0, y0, x1, y1):
    d.line((x0, y0, x1, y1), fill=BLUE, width=5)
    if x1 == x0:  # vertical, pointing down
        d.polygon([(x1 - 13, y1 - 18), (x1 + 13, y1 - 18), (x1, y1 + 2)], fill=BLUE)
    else:         # horizontal, pointing right
        d.polygon([(x1 - 18, y1 - 13), (x1 - 18, y1 + 13), (x1 + 2, y1)], fill=BLUE)


def pipeline(out, stats):
    im, d = canvas("Pipeline: crawl → clean → store → diff → report",
                   "Python · requests · BeautifulSoup · pandas · SQLite · matplotlib · pytest")
    bw, bh = 440, 290
    xs = [70, 580, 1090]
    row1, row2 = 200, 580
    box(d, (xs[0], row1, xs[0] + bw, row1 + bh), "1  Crawl", [
        "list pages → book pages", "≤1 request/second", "descriptive User-Agent",
        "retries + exponential backoff", "checkpoint/resume (JSONL)"])
    box(d, (xs[1], row1, xs[1] + bw, row1 + bh), "2  Clean & validate", [
        "£ price → float", "rating word → 1–5", "stock text → int",
        "de-duplicate by UPC", "count + type checks, anomalies"])
    box(d, (xs[2], row1, xs[2] + bw, row1 + bh), "3  Store", [
        "SQLite (UPC primary key)", "upsert, CHECK constraints", "CSV export",
        "Excel export", "typed columns, SQL-queryable"])
    box(d, (xs[2], row2, xs[2] + bw, row2 + bh), "4  Change detection", [
        "snapshot of last run", "diff: price / stock /", "added / removed books",
        "unit-tested on an edited copy", "(site itself is static)"])
    box(d, (xs[1], row2, xs[1] + bw, row2 + bh), "5  Report", [
        "Excel summary workbook", "counts by category", "price distribution",
        "rating vs price", "3 charts (PNG)"])
    box(d, (xs[0], row2, xs[0] + bw, row2 + bh), "Across all stages", [
        "pytest: parsers, cleaning, diff", "timestamped run log", "robots.txt checked first",
        "no CAPTCHA / WAF bypass", "no browser automation"], accent="#3D8B5A")
    arrow(d, xs[0] + bw, row1 + bh // 2, xs[1] - 4, row1 + bh // 2)
    arrow(d, xs[1] + bw, row1 + bh // 2, xs[2] - 4, row1 + bh // 2)
    arrow(d, xs[2] + bw // 2, row1 + bh, xs[2] + bw // 2, row2 - 4)
    d.line((xs[2], row2 + bh // 2, xs[1] + bw + 4, row2 + bh // 2), fill=BLUE, width=5)
    d.polygon([(xs[1] + bw + 22, row2 + bh // 2 - 13), (xs[1] + bw + 22, row2 + bh // 2 + 13),
               (xs[1] + bw + 2, row2 + bh // 2)], fill=BLUE)
    y = 940
    d.text((70, y), "Real run:", font=font("seguisb.ttf", 30), fill=INK)
    d.text((70 + d.textlength("Real run:", font=font("seguisb.ttf", 30)) + 16, y + 2), stats,
           font=font("segoeui.ttf", 28), fill=INK)
    im.save(out)


def fmt(v):
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() and abs(v) >= 1 else f"{v:.2f}" if abs(v) >= 1 or v == 0 else f"{v:.3f}"
    return v


def table(d, x, y, cols, rows, widths, size=22, rh=44, head_fill="#E3EBF6", mono=False):
    f = font("consola.ttf" if mono else "segoeui.ttf", size)
    fb = font("seguisb.ttf", size)
    cx = x
    for c, w in zip(cols, widths):
        d.rectangle((cx, y, cx + w, y + rh), fill=head_fill, outline=LINE)
        d.text((cx + 12, y + 9), c, font=fb, fill=INK)
        cx += w
    for i, r in enumerate(rows):
        cx, yy = x, y + rh * (i + 1)
        for v, w in zip(r, widths):
            d.rectangle((cx, yy, cx + w, yy + rh), fill=BG if i % 2 == 0 else "#FAFBFD", outline=LINE)
            s = str(fmt(v))
            while d.textlength(s, font=f) > w - 22 and len(s) > 3:
                s = s[:-2].rstrip() + "…" if not s.endswith("…") else s[:-2] + "…"
            d.text((cx + 12, yy + 9), s, font=f, fill=INK)
            cx += w
    return y + rh * (len(rows) + 1)


def before_after(out, raw, clean):
    im, d = canvas("Before → after: raw page text to a typed table",
                   "Same 6 books, first rows of the real crawl")
    sample = raw.head(6)
    d.text((70, 180), "BEFORE  · strings as scraped from the HTML", font=font("seguisb.ttf", 26), fill="#A04A2A")
    yb = table(d, 70, 225, ["title", "price_raw", "availability_raw", "rating_raw"],
               sample[["title", "price_raw", "availability_raw", "rating_raw"]].values.tolist(),
               [520, 200, 470, 270], mono=True)
    d.text((70, yb + 20), 'e.g. <p class="star-rating Three">  ·  <p class="price_color">£51.77</p>',
           font=font("consola.ttf", 21), fill=MUTED)
    arrow(d, W // 2, yb + 70, W // 2, yb + 130)
    d.text((W // 2 + 24, yb + 78), "parse · validate · de-duplicate by UPC", font=font("segoeui.ttf", 23), fill=MUTED)
    ya = yb + 150
    d.text((70, ya), "AFTER  · typed columns (float / int / int)", font=font("seguisb.ttf", 26), fill="#2D7A4B")
    c = clean.set_index("url").loc[sample["url"]].reset_index()
    rows = [[r.upc, r.title, r.category, f"{r.price_gbp:.2f}", r.stock, r.rating] for r in c.itertuples()]
    table(d, 70, ya + 45, ["upc", "title", "category", "price_gbp", "stock", "rating"], rows,
          [260, 470, 270, 170, 130, 160])
    im.save(out)


def chart(out, df):
    plt.rcParams.update({"font.size": 15, "axes.spines.top": False, "axes.spines.right": False})
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(16, 12), dpi=100, gridspec_kw={"height_ratios": [1.15, 1]})
    cat = df["category"].value_counts().head(10).iloc[::-1]
    a1.barh(cat.index, cat.values, color=BLUE)
    for yv, v in enumerate(cat.values):
        a1.text(v + 1, yv, str(v), va="center", fontsize=13)
    a1.set_title(f"Books per category, top 10 of {df['category'].nunique()}"
                 "", loc="left", fontsize=19)
    a1.set_xlabel("Books")
    a2.hist(df["price_gbp"], bins=20, color=BLUE, edgecolor="white")
    med = df["price_gbp"].median()
    a2.axvline(med, color="#C0392B", ls="--", lw=2)
    a2.legend([f"median £{med:.2f}"], loc="upper right", bbox_to_anchor=(1, 1.12), frameon=False, fontsize=14)
    a2.set_title(f"Price distribution, {len(df)} books (£{df.price_gbp.min():.2f} – £{df.price_gbp.max():.2f})",
                 loc="left", fontsize=19)
    a2.set_xlabel("Price (GBP)"); a2.set_ylabel("Books")
    fig.text(0.043, 0.012, BANNER + "  ·  prices are random  ·  'Default' and 'Add a comment' are the site's own categories", fontsize=12, color=MUTED)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(out); plt.close(fig)


def mono_block(d, x, y, lines, size=19, width_chars=128, color=INK):
    f = font("consola.ttf", size)
    for ln in lines:
        while True:
            d.text((x, y), ln[:width_chars], font=f, fill=color)
            y += size + 7
            ln = ln[width_chars:]
            if not ln:
                break
            ln = "    " + ln
    return y


def log_and_tests(out, pytest_txt, log_lines):
    im, d = canvas("Tests and run log (real output)")
    pytest_txt = [ln for ln in pytest_txt if ln.strip() and not ln.startswith(("platform", "rootdir", "plugins", "collecting"))]
    d.text((70, 138), "$ python -m pytest -v", font=font("seguisb.ttf", 24), fill=INK)
    d.rounded_rectangle((60, 176, W - 60, 718), 12, fill="#14181F")
    mono_block(d, 84, 190, pytest_txt, size=16, width_chars=150, color="#D8E1EC")
    d.text((70, 738), "$ python run.py   (logs/run_*.log, start and end of the full crawl)", font=font("seguisb.ttf", 24), fill=INK)
    d.rounded_rectangle((60, 776, W - 60, H - 72), 12, fill="#14181F")
    mono_block(d, 84, 788, log_lines, size=15, width_chars=158, color="#D8E1EC")
    im.save(out)


def excel_view(out, xlsx):
    sheets = pd.read_excel(xlsx, sheet_name=None)
    im, d = canvas("Excel summary report: summary_report.xlsx",
                   "Rendered from the real workbook; sheets: " + " · ".join(sheets))
    tab_x = 70
    for i, name in enumerate(sheets):
        w = d.textlength(name, font=font("segoeui.ttf", 20)) + 36
        d.rounded_rectangle((tab_x, 168, tab_x + w, 204), 6, fill="#2D7A4B" if i == 0 else CARD, outline=LINE)
        d.text((tab_x + 18, 172), name, font=font("segoeui.ttf", 20), fill="white" if i == 0 else MUTED)
        tab_x += w + 8
    s = sheets["Summary"].copy()
    s["Value"] = [f"{v:.2f}" if "price (GBP)" in m else v for m, v in zip(s["Metric"], s["Value"])]
    d.text((70, 228), "Summary", font=font("seguisb.ttf", 26), fill=INK)
    table(d, 70, 270, ["Metric", "Value"], s.values.tolist(), [380, 180], size=21, rh=42)
    r = sheets["Rating vs price"]
    d.text((70, 730), "Rating vs price", font=font("seguisb.ttf", 26), fill=INK)
    table(d, 70, 772, list(r.columns), r.values.tolist(), [100, 100, 170, 190], size=20, rh=40)
    c = sheets["By category"].head(16)
    d.text((720, 228), f"By category (top 16 of {len(sheets['By category'])})", font=font("seguisb.ttf", 26), fill=INK)
    table(d, 720, 270, list(c.columns), c.values.tolist(), [240, 90, 175, 135, 160], size=19, rh=46)
    im.save(out)


def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    pytest_txt = Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
    raw = pd.read_json(ROOT / "data/raw_books.jsonl", lines=True, dtype={"upc": str}, convert_dates=False)
    clean = pd.read_csv(ROOT / "output/books.csv", dtype={"upc": str})
    logf = max(f for f in (ROOT / "logs").glob("run_*.log") if "scraper: done" in f.read_text(encoding="utf-8"))
    log_lines = [ln.split(" ", 1)[1] if ln[:4].isdigit() else ln
                 for ln in logf.read_text(encoding="utf-8").replace(str(ROOT) + "\\", ".\\").splitlines()]
    NL = chr(10)
    log_lines = [x for ln in log_lines for x in ln.replace(", 'retries'", "," + NL + "      'retries'").split(NL)]
    keep = [ln for ln in log_lines if "list page" not in ln]
    tail = log_lines[:3] + ["..."] + [ln for ln in log_lines if "list page 50" in ln] + keep[2:]
    xl = pd.read_excel(ROOT / "output/summary_report.xlsx", sheet_name="Summary").set_index("Metric")["Value"]
    pages = sum(1 for ln in log_lines if "list page" in ln)
    dupes = len(raw) - raw["upc"].nunique()
    stats = (f"{int(xl['Books'])} books · {int(xl['Categories'])} categories · {pages} list pages · "
             f"median £{xl['Median price (GBP)']:.2f} · {dupes} duplicate UPCs")
    pipeline(out / "01_pipeline.png", stats)
    before_after(out / "02_before_after.png", raw, clean)
    chart(out / "03_results_chart.png", clean)
    log_and_tests(out / "04_tests_and_run_log.png", pytest_txt, tail[:16])
    excel_view(out / "05_excel_summary.png", ROOT / "output/summary_report.xlsx")
    for p in sorted(out.glob("*.png")):
        print(p.name, Image.open(p).size)


if __name__ == "__main__":
    main()
