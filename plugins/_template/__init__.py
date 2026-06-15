from ebook_manager.plugins import BasePlugin, ISource, Event
from typing import List, Optional, Dict, Any


class TemplateSource(BasePlugin, ISource):
    """插件开发模板

    这是一个数据源插件的完整模板，第三方开发者可以基于此开发新的数据源插件。
    """

    plugin_id = "template_source"
    plugin_name = "插件模板"
    version = "0.1.0"
    author = "你的名字"
    author_email = "your@email.com"
    description = "插件开发模板 - 请基于此创建你的数据源插件"
    dependencies = ["requests>=2.28.0"]
    allowed_domains = ["api.example.com"]
    plugin_type = "source"

    def __init__(self):
        super().__init__()
        self._session = None

    @property
    def source_id(self) -> str:
        """数据源唯一标识符"""
        return self.plugin_id

    @property
    def source_name(self) -> str:
        """数据源显示名称"""
        return self.plugin_name

    @property
    def source_url(self) -> str:
        """数据源官网"""
        return "https://example.com"

    def search_by_title(self, title: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """按书名搜索

        Args:
            title: 书名关键词
            max_results: 最大返回结果数

        Returns:
            搜索结果列表，每个结果为字典
        """
        try:
            results = []
            for i in range(min(max_results, 5)):
                result = {
                    "title": f"{title} - 结果{i+1}",
                    "author": "作者示例",
                    "publisher": "出版社示例",
                    "publish_date": "2024",
                    "isbn": "",
                    "source": self.source_id,
                    "subject_id": f"id_{i}",
                    "cover_url": "",
                    "source_url": "",
                }
                results.append(result)
            return results
        except Exception as e:
            return []

    def search_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """按 ISBN 搜索

        Args:
            isbn: ISBN 编号

        Returns:
            书籍详情，未找到返回 None
        """
        try:
            return {
                "title": "示例书籍",
                "author": "示例作者",
                "publisher": "示例出版社",
                "publish_date": "2024",
                "isbn": isbn,
                "source": self.source_id,
                "subject_id": isbn,
                "cover_url": "",
            }
        except Exception:
            return None

    def parse_result(self, raw_data: Any) -> Dict[str, Any]:
        """解析原始数据为标准格式

        Args:
            raw_data: API 返回的原始数据

        Returns:
            标准化的书籍信息字典
        """
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
        """获取书籍详细信息

        Args:
            book_id: 书籍在该数据源的唯一 ID

        Returns:
            详细书籍信息
        """
        try:
            return {
                "title": "书籍详情标题",
                "author": "详细作者",
                "publisher": "详细出版社",
                "publish_date": "2024",
                "isbn": "9787000000000",
                "description": "这是书籍的详细描述信息...",
                "tags": ["标签1", "标签2"],
                "source": self.source_id,
                "cover_url": "",
            }
        except Exception:
            return None

    def on_enable(self):
        """插件启用时调用

        可以在这里初始化资源、订阅事件等
        """
        if self._event_bus:
            self._event_bus.subscribe("cover.downloaded", self._on_cover_downloaded)

    def on_disable(self):
        """插件禁用时调用

        可以在这里清理资源、取消订阅等
        """
        if self._event_bus:
            self._event_bus.unsubscribe("cover.downloaded", self._on_cover_downloaded)

    def on_load(self):
        """插件加载时调用"""
        pass

    def on_unload(self):
        """插件卸载时调用"""
        pass

    def _on_cover_downloaded(self, event: Event):
        """封面下载完成事件处理

        Args:
            event: 事件对象，包含书籍ID和封面路径等信息
        """
        pass

    def _publish_search_event(self, query: str):
        """发布搜索事件示例

        Args:
            query: 搜索关键词
        """
        if self._event_bus:
            self._event_bus.publish(Event(
                name="source.search",
                data={"query": query, "source": self.source_id},
                source=self.plugin_id,
            ))
