# 插件开发指南

## 目录

- [简介](#简介)
- [快速开始](#快速开始)
- [插件接口说明](#插件接口说明)
- [沙箱安全机制](#沙箱安全机制)
- [事件总线](#事件总线)
- [插件生命周期](#插件生命周期)
- [热重载（开发模式）](#热重载开发模式)
- [示例代码](#示例代码)

## 简介

电子书元数据管理器支持插件扩展，第三方开发者可以开发自己的元数据来源插件，无需修改核心代码。插件以独立 Python 模块的形式放在 `plugins` 目录下，程序启动时自动扫描加载。

## 快速开始

### 1. 创建插件文件

将插件文件放入 `plugins/` 目录下，支持两种形式：

- **单文件插件**：`plugins/my_plugin.py`
- **目录插件**：`plugins/my_plugin/__init__.py`

### 2. 编写插件代码

```python
from ebook_manager.plugins import BasePlugin, ISource
from typing import List, Optional, Dict, Any

class MySourcePlugin(BasePlugin, ISource):
    plugin_id = "my_source"
    plugin_name = "我的数据源"
    version = "1.0.0"
    author = "你的名字"
    author_email = "your@email.com"
    description = "这是一个示例数据源插件"
    dependencies = ["requests>=2.28.0"]
    allowed_domains = ["api.example.com"]
    plugin_type = "source"

    @property
    def source_id(self) -> str:
        return self.plugin_id

    @property
    def source_name(self) -> str:
        return self.plugin_name

    @property
    def source_url(self) -> str:
        return "https://example.com"

    def search_by_title(self, title: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """按书名搜索"""
        # 实现搜索逻辑
        return []

    def search_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """按 ISBN 搜索"""
        # 实现搜索逻辑
        return None

    def parse_result(self, raw_data: Any) -> Dict[str, Any]:
        """解析原始数据"""
        return {}

    def get_book_detail(self, book_id: str) -> Optional[Dict[str, Any]]:
        """获取书籍详情"""
        # 实现详情获取逻辑
        return None
```

### 3. 启用插件

启动程序后，在「工具」→「插件市场」中找到你的插件，点击启用。

## 插件接口说明

### ISource 接口

所有数据源插件必须实现 `ISource` 接口：

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `search_by_title(title, max_results)` | 按书名搜索 | title: 书名<br>max_results: 最大结果数 | 搜索结果列表 |
| `search_by_isbn(isbn)` | 按 ISBN 搜索 | isbn: ISBN 编号 | 书籍详情或 None |
| `parse_result(raw_data)` | 解析原始数据 | raw_data: API 原始数据 | 标准化字典 |
| `get_book_detail(book_id)` | 获取书籍详情 | book_id: 书籍唯一 ID | 详细信息或 None |

### 插件元数据

继承 `BasePlugin` 后，需要定义以下类属性：

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `plugin_id` | str | ✅ | 插件唯一标识符，建议使用小写字母和下划线 |
| `plugin_name` | str | ✅ | 插件显示名称 |
| `version` | str | ✅ | 版本号，建议使用语义化版本（如 1.0.0） |
| `author` | str | - | 作者姓名 |
| `author_email` | str | - | 作者邮箱 |
| `description` | str | - | 插件描述 |
| `dependencies` | List[str] | - | 依赖的 Python 包列表，格式如 `["requests>=2.28.0"]` |
| `allowed_domains` | List[str] | - | 允许访问的网络域名白名单 |
| `plugin_type` | str | - | 插件类型，目前支持 `source` |

### 搜索结果格式

`search_by_title` 和 `search_by_isbn` 返回的字典应包含以下字段：

```python
{
    "title": "书名",
    "author": "作者",
    "publisher": "出版社",
    "publish_date": "出版日期",
    "isbn": "ISBN编号",
    "source": "数据源ID",
    "subject_id": "书籍在该数据源的唯一ID",
    "cover_url": "封面图片URL",
    "source_url": "书籍详情页URL",
    "description": "书籍简介",
    "tags": ["标签1", "标签2"],
}
```

## 沙箱安全机制

为了防止恶意插件窃取数据，插件运行在沙箱环境中，具有以下限制：

### 文件系统访问限制

插件只能访问以下目录：
- 插件自身目录（只读/写）
- 插件专属临时目录（只读/写）

**安全访问文件的方式：**

```python
# 使用沙箱提供的安全方法
if self._sandbox:
    with self._sandbox.safe_open("data.txt", "r") as f:
        content = f.read()

# 获取临时目录
temp_dir = self._sandbox.get_temp_dir()
```

### 网络请求限制

插件只能访问 `allowed_domains` 中声明的域名。

**安全发起网络请求的方式：**

```python
if self._sandbox:
    response = self._sandbox.safe_request(
        "GET",
        "https://api.example.com/books",
        params={"q": "python"}
    )
    data = response.json()
```

**违规访问会抛出 `SandboxViolationError` 异常。**

## 事件总线

插件间可以通过事件总线进行松耦合通信。

### 发布事件

```python
from ebook_manager.plugins import Event

if self._event_bus:
    self._event_bus.publish(Event(
        name="my_plugin.custom_event",
        data={"key": "value"},
        source=self.plugin_id,
    ))
```

### 订阅事件

```python
def on_custom_event(event):
    print(f"收到事件: {event.name}, 数据: {event.data}")

def on_enable(self):
    if self._event_bus:
        self._event_bus.subscribe("my_plugin.custom_event", on_custom_event)
        # 也可以订阅所有事件
        self._event_bus.subscribe("*", self._on_any_event)

def on_disable(self):
    if self._event_bus:
        self._event_bus.unsubscribe("my_plugin.custom_event", on_custom_event)
```

### 系统内置事件

| 事件名 | 触发时机 | 数据 |
|--------|----------|------|
| `plugin.loaded` | 插件加载后 | `{plugin_id, plugin_name}` |
| `plugin.unloaded` | 插件卸载后 | `{plugin_id}` |
| `plugin.enabled` | 插件启用后 | `{plugin_id}` |
| `plugin.disabled` | 插件禁用后 | `{plugin_id}` |
| `cover.downloaded` | 封面下载完成后 | `{book_id, cover_path}` |
| `source.search` | 元数据搜索时 | `{query, source}` |

## 插件生命周期

插件有以下生命周期钩子方法，可以重写以实现自定义逻辑：

```python
def on_load(self):
    """插件加载时调用，进行初始化"""
    pass

def on_unload(self):
    """插件卸载时调用，进行清理"""
    pass

def on_enable(self):
    """插件启用时调用"""
    pass

def on_disable(self):
    """插件禁用时调用"""
    pass
```

**调用顺序：**
- 加载：`__init__` → `on_load` → `on_enable`
- 禁用：`on_disable`
- 卸载：`on_disable` → `on_unload`

## 热重载（开发模式）

开发模式下，修改插件代码后无需重启程序即可生效。

### 启用开发模式

在创建 PluginManager 时设置 `dev_mode=True`：

```python
from ebook_manager.plugins import PluginManager

plugin_manager = PluginManager(
    plugins_dir="./plugins",
    dev_mode=True
)
```

### 安装 watchgod 依赖

热重载功能需要 `watchdog` 库：

```bash
pip install watchdog
```

启用后，修改插件文件会自动触发重新加载。

## 示例代码

### 示例1：简单的数据源插件

```python
from ebook_manager.plugins import BasePlugin, ISource
from typing import List, Optional, Dict, Any

class SimpleSource(BasePlugin, ISource):
    plugin_id = "simple_source"
    plugin_name = "简单数据源"
    version = "0.1.0"
    author = "开发者"
    author_email = "dev@example.com"
    description = "一个简单的示例数据源插件"
    dependencies = []
    allowed_domains = ["api.example.com"]
    plugin_type = "source"

    @property
    def source_id(self) -> str:
        return self.plugin_id

    @property
    def source_name(self) -> str:
        return self.plugin_name

    @property
    def source_url(self) -> str:
        return "https://example.com"

    def search_by_title(self, title: str, max_results: int = 5) -> List[Dict[str, Any]]:
        try:
            results = []
            for i in range(min(max_results, 5)):
                results.append({
                    "title": f"{title} (结果{i+1})",
                    "author": "作者名",
                    "publisher": "出版社",
                    "publish_date": "2024",
                    "isbn": "",
                    "source": self.source_id,
                    "subject_id": f"id_{i}",
                    "cover_url": "",
                })
            return results
        except Exception:
            return []

    def search_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        try:
            return {
                "title": "示例书籍",
                "author": "作者名",
                "publisher": "出版社",
                "publish_date": "2024",
                "isbn": isbn,
                "source": self.source_id,
            }
        except Exception:
            return None

    def parse_result(self, raw_data: Any) -> Dict[str, Any]:
        if isinstance(raw_data, dict):
            return {
                "title": raw_data.get("name", ""),
                "author": raw_data.get("writer", ""),
                "publisher": raw_data.get("press", ""),
                "publish_date": raw_data.get("year", ""),
                "isbn": raw_data.get("isbn", ""),
                "source": self.source_id,
            }
        return {}

    def get_book_detail(self, book_id: str) -> Optional[Dict[str, Any]]:
        try:
            return {
                "title": "书籍详情",
                "author": "作者名",
                "publisher": "出版社",
                "publish_date": "2024",
                "isbn": "9787000000000",
                "description": "这是书籍的详细描述...",
                "tags": ["标签1", "标签2"],
                "source": self.source_id,
            }
        except Exception:
            return None
```

### 示例2：使用事件总线的插件

```python
from ebook_manager.plugins import BasePlugin, ISource, Event
from typing import List, Optional, Dict, Any

class EventSource(BasePlugin, ISource):
    plugin_id = "event_source"
    plugin_name = "事件示例插件"
    version = "0.1.0"
    author = "开发者"
    author_email = "dev@example.com"
    description = "演示事件总线的使用"
    dependencies = []
    allowed_domains = []
    plugin_type = "source"

    @property
    def source_id(self) -> str:
        return self.plugin_id

    @property
    def source_name(self) -> str:
        return self.plugin_name

    @property
    def source_url(self) -> str:
        return "https://example.com"

    def search_by_title(self, title: str, max_results: int = 5) -> List[Dict[str, Any]]:
        self._publish_search_event(title)
        return []

    def search_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        return None

    def parse_result(self, raw_data: Any) -> Dict[str, Any]:
        return {}

    def get_book_detail(self, book_id: str) -> Optional[Dict[str, Any]]:
        return None

    def on_enable(self):
        if self._event_bus:
            self._event_bus.subscribe("cover.downloaded", self._on_cover_downloaded)

    def on_disable(self):
        if self._event_bus:
            self._event_bus.unsubscribe("cover.downloaded", self._on_cover_downloaded)

    def _on_cover_downloaded(self, event: Event):
        pass

    def _publish_search_event(self, query: str):
        if self._event_bus:
            self._event_bus.publish(Event(
                name="source.search",
                data={"query": query},
                source=self.plugin_id,
            ))
```

## 常见问题

### Q: 如何调试插件？

A: 可以在插件中使用 `print()` 输出日志，或者使用 Python 的 `logging` 模块。

### Q: 插件可以访问数据库吗？

A: 可以，但需要在 `dependencies` 中声明数据库驱动，并自行管理数据库连接。数据库文件建议放在插件临时目录中。

### Q: 插件之间可以直接调用吗？

A: 不建议直接调用，应该通过事件总线进行松耦合通信。

### Q: 如何发布我的插件？

A: 将插件文件或目录打包分享，用户放入 `plugins` 目录后刷新即可使用。
