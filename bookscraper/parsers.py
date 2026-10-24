"""HTML parsers. They return raw text exactly as shown on the page; cleaning.py does the typing."""
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def parse_list_page(html: str, page_url: str) -> tuple[list[str], str | None]:
    """Return (absolute book URLs, absolute next-page URL or None)."""
    soup = BeautifulSoup(html, "html.parser")
    links = [urljoin(page_url, a["href"]) for a in soup.select("article.product_pod h3 a[href]")]
    nxt = soup.select_one("ul.pager li.next a[href]")
    return links, (urljoin(page_url, nxt["href"]) if nxt else None)


def parse_book_page(html: str, url: str) -> dict:
    """Extract raw fields from one book page."""
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("div.product_main")
    if main is None:
        raise ValueError(f"not a book page: {url}")
    rating_el = main.select_one("p.star-rating")
    rating_raw = next((c for c in rating_el.get("class", []) if c != "star-rating"), "") if rating_el else ""
    crumbs = soup.select("ul.breadcrumb li a")
    table = {th.get_text(strip=True): td.get_text(strip=True)
             for th, td in ((tr.th, tr.td) for tr in soup.select("table.table tr")) if th and td}
    return {
        "title": main.h1.get_text(strip=True) if main.h1 else "",
        "price_raw": main.select_one("p.price_color").get_text(strip=True) if main.select_one("p.price_color") else "",
        "availability_raw": " ".join(main.select_one("p.availability").get_text().split()) if main.select_one("p.availability") else "",
        "rating_raw": rating_raw,
        "category": crumbs[-1].get_text(strip=True) if len(crumbs) >= 3 else "",
        "upc": table.get("UPC", ""),
        "url": url,
    }
