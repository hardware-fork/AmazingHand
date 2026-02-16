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

import sys
import unittest
from pathlib import Path

EXAMPLE_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = EXAMPLE_ROOT / "config.toml"


class TestConfigStructure(unittest.TestCase):
    """Check config.toml exists and has expected team sections and serial keys."""

    def test_config_file_exists(self):
        self.assertTrue(CONFIG_PATH.exists(), f"config.toml not found at {CONFIG_PATH}")

    def test_config_has_team_sections(self):
        if sys.version_info < (3, 11):
            self.skipTest("tomllib requires Python 3.11+")
        import tomllib
        with open(CONFIG_PATH, "rb") as f:
            data = tomllib.load(f)
        self.assertIn("team_julia", data)
        self.assertIn("team_krishan", data)

    def test_team_sections_have_serial_keys(self):
        if sys.version_info < (3, 11):
            self.skipTest("tomllib requires Python 3.11+")
        import tomllib
        with open(CONFIG_PATH, "rb") as f:
            data = tomllib.load(f)
        for team in ("team_julia", "team_krishan"):
            section = data[team]
            self.assertIn("port", section, f"{team} missing port")
            self.assertIn("baudrate", section, f"{team} missing baudrate")
            self.assertIn("timeout", section, f"{team} missing timeout")


if __name__ == "__main__":
    unittest.main()
