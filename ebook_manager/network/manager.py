from typing import List, Optional, Dict
from pathlib import Path

from .douban import DoubanSource
from .openlibrary import OpenLibrarySource
from ..plugins import PluginManager


class NetworkSourceManager:
    def __init__(self, plugin_manager: Optional[PluginManager] = None):
        self.douban = DoubanSource()
        self.openlibrary = OpenLibrarySource()

        if plugin_manager is None:
            plugins_dir = Path(__file__).parent.parent.parent / "plugins"
            self.plugin_manager = PluginManager(plugins_dir=str(plugins_dir))
            self.plugin_manager.scan_plugins()
            self.plugin_manager.load_all_plugins()
        else:
            self.plugin_manager = plugin_manager

    def get_builtin_sources(self) -> List[str]:
        return ["douban", "openlibrary"]

    def get_plugin_sources(self) -> List[str]:
        sources = []
        for plugin in self.plugin_manager.get_source_plugins():
            if plugin.enabled:
                sources.append(plugin.source_id)
        return sources

    def get_all_sources(self) -> List[str]:
        return self.get_builtin_sources() + self.get_plugin_sources()

    def get_source_names(self) -> Dict[str, str]:
        names = {
            "douban": "豆瓣读书",
            "openlibrary": "OpenLibrary",
        }
        for plugin in self.plugin_manager.get_source_plugins():
            if plugin.enabled:
                names[plugin.source_id] = plugin.source_name
        return names

    def search(
        self, query: str, sources: Optional[List[str]] = None, max_results: int = 5
    ) -> List[Dict]:
        if sources is None:
            sources = self.get_all_sources()
        results = []
        if "douban" in sources:
            results.extend(self.douban.search_by_title(query, max_results))
        if "openlibrary" in sources:
            results.extend(self.openlibrary.search_by_title(query, max_results))

        for plugin in self.plugin_manager.get_source_plugins():
            if plugin.source_id in sources and plugin.enabled:
                try:
                    plugin_results = plugin.search_by_title(query, max_results)
                    results.extend(plugin_results)
                except Exception:
                    pass

        return results[: max_results * 2]

    def search_by_isbn(self, isbn: str, sources: Optional[List[str]] = None) -> Optional[Dict]:
        if sources is None:
            sources = self.get_all_sources()

        if "douban" in sources:
            result = self.douban.search_by_isbn(isbn)
            if result:
                return result
        if "openlibrary" in sources:
            result = self.openlibrary.search_by_isbn(isbn)
            if result:
                return result

        for plugin in self.plugin_manager.get_source_plugins():
            if plugin.source_id in sources and plugin.enabled:
                try:
                    result = plugin.search_by_isbn(isbn)
                    if result:
                        return result
                except Exception:
                    pass

        return None

    def get_plugin_manager(self) -> PluginManager:
        return self.plugin_manager
