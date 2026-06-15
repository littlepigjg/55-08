from ebook_manager.plugins import BasePlugin, ISource
from typing import List, Optional, Dict, Any


class DedaoSource(BasePlugin, ISource):
    """得到电子书元数据来源插件示例"""

    plugin_id = "dedao"
    plugin_name = "得到电子书"
    version = "0.1.0"
    author = "开发者名称"
    author_email = "dev@example.com"
    description = "得到电子书元数据查询插件"
    dependencies = []
    allowed_domains = ["dedao.cn", "igetget.com"]
    plugin_type = "source"

    @property
    def source_id(self) -> str:
        return self.plugin_id

    @property
    def source_name(self) -> str:
        return self.plugin_name

    @property
    def source_url(self) -> str:
        return "https://www.dedao.cn"

    def search_by_title(self, title: str, max_results: int = 5) -> List[Dict[str, Any]]:
        try:
            results = []
            for i in range(min(max_results, 3)):
                results.append({
                    "title": f"{title} (得到示例{i+1})",
                    "author": "示例作者",
                    "publisher": "得到出版社",
                    "publish_date": "2024",
                    "isbn": "",
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
                "title": "得到示例书籍",
                "author": "示例作者",
                "publisher": "得到出版社",
                "publish_date": "2024",
                "isbn": isbn,
                "source": self.source_id,
                "cover_url": "",
            }
        except Exception:
            return None

    def parse_result(self, raw_data: Any) -> Dict[str, Any]:
        if isinstance(raw_data, dict):
            return {
                "title": raw_data.get("book_title", raw_data.get("title", "")),
                "author": raw_data.get("author", ""),
                "publisher": raw_data.get("publisher", ""),
                "publish_date": raw_data.get("publish_time", ""),
                "isbn": raw_data.get("isbn", ""),
                "source": self.source_id,
            }
        return {}

    def get_book_detail(self, book_id: str) -> Optional[Dict[str, Any]]:
        try:
            return {
                "title": "得到书籍详情",
                "author": "示例作者",
                "publisher": "得到出版社",
                "publish_date": "2024",
                "isbn": "",
                "description": "这是得到电子书数据源的示例书籍详情",
                "source": self.source_id,
            }
        except Exception:
            return None
