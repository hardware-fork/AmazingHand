# Copyright (C) 2026 Julia Jia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Platform-specific config tests using mocks (no Windows CI required)."""

import sys
from unittest.mock import MagicMock, patch

# Mock rustypot before importing amazinghand (client depends on it)
if "rustypot" not in sys.modules:
    sys.modules["rustypot"] = MagicMock()

from amazinghand import config as config_module
from amazinghand.client import _default_port


def test_user_config_dir_windows():
    """_user_config_dir returns LOCALAPPDATA on Windows."""
    mock_os = MagicMock()
    mock_os.name = "nt"
    mock_os.environ.get.side_effect = lambda k, d=None: (
        "C:\\Users\\foo\\AppData\\Local" if k == "LOCALAPPDATA" else d
    )
    mock_os.path.expanduser.return_value = "C:\\Users\\foo"
    with patch.object(config_module, "os", mock_os):
        result = config_module._user_config_dir()
    assert "amazinghand" in str(result)
    assert result.name == "amazinghand"


def test_user_config_dir_windows_fallback():
    """_user_config_dir falls back to expanduser when LOCALAPPDATA unset."""
    mock_os = MagicMock()
    mock_os.name = "nt"
    mock_os.environ.get.side_effect = lambda k, d=None: d
    mock_os.path.expanduser.return_value = "C:\\Users\\bar"
    with patch.object(config_module, "os", mock_os):
        result = config_module._user_config_dir()
    assert "amazinghand" in str(result)
    mock_os.path.expanduser.assert_called_with("~")


def test_user_config_dir_linux():
    """_user_config_dir returns XDG_CONFIG_HOME on Linux."""
    mock_os = MagicMock()
    mock_os.name = "posix"
    mock_os.environ.get.side_effect = lambda k, d=None: (
        "/home/foo/.config" if k == "XDG_CONFIG_HOME" else d
    )
    mock_os.path.expanduser.return_value = "/home/foo/.config"
    with patch.object(config_module, "os", mock_os):
        result = config_module._user_config_dir()
    assert "amazinghand" in str(result)
    assert result.name == "amazinghand"


def test_user_config_dir_linux_fallback():
    """_user_config_dir falls back to ~/.config when XDG_CONFIG_HOME unset."""
    mock_os = MagicMock()
    mock_os.name = "posix"
    mock_os.environ.get.side_effect = lambda k, d=None: d
    mock_os.path.expanduser.return_value = "/home/bar/.config"
    with patch.object(config_module, "os", mock_os):
        result = config_module._user_config_dir()
    assert "amazinghand" in str(result)
    mock_os.path.expanduser.assert_called_with("~/.config")


def test_default_port_windows():
    """_default_port returns COM3 on Windows."""
    with patch("sys.platform", "win32"):
        assert _default_port() == "COM3"


def test_default_port_linux():
    """_default_port returns /dev/ttyUSB0 on Linux."""
    with patch("sys.platform", "linux"):
        assert _default_port() == "/dev/ttyUSB0"


def test_default_port_darwin():
    """_default_port returns /dev/ttyUSB0 on macOS."""
    with patch("sys.platform", "darwin"):
        assert _default_port() == "/dev/ttyUSB0"
