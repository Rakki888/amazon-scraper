from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

from scraper.models.product import Product


def _get_text_safe(tag) -> Optional[str]:
    if not tag:
        return None
    text = tag.get_text(strip=True)
    return text or None


def parse_product_detail(html: str, url: str, category: str | None = None) -> Product:
    """
    Amazon商品詳細ページのHTMLからProductを生成する.

    レイアウト変更に弱い部分はあるが、代表的なセレクタを複数試して値を取得する。
    """
    soup = BeautifulSoup(html, "lxml")

    # 商品名（タイトル）
    name = None
    title_tag = soup.find(id="productTitle")
    if not title_tag:
        title_tag = soup.title
    name = _get_text_safe(title_tag)

    # 価格（代表的なパターンを順番に試す）
    price_raw = None
    price_candidates = [
        soup.find(id="priceblock_ourprice"),
        soup.find(id="priceblock_dealprice"),
        soup.find(id="priceblock_saleprice"),
    ]
    if not any(price_candidates):
        # data-a-color="price" を持つ要素もよく使われる
        price_candidates.append(
            soup.select_one('span.a-price span.a-offscreen')
        )

    for tag in price_candidates:
        price_raw = _get_text_safe(tag)
        if price_raw:
            break

    # 数値価格への変換（¥やカンマを取り除く）
    price_value: Optional[float] = None
    if price_raw:
        cleaned = (
            price_raw.replace("￥", "")
            .replace("¥", "")
            .replace(",", "")
            .strip()
        )
        try:
            price_value = float(cleaned)
        except ValueError:
            price_value = None

    # 在庫情報
    stock_tag = soup.find(id="availability")
    stock = None
    if stock_tag:
        stock = _get_text_safe(stock_tag)

    # レーティング（「星5つ中4.3」のようなテキスト）
    rating = None
    rating_tag = soup.find("span", id="acrPopover")
    if rating_tag and rating_tag.has_attr("title"):
        # 例: "星5つ中4.3"
        title_text = rating_tag["title"]
        # 数字部分だけを抽出
        import re

        m = re.search(r"([0-9]+(\.[0-9]+)?)", title_text)
        if m:
            try:
                rating = float(m.group(1))
            except ValueError:
                rating = None

    # レビュー数
    review_count = None
    review_tag = soup.find(id="acrCustomerReviewText")
    if review_tag:
        import re

        txt = _get_text_safe(review_tag) or ""
        # 例: "1,234個の評価"
        digits = re.sub(r"[^\d]", "", txt)
        if digits:
            try:
                review_count = int(digits)
            except ValueError:
                review_count = None

    # ASIN（hidden input やテーブルから取得を試みる）
    asin = None
    asin_input = soup.find("input", {"id": "ASIN"})
    if asin_input and asin_input.has_attr("value"):
        asin = asin_input["value"] or None
    if not asin:
        # 詳細テーブルの "ASIN" 行を探す
        detail_tables = soup.select("#productDetails_detailBullets_sections1 tr")
        for tr in detail_tables:
            header = _get_text_safe(tr.find("th"))
            value = _get_text_safe(tr.find("td"))
            if header and "ASIN" in header and value:
                asin = value
                break

    return Product(
        asin=asin,
        name=name,
        price=price_value,
        price_raw=price_raw,
        stock=stock,
        rating=rating,
        review_count=review_count,
        url=url,
        category=category,
        scraped_at=datetime.now(),
    )

