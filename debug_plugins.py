import sys
import os
from pathlib import Path

print("当前工作目录:", os.getcwd())

script_dir = Path(__file__).parent
print("脚本目录:", script_dir)

plugin_manager_file = script_dir / "ebook_manager" / "plugins" / "plugin_manager.py"
print("plugin_manager.py 路径:", plugin_manager_file.resolve())
print("文件是否存在:", plugin_manager_file.exists())

default_plugins_dir = plugin_manager_file.parent.parent.parent / "plugins"
print("\n默认 plugins 目录:", default_plugins_dir.resolve())
print("目录是否存在:", default_plugins_dir.exists())

if default_plugins_dir.exists():
    print("\n目录内容:")
    for item in default_plugins_dir.iterdir():
        item_type = "目录" if item.is_dir() else "文件"
        print(f"  {item.name} ({item_type})")

sys.path.insert(0, str(script_dir))
from ebook_manager.plugins import PluginManager

print("\n" + "="*50)
print("测试 PluginManager...")
manager = PluginManager(plugins_dir=str(default_plugins_dir))
infos = manager.scan_plugins()
print(f"扫描到 {len(infos)} 个插件")

for info in infos:
    print(f"\n  - {info.plugin_name}")
    print(f"    ID: {info.plugin_id}")
    print(f"    版本: {info.version}")
    if info.error:
        print(f"    错误: {info.error}")
