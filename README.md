# Web Scraping Automation Scripts

A simple Python web scraper for extracting product information from e-commerce pages and exporting it to CSV.

## Features

- Fetch a product listing page
- Extract product titles, prices, links, and ratings when available
- Export results to CSV
- Support pagination and custom CSS selectors

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python scraper.py --url "https://example.com/products" --output products.csv --max-pages 2
```

## Notes

This project is intentionally written as a reusable template for public e-commerce pages. Some sites enforce anti-bot protections, rate limits, or use JavaScript-rendered content, so you may need to adjust selectors or use a browser automation tool for harder targets.
