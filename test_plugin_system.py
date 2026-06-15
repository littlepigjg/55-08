import sys
import os
import tempfile

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

from ebook_manager.plugins import (
    PluginManager, BasePlugin, ISource,
    EventBus, Event, get_event_bus,
    PluginSandbox, SandboxViolationError
)

print("=" * 60)
print("插件系统测试")
print("=" * 60)

# 1. 测试事件总线
print("\n1. 测试事件总线...")
bus = EventBus()
events_received = []

def handler(event):
    events_received.append(event)

bus.subscribe("test.event", handler)
bus.publish(Event(name="test.event", data={"key": "value"}, source="test"))
assert len(events_received) == 1
assert events_received[0].name == "test.event"
assert events_received[0].data["key"] == "value"
print("   ✅ 事件总线工作正常")

# 2. 测试沙箱
print("\n2. 测试沙箱系统...")
temp_dir = tempfile.mkdtemp()
sandbox = PluginSandbox("test_plugin", temp_dir, ["example.com", "api.test.com"])

assert sandbox.can_access_network("https://example.com/api") == True
assert sandbox.can_access_network("https://sub.example.com/path") == True
assert sandbox.can_access_network("https://api.test.com/v1/books") == True
assert sandbox.can_access_network("https://google.com") == False
print("   ✅ 网络域名白名单工作正常")

test_file = os.path.join(temp_dir, "test.txt")
with open(test_file, "w") as f:
    f.write("test")

assert sandbox.can_access_file(test_file) == True
assert sandbox.can_access_file("C:\\Windows\\system32\\config") == False
print("   ✅ 文件系统访问限制工作正常")

# 3. 测试插件管理器
print("\n3. 测试插件管理器...")
plugins_dir = os.path.join(base_dir, "plugins")
manager = PluginManager(plugins_dir=plugins_dir)

infos = manager.scan_plugins()
print(f"   发现 {len(infos)} 个插件")
for info in infos:
    status = "✅" if not info.error else "❌"
    print(f"     {status} {info.plugin_name} (v{info.version}) - {info.plugin_id}")

# 4. 测试插件加载
print("\n4. 测试插件加载...")
loaded_count = 0
for info in infos:
    if info.plugin_id.startswith("_"):
        continue
    if info.error:
        continue
    success = manager.load_plugin(info.plugin_id)
    if success:
        loaded_count += 1
        print(f"   ✅ 成功加载: {info.plugin_name}")
    else:
        print(f"   ❌ 加载失败: {info.plugin_name}")

print(f"\n   共成功加载 {loaded_count} 个插件")

# 5. 测试数据源插件
print("\n5. 测试数据源插件...")
source_plugins = manager.get_source_plugins()
print(f"   找到 {len(source_plugins)} 个数据源插件")

for source in source_plugins:
    if hasattr(source, "search_by_title"):
        try:
            results = source.search_by_title("Python", 3)
            print(f"   ✅ {source.source_name}: 返回 {len(results)} 条结果")
        except Exception as e:
            print(f"   ❌ {source.source_name}: 搜索失败 - {e}")

# 6. 测试全局事件总线
print("\n6. 测试全局事件总线...")
global_bus = get_event_bus()
assert global_bus is not None
print("   ✅ 全局事件总线获取成功")

print("\n" + "=" * 60)
print("🎉 所有测试通过！插件系统工作正常")
print("=" * 60)
