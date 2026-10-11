#!/usr/bin/env python3
import argparse
import csv
import re
import time
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup


DEFAULT_SELECTORS = {
    "card": "article.product, div.product, li.product-item, .product-card, .product",
    "title": "h2, h3, .product-title, .title, a.product-link, a[href*='/product/']",
    "price": ".price, .product-price, .amount, .current-price, [data-price]",
    "rating": ".rating, .stars, [class*='rating'], [aria-label*='rating']",
    "link": "a[href]",
}


def build_headers() -> Dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }


def clean_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    return text


def parse_price(value: str) -> str:
    if not value:
        return ""
    match = re.search(r"\$?\d+(?:[.,]\d{2,})?", value)
    if match:
        return match.group(0).replace(",", "")
    return value


def extract_text(node: Optional[object], selectors: List[str]) -> str:
    if node is None:
        return ""
    for selector in selectors:
        item = node.select_one(selector)
        if item is not None:
            return clean_text(item.get_text(" ", strip=True))
    return ""


def get_link(node: Optional[object], selectors: List[str]) -> str:
    if node is None:
        return ""
    for selector in selectors:
        item = node.select_one(selector)
        if item is not None and item.has_attr("href"):
            href = item.get("href")
            if href:
                return href
    return ""


def get_rating(node: Optional[object], selectors: List[str]) -> str:
    if node is None:
        return ""
    for selector in selectors:
        item = node.select_one(selector)
        if item is not None:
            text = clean_text(item.get_text(" ", strip=True))
            if text:
                return text
            aria = item.get("aria-label")
            if aria:
                return clean_text(aria)
    return ""


def parse_product(card, selectors: Dict[str, str]) -> Dict[str, str]:
    title = extract_text(card, selectors["title"].split(","))
    price = extract_text(card, selectors["price"].split(","))
    rating = get_rating(card, selectors["rating"].split(","))
    link = get_link(card, selectors["link"].split(","))

    if not title:
        title = clean_text(card.get("data-name"))

    if not title:
        title = clean_text(card.find("a").get_text(" ", strip=True)) if card.find("a") else ""

    if not price:
        price = clean_text(card.get("data-price"))

    return {
        "title": title,
        "price": parse_price(price),
        "rating": rating,
        "link": link,
    }


def build_url(base_url: str, page_number: int) -> str:
    if page_number <= 1:
        return base_url

    if "?" in base_url:
        return f"{base_url}&page={page_number}"
    return f"{base_url}?page={page_number}"


def scrape_products(url: str, max_pages: int = 1, pause_seconds: float = 2.0) -> List[Dict[str, str]]:
    products: List[Dict[str, str]] = []
    seen_titles = set()

    for page_number in range(1, max_pages + 1):
        page_url = build_url(url, page_number)
        response = requests.get(page_url, headers=build_headers(), timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select(DEFAULT_SELECTORS["card"])

        if not cards:
            print(f"No product cards found on page {page_number}: {page_url}")
            break

        for card in cards:
            product = parse_product(card, DEFAULT_SELECTORS)
            title = product.get("title", "").strip()
            if not title:
                continue
            if title in seen_titles:
                continue
            seen_titles.add(title)
            products.append(product)

        if page_number < max_pages:
            time.sleep(pause_seconds)

    return products


def write_csv(rows: List[Dict[str, str]], output_path: str) -> None:
    fieldnames = ["title", "price", "rating", "link"]

    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} entries to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape product data from an e-commerce page.")
    parser.add_argument("--url", required=True, help="URL of the product listing page to scrape.")
    parser.add_argument("--output", default="products.csv", help="CSV file to save the scraped data.")
    parser.add_argument("--max-pages", type=int, default=1, help="Number of pages to scrape.")
    parser.add_argument("--pause", type=float, default=2.0, help="Seconds to wait between page requests.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        data = scrape_products(args.url, max_pages=max(1, args.max_pages), pause_seconds=args.pause)
        write_csv(data, args.output)
    except requests.RequestException as exc:
        raise SystemExit(f"Request failed: {exc}") from exc


if __name__ == "__main__":
    main()
