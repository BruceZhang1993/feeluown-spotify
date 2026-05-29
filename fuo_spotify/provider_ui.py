# fuo_spotify/provider_ui.py
import logging
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QWidget,
)

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    def __init__(self, login_manager, parent=None):
        super().__init__(parent)
        self._login_manager = login_manager
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Spotify 登录")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # 密码登录 Tab
        password_tab = QWidget()
        password_layout = QVBoxLayout(password_tab)
        password_layout.addWidget(QLabel("用户名/邮箱:"))
        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("your@email.com")
        password_layout.addWidget(self._username_input)
        password_layout.addWidget(QLabel("密码:"))
        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self._password_input)
        self._login_btn = QPushButton("登录")
        self._login_btn.clicked.connect(self._on_login)
        password_layout.addWidget(self._login_btn)
        tabs.addTab(password_tab, "密码登录")

        # Cookie 登录 Tab
        cookie_tab = QWidget()
        cookie_layout = QVBoxLayout(cookie_tab)
        cookie_layout.addWidget(QLabel("Cookie 数据 (JSON):"))
        self._cookie_input = QLineEdit()
        self._cookie_input.setPlaceholderText('{"session": "..."}')
        cookie_layout.addWidget(self._cookie_input)
        self._cookie_login_btn = QPushButton("使用 Cookie 登录")
        self._cookie_login_btn.clicked.connect(self._on_cookie_login)
        cookie_layout.addWidget(self._cookie_login_btn)
        tabs.addTab(cookie_tab, "Cookie 登录")

        layout.addWidget(tabs)
        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

    def _on_login(self):
        username = self._username_input.text().strip()
        password = self._password_input.text().strip()
        if not username or not password:
            self._status_label.setText("请输入用户名和密码")
            return
        try:
            self._login_manager.login_with_password(username, password)
            self._status_label.setText("登录成功!")
            self.accept()
        except Exception as e:
            self._status_label.setText(f"登录失败: {e}")

    def _on_cookie_login(self):
        import json
        cookie_text = self._cookie_input.text().strip()
        if not cookie_text:
            self._status_label.setText("请输入 Cookie 数据")
            return
        try:
            cookies = json.loads(cookie_text)
            self._login_manager.login_with_cookies(cookies)
            self._status_label.setText("登录成功!")
            self.accept()
        except json.JSONDecodeError:
            self._status_label.setText("Cookie 格式错误，请输入有效的 JSON")
        except Exception as e:
            self._status_label.setText(f"登录失败: {e}")


class ProviderUI:
    def __init__(self, app, login_manager, provider):
        self._app = app
        self._login_manager = login_manager
        self._provider = provider
        self._dialog = None

    @property
    def provider(self):
        return self._provider

    def register_pages(self, route):
        pass

    def show_login_dialog(self):
        if self._dialog is None:
            self._dialog = LoginDialog(self._login_manager, self._app)
        self._dialog.show()

    def get_status_text(self):
        if self._login_manager.is_logged_in:
            user = self._provider.get_current_user()
            if user:
                return f"Spotify: {user.name}"
            return "Spotify: 已连接"
        return "Spotify: 未登录"
