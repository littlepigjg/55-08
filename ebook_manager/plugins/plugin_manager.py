import os
import sys
import importlib
import importlib.util
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass

from .base import BasePlugin, ISource
from .event_bus import EventBus, Event, get_event_bus
from .sandbox import PluginSandbox


@dataclass
class PluginInfo:
    """插件信息"""
    plugin_id: str
    plugin_name: str
    version: str
    author: str
    author_email: str
    description: str
    dependencies: List[str]
    allowed_domains: List[str]
    plugin_type: str
    enabled: bool
    plugin_dir: str
    module_path: str
    error: str = ""


class PluginManager:
    """插件管理器

    负责插件的扫描、加载、卸载、依赖管理等
    """

    def __init__(self, plugins_dir: Optional[str] = None, dev_mode: bool = False):
        if plugins_dir is None:
            self.plugins_dir = Path(__file__).parent.parent.parent / "plugins"
        else:
            self.plugins_dir = Path(plugins_dir)

        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_infos: Dict[str, PluginInfo] = {}
        self._event_bus: EventBus = get_event_bus()
        self._sandboxes: Dict[str, PluginSandbox] = {}
        self._dev_mode = dev_mode
        self._file_watchers = {}

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    def scan_plugins(self) -> List[PluginInfo]:
        """扫描插件目录，发现可用插件

        Returns:
            插件信息列表
        """
        self._plugin_infos.clear()

        if not self.plugins_dir.exists():
            return []

        for item in self.plugins_dir.iterdir():
            if item.is_dir():
                plugin_info = self._inspect_plugin_dir(item)
                if plugin_info:
                    self._plugin_infos[plugin_info.plugin_id] = plugin_info
            elif item.suffix == ".py" and item.stem != "__init__":
                plugin_info = self._inspect_plugin_file(item)
                if plugin_info:
                    self._plugin_infos[plugin_info.plugin_id] = plugin_info

        return list(self._plugin_infos.values())

    def _inspect_plugin_dir(self, plugin_dir: Path) -> Optional[PluginInfo]:
        """检查目录型插件"""
        init_file = plugin_dir / "__init__.py"
        if not init_file.exists():
            return None

        try:
            spec = importlib.util.spec_from_file_location(
                f"plugin_temp_{plugin_dir.name}", init_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                plugin_class = self._find_plugin_class(module)
                if plugin_class:
                    plugin_instance = plugin_class()
                    info = plugin_instance.get_info()
                    return PluginInfo(
                        plugin_id=info["plugin_id"],
                        plugin_name=info["plugin_name"],
                        version=info["version"],
                        author=info["author"],
                        author_email=info["author_email"],
                        description=info["description"],
                        dependencies=info["dependencies"],
                        allowed_domains=info["allowed_domains"],
                        plugin_type=info["plugin_type"],
                        enabled=False,
                        plugin_dir=str(plugin_dir),
                        module_path=str(init_file),
                    )
        except Exception as e:
            return PluginInfo(
                plugin_id=plugin_dir.name,
                plugin_name=plugin_dir.name,
                version="unknown",
                author="",
                author_email="",
                description=f"加载失败: {str(e)}",
                dependencies=[],
                allowed_domains=[],
                plugin_type="unknown",
                enabled=False,
                plugin_dir=str(plugin_dir),
                module_path=str(init_file),
                error=str(e),
            )

        return None

    def _inspect_plugin_file(self, plugin_file: Path) -> Optional[PluginInfo]:
        """检查单文件插件"""
        try:
            spec = importlib.util.spec_from_file_location(
                f"plugin_temp_{plugin_file.stem}", plugin_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                plugin_class = self._find_plugin_class(module)
                if plugin_class:
                    plugin_instance = plugin_class()
                    info = plugin_instance.get_info()
                    return PluginInfo(
                        plugin_id=info["plugin_id"],
                        plugin_name=info["plugin_name"],
                        version=info["version"],
                        author=info["author"],
                        author_email=info["author_email"],
                        description=info["description"],
                        dependencies=info["dependencies"],
                        allowed_domains=info["allowed_domains"],
                        plugin_type=info["plugin_type"],
                        enabled=False,
                        plugin_dir=str(plugin_file.parent),
                        module_path=str(plugin_file),
                    )
        except Exception as e:
            return PluginInfo(
                plugin_id=plugin_file.stem,
                plugin_name=plugin_file.stem,
                version="unknown",
                author="",
                author_email="",
                description=f"加载失败: {str(e)}",
                dependencies=[],
                allowed_domains=[],
                plugin_type="unknown",
                enabled=False,
                plugin_dir=str(plugin_file.parent),
                module_path=str(plugin_file),
                error=str(e),
            )

        return None

    def _find_plugin_class(self, module) -> Optional[Type[BasePlugin]]:
        """在模块中查找插件类"""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BasePlugin)
                and attr is not BasePlugin
                and attr is not ISource
            ):
                return attr
        return None

    def load_plugin(self, plugin_id: str) -> bool:
        """加载插件

        Args:
            plugin_id: 插件 ID

        Returns:
            是否加载成功
        """
        if plugin_id in self._plugins:
            return True

        if plugin_id not in self._plugin_infos:
            return False

        info = self._plugin_infos[plugin_id]

        try:
            self._install_dependencies(info.dependencies)

            module_path = Path(info.module_path)
            module_name = f"plugin_{plugin_id}"

            if module_path.is_dir():
                module_path = module_path / "__init__.py"

            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if not spec or not spec.loader:
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                return False

            plugin_instance = plugin_class()

            sandbox = PluginSandbox(
                plugin_id=plugin_id,
                plugin_dir=info.plugin_dir,
                allowed_domains=info.allowed_domains,
            )
            plugin_instance.set_sandbox(sandbox)
            self._sandboxes[plugin_id] = sandbox

            plugin_instance.set_event_bus(self._event_bus)

            plugin_instance.on_load()

            self._plugins[plugin_id] = plugin_instance
            self._plugin_infos[plugin_id].enabled = True

            self._event_bus.publish(Event(
                name="plugin.loaded",
                data={"plugin_id": plugin_id, "plugin_name": info.plugin_name},
                source="plugin_manager",
            ))

            if self._dev_mode:
                self._start_file_watcher(plugin_id, info.plugin_dir)

            return True

        except Exception as e:
            if plugin_id in self._plugin_infos:
                self._plugin_infos[plugin_id].error = str(e)
            return False

    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件

        Args:
            plugin_id: 插件 ID

        Returns:
            是否卸载成功
        """
        if plugin_id not in self._plugins:
            return False

        try:
            plugin = self._plugins[plugin_id]
            plugin.on_unload()

            if plugin_id in self._file_watchers:
                self._stop_file_watcher(plugin_id)

            if plugin_id in self._sandboxes:
                del self._sandboxes[plugin_id]

            module_name = f"plugin_{plugin_id}"
            if module_name in sys.modules:
                del sys.modules[module_name]

            del self._plugins[plugin_id]
            if plugin_id in self._plugin_infos:
                self._plugin_infos[plugin_id].enabled = False

            self._event_bus.publish(Event(
                name="plugin.unloaded",
                data={"plugin_id": plugin_id},
                source="plugin_manager",
            ))

            return True
        except Exception as e:
            if plugin_id in self._plugin_infos:
                self._plugin_infos[plugin_id].error = str(e)
            return False

    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件

        Args:
            plugin_id: 插件 ID

        Returns:
            是否启用成功
        """
        if plugin_id not in self._plugins:
            if not self.load_plugin(plugin_id):
                return False

        plugin = self._plugins[plugin_id]
        plugin.set_enabled(True)

        self._event_bus.publish(Event(
            name="plugin.enabled",
            data={"plugin_id": plugin_id},
            source="plugin_manager",
        ))

        return True

    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件

        Args:
            plugin_id: 插件 ID

        Returns:
            是否禁用成功
        """
        if plugin_id not in self._plugins:
            return False

        plugin = self._plugins[plugin_id]
        plugin.set_enabled(False)

        self._event_bus.publish(Event(
            name="plugin.disabled",
            data={"plugin_id": plugin_id},
            source="plugin_manager",
        ))

        return True

    def reload_plugin(self, plugin_id: str) -> bool:
        """重新加载插件

        Args:
            plugin_id: 插件 ID

        Returns:
            是否重载成功
        """
        self.unload_plugin(plugin_id)
        return self.load_plugin(plugin_id)

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """获取插件实例

        Args:
            plugin_id: 插件 ID

        Returns:
            插件实例
        """
        return self._plugins.get(plugin_id)

    def get_source_plugins(self) -> List[BasePlugin]:
        """获取所有数据源类型的插件

        Returns:
            数据源插件列表
        """
        sources = []
        for plugin in self._plugins.values():
            if plugin.enabled and isinstance(plugin, ISource):
                sources.append(plugin)
        return sources

    def get_sandbox(self, plugin_id: str) -> Optional[PluginSandbox]:
        """获取插件沙箱

        Args:
            plugin_id: 插件 ID

        Returns:
            沙箱实例
        """
        return self._sandboxes.get(plugin_id)

    def get_all_plugins_info(self) -> List[PluginInfo]:
        """获取所有插件信息

        Returns:
            插件信息列表
        """
        return list(self._plugin_infos.values())

    def get_plugin_info(self, plugin_id: str) -> Optional[PluginInfo]:
        """获取指定插件信息

        Args:
            plugin_id: 插件 ID

        Returns:
            插件信息
        """
        return self._plugin_infos.get(plugin_id)

    def _install_dependencies(self, dependencies: List[str]):
        """安装插件依赖

        Args:
            dependencies: 依赖包列表
        """
        if not dependencies:
            return

        for dep in dependencies:
            try:
                importlib.import_module(dep.split("==")[0].split(">=")[0].split("<=")[0])
            except ImportError:
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", dep],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    pass

    def _start_file_watcher(self, plugin_id: str, plugin_dir: str):
        """启动文件监视器（开发模式）

        Args:
            plugin_id: 插件 ID
            plugin_dir: 插件目录
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class PluginFileHandler(FileSystemEventHandler):
                def __init__(self, manager, pid):
                    self.manager = manager
                    self.plugin_id = pid

                def on_modified(self, event):
                    if event.src_path.endswith(".py"):
                        from PyQt6.QtCore import QTimer
                        QTimer.singleShot(500, lambda: self._safe_reload())

                def _safe_reload(self):
                    try:
                        self.manager.reload_plugin(self.plugin_id)
                    except Exception:
                        pass

            observer = Observer()
            handler = PluginFileHandler(self, plugin_id)
            observer.schedule(handler, plugin_dir, recursive=True)
            observer.start()

            self._file_watchers[plugin_id] = observer
        except ImportError:
            pass

    def _stop_file_watcher(self, plugin_id: str):
        """停止文件监视器

        Args:
            plugin_id: 插件 ID
        """
        if plugin_id in self._file_watchers:
            try:
                self._file_watchers[plugin_id].stop()
                self._file_watchers[plugin_id].join()
            except Exception:
                pass
            del self._file_watchers[plugin_id]

    def load_all_plugins(self):
        """加载所有已发现的插件"""
        for plugin_id in list(self._plugin_infos.keys()):
            self.load_plugin(plugin_id)

    def unload_all_plugins(self):
        """卸载所有已加载的插件"""
        for plugin_id in list(self._plugins.keys()):
            self.unload_plugin(plugin_id)
