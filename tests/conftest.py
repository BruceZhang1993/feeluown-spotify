import sys
from unittest.mock import MagicMock

import pytest

# spotapi 包的 saver.py 在顶层无条件导入 pymongo/redis/readerwriterlock，
# 但这些并非本项目的直接依赖，且 spotapi 未正确声明它们。
# 在测试模块加载前将 spotapi 注入 sys.modules，避免触发有问题的导入链。
_spotapi_mock = MagicMock()
for _submod in [
    "spotapi",
    "spotapi.artist",
    "spotapi.client",
    "spotapi.song",
    "spotapi.album",
    "spotapi.playlist",
    "spotapi.user",
    "spotapi.login",
    "spotapi.config",
    "spotapi.types",
    "spotapi.types.interfaces",
    "spotapi.utils",
    "spotapi.utils.logger",
    "spotapi.utils.saver",
    "spotapi.utils.strings",
    "spotapi.exceptions",
]:
    sys.modules.setdefault(_submod, MagicMock())


@pytest.fixture
def mock_app():
    app = MagicMock()
    app.mode = 0
    app.GuiMode = 1
    return app
