from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QCheckBox, QGroupBox, QTextEdit, QSplitter,
    QMessageBox, QProgressBar, QTabWidget, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from ..plugins import PluginManager, PluginInfo


class PluginMarketDialog(QDialog):
    """插件市场对话框"""

    def __init__(self, plugin_manager: PluginManager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.setWindowTitle("插件市场")
        self.setMinimumSize(900, 600)
        self._init_ui()
        self._load_plugins()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        header = QLabel("🔌 插件管理中心")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        main_layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        list_header = QLabel("已安装插件")
        list_header.setStyleSheet("font-weight: bold; padding: 4px;")
        left_layout.addWidget(list_header)

        self.plugin_list = QListWidget()
        self.plugin_list.itemSelectionChanged.connect(self._on_plugin_selected)
        left_layout.addWidget(self.plugin_list)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self._refresh_plugins)
        btn_layout.addWidget(self.refresh_btn)

        self.install_btn = QPushButton("📦 安装插件")
        self.install_btn.clicked.connect(self._install_plugin)
        btn_layout.addWidget(self.install_btn)

        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)

        self.plugin_name_label = QLabel("选择一个插件查看详情")
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        self.plugin_name_label.setFont(name_font)
        info_layout.addWidget(self.plugin_name_label)

        self.plugin_id_label = QLabel("")
        self.plugin_id_label.setStyleSheet("color: #666; font-size: 12px;")
        info_layout.addWidget(self.plugin_id_label)

        info_layout.addSpacing(10)

        info_group = QGroupBox("基本信息")
        info_group_layout = QVBoxLayout(info_group)

        self.version_label = QLabel("版本: -")
        info_group_layout.addWidget(self.version_label)

        self.author_label = QLabel("作者: -")
        info_group_layout.addWidget(self.author_label)

        self.email_label = QLabel("邮箱: -")
        info_group_layout.addWidget(self.email_label)

        self.type_label = QLabel("类型: -")
        info_group_layout.addWidget(self.type_label)

        info_layout.addWidget(info_group)

        desc_group = QGroupBox("描述")
        desc_layout = QVBoxLayout(desc_group)
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMaximumHeight(120)
        desc_layout.addWidget(self.desc_text)
        info_layout.addWidget(desc_group)

        domains_group = QGroupBox("允许的网络域名")
        domains_layout = QVBoxLayout(domains_group)
        self.domains_text = QTextEdit()
        self.domains_text.setReadOnly(True)
        self.domains_text.setMaximumHeight(80)
        domains_layout.addWidget(self.domains_text)
        info_layout.addWidget(domains_group)

        deps_group = QGroupBox("依赖项")
        deps_layout = QVBoxLayout(deps_group)
        self.deps_text = QTextEdit()
        self.deps_text.setReadOnly(True)
        self.deps_text.setMaximumHeight(80)
        deps_layout.addWidget(self.deps_text)
        info_layout.addWidget(deps_group)

        info_layout.addStretch()

        self.tabs.addTab(info_tab, "📋 详情")

        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)

        enable_group = QGroupBox("插件状态")
        enable_layout = QVBoxLayout(enable_group)

        self.enable_checkbox = QCheckBox("启用此插件")
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        enable_layout.addWidget(self.enable_checkbox)

        settings_layout.addWidget(enable_group)

        actions_group = QGroupBox("操作")
        actions_layout = QVBoxLayout(actions_group)

        self.reload_btn = QPushButton("🔄 重新加载插件")
        self.reload_btn.clicked.connect(self._reload_plugin)
        actions_layout.addWidget(self.reload_btn)

        self.uninstall_btn = QPushButton("🗑️ 卸载插件")
        self.uninstall_btn.clicked.connect(self._uninstall_plugin)
        actions_layout.addWidget(self.uninstall_btn)

        settings_layout.addWidget(actions_group)
        settings_layout.addStretch()

        self.tabs.addTab(settings_tab, "⚙️ 设置")

        right_layout.addWidget(self.tabs)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(self.close_btn)

        main_layout.addLayout(bottom_layout)

        self.setStyleSheet("""
            QDialog { background: #f5f6fa; }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background: #4a9eff33;
                color: #000;
            }
            QPushButton {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 12px;
                background: white;
            }
            QPushButton:hover { background: #f0f7ff; border-color: #4a9eff; }
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QTabBar::tab {
                padding: 6px 16px;
                border: 1px solid #ddd;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                background: #fafafa;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
            }
        """)

    def _load_plugins(self):
        self.plugin_manager.scan_plugins()
        self._refresh_plugin_list()

    def _refresh_plugin_list(self):
        self.plugin_list.clear()
        plugins = self.plugin_manager.get_all_plugins_info()

        for info in sorted(plugins, key=lambda p: p.plugin_name):
            item = QListWidgetItem()

            status_icon = "✅" if info.enabled else "⬜"
            if info.error:
                status_icon = "❌"

            item.setText(f"{status_icon} {info.plugin_name}")
            item.setData(Qt.ItemDataRole.UserRole, info.plugin_id)

            self.plugin_list.addItem(item)

    def _on_plugin_selected(self):
        current_item = self.plugin_list.currentItem()
        if not current_item:
            return

        plugin_id = current_item.data(Qt.ItemDataRole.UserRole)
        info = self.plugin_manager.get_plugin_info(plugin_id)

        if not info:
            return

        self.plugin_name_label.setText(info.plugin_name)
        self.plugin_id_label.setText(f"ID: {info.plugin_id}")
        self.version_label.setText(f"版本: {info.version}")
        self.author_label.setText(f"作者: {info.author or '未知'}")
        self.email_label.setText(f"邮箱: {info.author_email or '未知'}")
        self.type_label.setText(f"类型: {info.plugin_type}")

        desc = info.description
        if info.error:
            desc = f"⚠️ 加载错误: {info.error}\n\n{desc}"
        self.desc_text.setPlainText(desc)

        self.domains_text.setPlainText(
            "\n".join(info.allowed_domains) if info.allowed_domains else "无"
        )
        self.deps_text.setPlainText(
            "\n".join(info.dependencies) if info.dependencies else "无"
        )

        self.enable_checkbox.blockSignals(True)
        self.enable_checkbox.setChecked(info.enabled)
        self.enable_checkbox.blockSignals(False)

        self.enable_checkbox.setEnabled(bool(info.plugin_id and not info.error))

    def _on_enable_changed(self, state):
        current_item = self.plugin_list.currentItem()
        if not current_item:
            return

        plugin_id = current_item.data(Qt.ItemDataRole.UserRole)
        enabled = state == Qt.CheckState.Checked.value

        if enabled:
            success = self.plugin_manager.enable_plugin(plugin_id)
            if not success:
                QMessageBox.warning(self, "提示", "启用插件失败")
                self.enable_checkbox.blockSignals(True)
                self.enable_checkbox.setChecked(False)
                self.enable_checkbox.blockSignals(False)
                return
        else:
            self.plugin_manager.disable_plugin(plugin_id)

        self._refresh_plugin_list()
        self._select_plugin(plugin_id)

    def _select_plugin(self, plugin_id):
        for i in range(self.plugin_list.count()):
            item = self.plugin_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == plugin_id:
                self.plugin_list.setCurrentRow(i)
                break

    def _refresh_plugins(self):
        self._load_plugins()
        QMessageBox.information(self, "提示", "插件列表已刷新")

    def _install_plugin(self):
        QMessageBox.information(
            self, "安装插件",
            "将插件文件或目录放入 plugins 文件夹后，点击刷新即可。\n\n"
            "plugins 目录位于程序根目录下。"
        )

    def _reload_plugin(self):
        current_item = self.plugin_list.currentItem()
        if not current_item:
            return

        plugin_id = current_item.data(Qt.ItemDataRole.UserRole)
        if self.plugin_manager.reload_plugin(plugin_id):
            QMessageBox.information(self, "提示", "插件已重新加载")
            self._refresh_plugin_list()
            self._select_plugin(plugin_id)
        else:
            QMessageBox.warning(self, "提示", "插件重载失败")

    def _uninstall_plugin(self):
        current_item = self.plugin_list.currentItem()
        if not current_item:
            return

        plugin_id = current_item.data(Qt.ItemDataRole.UserRole)
        info = self.plugin_manager.get_plugin_info(plugin_id)

        if not info:
            return

        reply = QMessageBox.question(
            self, "确认卸载",
            f"确定要卸载插件「{info.plugin_name}」吗？\n\n"
            "注意：这将禁用插件，但不会删除插件文件。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.plugin_manager.unload_plugin(plugin_id)
            self._refresh_plugin_list()
            QMessageBox.information(self, "提示", "插件已卸载")

    def get_enabled_sources(self):
        return self.plugin_manager.get_source_plugins()
