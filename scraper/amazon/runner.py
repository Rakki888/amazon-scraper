import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from scraper.amazon.client import AmazonClient
from scraper.amazon.parser import parse_product_detail
from scraper.models.product import Product


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "amazon"
DATA_DIR.mkdir(parents=True, exist_ok=True)


SEARCH_KEYWORDS: list[str] = ["シャンプー", "洗濯洗剤", "ノートPC"]
MAX_ITEMS_PER_KEYWORD = 5  # 1キーワードあたりの最大取得件数（必要に応じて調整）


async def _fetch_search_result_urls(
    client: AmazonClient, keyword: str, max_items: int
) -> list[str]:
    """
    検索キーワードからAmazonの一覧ページを1ページ取得し、商品詳細URLを抽出する。
    """
    encoded = quote_plus(keyword)
    search_url = f"https://www.amazon.co.jp/s?k={encoded}"
    html = await client.fetch_html(search_url)
    soup = BeautifulSoup(html, "lxml")

    urls: list[str] = []

    # 検索結果の商品リンクは a[href*="/dp/"] が多いのでそれを利用
    for a in soup.select("a[href*='/dp/']"):
        href = a.get("href")
        if not href:
            continue
        full_url = urljoin("https://www.amazon.co.jp", href)
        # 重複除去
        if full_url not in urls:
            urls.append(full_url)
        if len(urls) >= max_items:
            break

    return urls


async def run_amazon_scraping() -> list[Product]:
    """
    Amazonスクレイピングのメイン処理。

    1. キーワードごとに検索一覧ページを取得
    2. 一覧から商品詳細URLを抽出
    3. 各商品詳細ページをスクレイピングしてProductに変換
    """
    client = AmazonClient()
    products: list[Product] = []

    try:
        all_urls: list[tuple[str, str]] = []  # (url, keyword)
        for kw in SEARCH_KEYWORDS:
            urls = await _fetch_search_result_urls(
                client, kw, max_items=MAX_ITEMS_PER_KEYWORD
            )
            all_urls.extend((u, kw) for u in urls)

        for url, kw in all_urls:
            html = await client.fetch_html(url)
            product = parse_product_detail(html, url=url, category=kw)
            products.append(product)
    finally:
        await client.aclose()

    return products


def save_as_json(products: list[Product]) -> Path:
    """取得したProduct一覧を日付付きJSONとして保存."""
    today = datetime.now().strftime("%Y-%m-%d")
    out_path = DATA_DIR / f"{today}-products.json"
    # datetime などもJSONシリアライズ可能な形（ISO8601文字列）に変換
    data = [p.model_dump(mode="json") for p in products]
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> Path | None:
    """同期実行用エントリポイント."""
    products = asyncio.run(run_amazon_scraping())
    if not products:
        return None
    return save_as_json(products)


if __name__ == "__main__":
    main()

