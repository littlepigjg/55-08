from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class ISource(ABC):
    """元数据来源标准接口

    所有插件数据源必须实现此接口
    """

    @property
    @abstractmethod
    def source_id(self) -> str:
        """数据源唯一标识符，如 'douban', 'openlibrary'"""
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源显示名称，如 '豆瓣读书'"""
        ...

    @property
    @abstractmethod
    def source_url(self) -> str:
        """数据源官网 URL"""
        ...

    @abstractmethod
    def search_by_title(self, title: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """按书名搜索

        Args:
            title: 书名关键词
            max_results: 最大返回结果数

        Returns:
            搜索结果列表，每个结果为字典，包含 title, author, publisher, cover_url 等字段
        """
        ...

    @abstractmethod
    def search_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """按 ISBN 搜索

        Args:
            isbn: ISBN 编号

        Returns:
            书籍详情字典，未找到返回 None
        """
        ...

    @abstractmethod
    def parse_result(self, raw_data: Any) -> Dict[str, Any]:
        """解析原始数据为标准格式

        Args:
            raw_data: 原始 API 返回的原始数据

        Returns:
            标准化的书籍信息字典
        """
        ...

    @abstractmethod
    def get_book_detail(self, book_id: str) -> Optional[Dict[str, Any]]:
        """获取书籍详细信息

        Args:
            book_id: 书籍在该数据源的唯一 ID

        Returns:
            详细书籍信息字典
        """
        ...


class BasePlugin(ABC):
    """插件基类

    所有插件必须继承此类，提供插件元数据和生命周期钩子
    """

    plugin_id: str = ""
    plugin_name: str = ""
    version: str = "0.1.0"
    author: str = ""
    author_email: str = ""
    description: str = ""
    dependencies: List[str] = []
    allowed_domains: List[str] = []
    plugin_type: str = "source"

    def __init__(self):
        self._enabled = True
        self._event_bus = None
        self._sandbox = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if enabled:
            self.on_enable()
        else:
            self.on_disable()

    def set_event_bus(self, event_bus):
        self._event_bus = event_bus

    def set_sandbox(self, sandbox):
        self._sandbox = sandbox

    def on_enable(self):
        """插件启用时调用"""
        pass

    def on_disable(self):
        """插件禁用时调用"""
        pass

    def on_load(self):
        """插件加载时调用"""
        pass

    def on_unload(self):
        """插件卸载时调用"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "plugin_id": self.plugin_id,
            "plugin_name": self.plugin_name,
            "version": self.version,
            "author": self.author,
            "author_email": self.author_email,
            "description": self.description,
            "dependencies": self.dependencies,
            "allowed_domains": self.allowed_domains,
            "plugin_type": self.plugin_type,
            "enabled": self._enabled,
        }
