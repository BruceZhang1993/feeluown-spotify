# fuo_spotify/provider_ui.py
import logging
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from feeluown.utils.dispatch import Signal

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    def __init__(self, login_manager, parent=None):
        super().__init__(parent)
        self._login_manager = login_manager
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Spotify Cookie 登录")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("邮箱或用户名:"))
        self._identifier_input = QLineEdit()
        self._identifier_input.setPlaceholderText("user@example.com")
        layout.addWidget(self._identifier_input)
        layout.addWidget(QLabel("Cookie 数据 (JSON):"))
        self._cookie_input = QLineEdit()
        self._cookie_input.setPlaceholderText('{"sp_dc": "..."}')
        layout.addWidget(self._cookie_input)
        extract_row = QHBoxLayout()
        self._browser_combo = QComboBox()
        from fuo_spotify.login import BROWSER_LABELS
        for key, label in BROWSER_LABELS.items():
            self._browser_combo.addItem(label, key)
        extract_row.addWidget(self._browser_combo)
        self._extract_btn = QPushButton("从浏览器提取")
        self._extract_btn.clicked.connect(self._on_extract)
        extract_row.addWidget(self._extract_btn)
        extract_row.addStretch()
        layout.addLayout(extract_row)
        self._login_btn = QPushButton("登录")
        self._login_btn.clicked.connect(self._on_login)
        layout.addWidget(self._login_btn)
        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

    def _on_login(self):
        import json
        identifier = self._identifier_input.text().strip()
        cookie_text = self._cookie_input.text().strip()
        if not identifier:
            self._status_label.setText("请输入邮箱或用户名")
            return
        if not cookie_text:
            self._status_label.setText("请输入 Cookie 数据")
            return
        try:
            cookies = json.loads(cookie_text)
            self._login_manager.login_with_cookies(identifier, cookies)
            self._status_label.setText("登录成功!")
            self.accept()
        except json.JSONDecodeError:
            self._status_label.setText("Cookie 格式错误，请输入有效的 JSON")
        except Exception as e:
            self._status_label.setText(f"登录失败: {e}")

    def _on_extract(self):
        import json
        from fuo_spotify.login import extract_browser_cookies
        browser = self._browser_combo.currentData()
        try:
            self._extract_btn.setEnabled(False)
            self._status_label.setText("正在从浏览器提取 Cookie …")
            cookies = extract_browser_cookies(browser)
            self._cookie_input.setText(json.dumps(cookies))
            self._status_label.setText(
                "已提取，请填写邮箱后点击登录"
            )
        except Exception as e:
            self._status_label.setText(f"提取失败: {e}")
        finally:
            self._extract_btn.setEnabled(True)


class ProviderUI:
    def __init__(self, app, provider):
        self._app = app
        self._provider = provider
        self._dialog = None
        self._login_event = Signal("login_event")

    @property
    def provider(self):
        return self._provider

    @property
    def login_event(self):
        return self._login_event

    def login_or_go_home(self):
        if self.provider._login_manager.is_logged_in:
            # 对齐 bilibili 模式：emit event 2（重新登录）
            # 首次选择 provider 时 current_pvd_ui 为 None，handler 会刷新
            # 后续点击 avatar 时 current_pvd_ui 已设置，handler 会跳过
            self._login_event.emit(self, 2)
            return
        self._show_login_dialog()

    def register_pages(self, route):
        pass

    def get_colorful_svg(self) -> str:
        from pathlib import Path
        return str(Path(__file__).parent / 'icons' / 'spotify.svg')

    def _show_login_dialog(self):
        if self._dialog is None:
            self._dialog = LoginDialog(self.provider._login_manager, self._app)
            self._dialog.accepted.connect(self._on_login_accepted)
        self._dialog.show()

    def _on_login_accepted(self):
        from fuo_spotify.api import SpotifyApi

        login = self.provider._login_manager.login
        if login is None:
            return
        api = SpotifyApi(login)
        self._provider.set_api(api)
        try:
            user = self._provider.user_info()
            # 直接设置用户，不触发 current_user_changed 信号
            # （避免与 login_event 重复刷新播放列表）
            self._provider._user = user
            logger.info(f"Spotify user logged in: {user.name}")
        except Exception as e:
            logger.warning(f"Get user info failed: {e}")
        # emit login_event → 框架的 on_provider_ui_login_event 刷新播放列表
        self._login_event.emit(self, 1)

    def get_status_text(self):
        if self.provider._login_manager.is_logged_in:
            user = self._provider.get_current_user()
            if user:
                return f"Spotify: {user.name}"
            return "Spotify: 已连接"
        return "Spotify: 未登录"
