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
REPO_CONFIG = EXAMPLE_ROOT.parent / "config"


class TestCanonicalConfigStructure(unittest.TestCase):
    """Check config/profiles.toml and config/calibration/ exist and have expected layout."""

    def test_config_dir_exists(self):
        self.assertTrue(REPO_CONFIG.is_dir(), f"config/ not found at {REPO_CONFIG}")

    def test_profiles_toml_exists(self):
        path = REPO_CONFIG / "profiles.toml"
        self.assertTrue(path.exists(), f"profiles.toml not found at {path}")

    def test_profiles_have_expected_sections(self):
        if sys.version_info < (3, 11):
            self.skipTest("tomllib requires Python 3.11+")
        import tomllib
        path = REPO_CONFIG / "profiles.toml"
        if not path.exists():
            self.skipTest("profiles.toml not found")
        with open(path, "rb") as f:
            data = tomllib.load(f)
        profile = data.get("profile", {})
        self.assertIn("team_julia", profile, "profile.team_julia required")
        self.assertIn("team_krishan", profile, "profile.team_krishan required")

    def test_profiles_have_connection_and_calibration(self):
        if sys.version_info < (3, 11):
            self.skipTest("tomllib requires Python 3.11+")
        import tomllib
        path = REPO_CONFIG / "profiles.toml"
        if not path.exists():
            self.skipTest("profiles.toml not found")
        with open(path, "rb") as f:
            data = tomllib.load(f)
        for name in ("team_julia", "team_krishan"):
            section = data.get("profile", {}).get(name, {})
            self.assertIn("port", section, f"{name} missing port")
            self.assertIn("baudrate", section, f"{name} missing baudrate")
            self.assertIn("timeout", section, f"{name} missing timeout")
            self.assertIn("right_hand_calibration", section, f"{name} missing right_hand_calibration")

    def test_team_julia_calibration_file_exists(self):
        """Profile team_julia references a calibration file that must exist."""
        if sys.version_info < (3, 11):
            self.skipTest("tomllib requires Python 3.11+")
        import tomllib
        path = REPO_CONFIG / "profiles.toml"
        if not path.exists():
            self.skipTest("profiles.toml not found")
        with open(path, "rb") as f:
            data = tomllib.load(f)
        cal = data.get("profile", {}).get("team_julia", {}).get("right_hand_calibration", "")
        if not cal:
            self.skipTest("team_julia has no right_hand_calibration")
        cal_path = REPO_CONFIG / "calibration" / f"{cal}.toml"
        self.assertTrue(cal_path.exists(), f"Calibration file {cal_path} not found")

    def test_calibration_has_hand_1_keys_for_demo(self):
        """Canonical load for team_julia must yield hand_1_* so get_demo_hand_config(side=1) works."""
        if not (REPO_CONFIG / "profiles.toml").exists():
            self.skipTest("profiles.toml not found")
        import common
        cfg = common.load_config(profile="team_julia", config_root=REPO_CONFIG)
        for name in ("index", "middle", "ring", "thumb"):
            self.assertIn(f"hand_1_{name}_servo_ids", cfg, f"hand_1_{name}_servo_ids missing")
            self.assertIn(f"hand_1_{name}_middle_pos", cfg, f"hand_1_{name}_middle_pos missing")
