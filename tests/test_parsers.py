from pathlib import Path

import pytest

from bookscraper.parsers import parse_book_page, parse_list_page

FIX = Path(__file__).parent / "fixtures"
PAGE = "https://books.toscrape.com/catalogue/page-1.html"


def test_list_page_links_and_next():
    links, nxt = parse_list_page((FIX / "list.html").read_text(encoding="utf-8"), PAGE)
    assert links == ["https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                     "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html"]
    assert nxt == "https://books.toscrape.com/catalogue/page-2.html"


def test_last_list_page_has_no_next():
    html = '<article class="product_pod"><h3><a href="x/index.html">x</a></h3></article><ul class="pager"></ul>'
    assert parse_list_page(html, PAGE)[1] is None


def test_book_page_fields():
    rec = parse_book_page((FIX / "book.html").read_text(encoding="utf-8"), "u")
    assert rec == {"title": "A Light in the Attic", "price_raw": "£51.77",
                   "availability_raw": "In stock (22 available)", "rating_raw": "Three",
                   "category": "Poetry", "upc": "a897fe39b1053632", "url": "u"}


def test_non_book_page_raises():
    with pytest.raises(ValueError):
        parse_book_page("<html><body>404</body></html>", "u")
