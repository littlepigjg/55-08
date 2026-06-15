import os
import sys
from typing import List, Optional, Set
from urllib.parse import urlparse
from pathlib import Path


class SandboxViolationError(Exception):
    """沙箱违规异常"""
    pass


class PluginSandbox:
    """插件沙箱

    提供插件运行时安全隔离：
    - 文件系统访问限制（仅允许访问插件目录和临时目录
    - 网络请求域名白名单
    """

    def __init__(self, plugin_id: str, plugin_dir: str, allowed_domains: Optional[List[str]] = None):
        self.plugin_id = plugin_id
        self.plugin_dir = Path(plugin_dir).resolve()
        self.allowed_domains: Set[str] = set(allowed_domains or [])
        self._temp_dir: Optional[Path] = None

    def get_temp_dir(self) -> Path:
        """获取插件临时目录

        Returns:
            插件专属临时目录路径
        """
        if self._temp_dir is None:
            import tempfile

            temp_base = Path(tempfile.gettempdir()) / "ebook_manager_plugins" / self.plugin_id
            temp_base.mkdir(parents=True, exist_ok=True)
            self._temp_dir = temp_base
        return self._temp_dir

    def get_plugin_dir(self) -> Path:
        """获取插件目录

        Returns:
            插件安装目录路径
        """
        return self.plugin_dir

    def can_access_file(self, file_path: str) -> bool:
        """检查是否允许访问文件

        Args:
            file_path: 文件路径

        Returns:
            是否允许访问
        """
        try:
            resolved = Path(file_path).resolve()
        except Exception:
            return False

        if self.plugin_dir in resolved.parents or resolved == self.plugin_dir:
            return True

        temp_dir = self.get_temp_dir()
        if temp_dir in resolved.parents or resolved == temp_dir:
            return True

        return False

    def can_access_network(self, url: str) -> bool:
        """检查是否允许访问网络地址

        Args:
            url: URL 地址

        Returns:
            是否允许访问
        """
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return False

            domain = parsed.netloc.lower()

            if domain in self.allowed_domains:
                return True

            for allowed in self.allowed_domains:
                if domain.endswith("." + allowed) or domain == allowed:
                    return True

            return False
        except Exception:
            return False

    def safe_open(self, file_path: str, mode: str = "r", **kwargs):
        """安全打开文件

        Args:
            file_path: 文件路径
            mode: 打开模式
            **kwargs: 其他参数

        Returns:
            文件对象

        Raises:
            SandboxViolationError: 不允许访问该文件
        """
        if not self.can_access_file(file_path):
            raise SandboxViolationError(
                f"Plugin '{self.plugin_id}' is not allowed to access file: {file_path}"
            )
        return open(file_path, mode, **kwargs)

    def safe_request(self, method: str, url: str, **kwargs):
        """安全发起网络请求

        Args:
            method: HTTP 方法
            url: URL 地址
            **kwargs: 请求参数

        Returns:
            requests.Response 对象

        Raises:
            SandboxViolationError: 不允许访问该域名
        """
        if not self.can_access_network(url):
            raise SandboxViolationError(
                f"Plugin '{self.plugin_id}' is not allowed to access URL: {url}"
            )
        import requests
        return requests.request(method, url, timeout=kwargs.pop("timeout", 10), **kwargs)

    def add_allowed_domain(self, domain: str):
        """添加允许的域名

        Args:
            domain: 域名
        """
        self.allowed_domains.add(domain.lower())

    def remove_allowed_domain(self, domain: str):
        """移除允许的域名

        Args:
            domain: 域名
        """
        self.allowed_domains.discard(domain.lower())
