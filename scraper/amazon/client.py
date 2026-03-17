import asyncio
from typing import Iterable, List

import httpx


class AmazonClient:
    """Amazon向けのシンプルなHTTPクライアント."""

    def __init__(self, delay_sec: float = 2.0):
        self.delay_sec = delay_sec
        self.client = httpx.AsyncClient(timeout=20)

    async def fetch_html(self, url: str) -> str:
        """指定URLのHTMLを取得し、delayを挟む."""
        resp = await self.client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        await asyncio.sleep(self.delay_sec)
        return resp.text

    async def fetch_many(self, urls: Iterable[str]) -> List[str]:
        """複数URLのHTMLを順番に取得."""
        html_list: List[str] = []
        for url in urls:
            html_list.append(await self.fetch_html(url))
        return html_list

    async def aclose(self) -> None:
        await self.client.aclose()

