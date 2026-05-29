import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_app():
    app = MagicMock()
    app.mode = 0
    app.GuiMode = 1
    return app
