from ebook_manager.plugins import BasePlugin, ISource
from typing import List, Optional, Dict, Any


class NationalLibrarySource(BasePlugin, ISource):
    """国家图书馆元数据来源插件示例"""

    plugin_id = "national_library"
    plugin_name = "国家图书馆"
    version = "0.1.0"
    author = "开发者名称"
    author_email = "dev@example.com"
    description = "国家图书馆书籍元数据查询插件"
    dependencies = []
    allowed_domains = ["nlc.cn"]
    plugin_type = "source"

    SEARCH_URL = "https://opac.nlc.cn/F"

    @property
    def source_id(self) -> str:
        return self.plugin_id

    @property
    def source_name(self) -> str:
        return self.plugin_name

    @property
    def source_url(self) -> str:
        return "https://www.nlc.cn"

    def search_by_title(self, title: str, max_results: int = 5) -> List[Dict[str, Any]]:
        try:
            if not self._sandbox:
                return []

            results = []
            for i in range(min(max_results, 3)):
                results.append({
                    "title": f"{title} (国家图书馆示例{i+1})",
                    "author": "示例作者",
                    "publisher": "国家图书馆出版社",
                    "publish_date": "2020",
                    "isbn": f"9787{i:010d}",
                    "source": self.source_id,
                    "cover_url": "",
                    "source_url": "",
                })
            return results
        except Exception:
            return []

    def search_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        try:
            return {
                "title": "国家图书馆示例书籍",
                "author": "示例作者",
                "publisher": "国家图书馆出版社",
                "publish_date": "2020",
                "isbn": isbn,
                "source": self.source_id,
                "cover_url": "",
            }
        except Exception:
            return None

    def parse_result(self, raw_data: Any) -> Dict[str, Any]:
        if isinstance(raw_data, dict):
            return {
                "title": raw_data.get("title", ""),
                "author": raw_data.get("author", ""),
                "publisher": raw_data.get("publisher", ""),
                "publish_date": raw_data.get("publish_date", ""),
                "isbn": raw_data.get("isbn", ""),
                "source": self.source_id,
            }
        return {}

    def get_book_detail(self, book_id: str) -> Optional[Dict[str, Any]]:
        try:
            return {
                "title": "书籍详情示例",
                "author": "示例作者",
                "publisher": "国家图书馆出版社",
                "publish_date": "2020",
                "isbn": "9787000000000",
                "description": "这是国家图书馆数据源的示例书籍详情",
                "source": self.source_id,
            }
        except Exception:
            return None

    def on_enable(self):
        if self._event_bus:
            self._event_bus.subscribe("cover.downloaded", self._on_cover_downloaded)

    def on_disable(self):
        if self._event_bus:
            self._event_bus.unsubscribe("cover.downloaded", self._on_cover_downloaded)

    def _on_cover_downloaded(self, event):
        pass
