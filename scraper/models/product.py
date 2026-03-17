from datetime import datetime

from pydantic import BaseModel


class Product(BaseModel):
    site: str = "amazon"
    asin: str | None = None
    name: str | None = None
    price: float | None = None
    price_raw: str | None = None
    stock: str | None = None
    rating: float | None = None
    review_count: int | None = None
    url: str | None = None
    category: str | None = None
    scraped_at: datetime

