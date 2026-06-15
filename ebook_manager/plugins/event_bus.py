from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
import threading


@dataclass
class Event:
    """事件对象

    Attributes:
        name: 事件名称
        data: 事件数据
        source: 事件来源（插件 ID）
    """
    name: str
    data: Any = None
    source: str = "system"


class EventBus:
    """事件总线

    支持插件间的松耦合通信，发布-订阅模式
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._lock = threading.RLock()

    def subscribe(self, event_name: str, callback: Callable[[Event], None]):
        """订阅事件

        Args:
            event_name: 事件名称，支持 '*' 订阅所有事件
            callback: 回调函数
        """
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            if callback not in self._subscribers[event_name]:
                self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[Event], None]):
        """取消订阅

        Args:
            event_name: 事件名称
            callback: 回调函数
        """
        with self._lock:
            if event_name in self._subscribers:
                try:
                    self._subscribers[event_name].remove(callback)
                except ValueError:
                    pass

    def publish(self, event: Event):
        """发布事件

        Args:
            event: 事件对象
        """
        with self._lock:
            callbacks = []
            if event.name in self._subscribers:
                callbacks.extend(self._subscribers[event.name])
            if "*" in self._subscribers:
                callbacks.extend(self._subscribers["*"])

        for callback in callbacks:
            try:
                callback(event)
            except Exception:
                pass

    def clear(self):
        """清空所有订阅者"""
        with self._lock:
            self._subscribers.clear()

    def get_subscribers_count(self, event_name: str = None) -> int:
        """获取订阅者数量

        Args:
            event_name: 事件名称，为 None 时返回总数
        """
        with self._lock:
            if event_name:
                return len(self._subscribers.get(event_name, []))
            return sum(len(callbacks) for callbacks in self._subscribers.values())


_global_event_bus = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus
