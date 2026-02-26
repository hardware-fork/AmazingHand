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

"""
Regression tests for canonical hand config design.
PythonExample loads hand config from config/profiles.toml and config/calibration/ only.
"""

import sys
import unittest
from pathlib import Path

_EXAMPLE_ROOT = Path(__file__).resolve().parent.parent
if str(_EXAMPLE_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXAMPLE_ROOT))


class TestAdapterOutputContract(unittest.TestCase):
    """Contract for adapter output: any config passed to get_demo_hand_config must have these keys and produce 8 ids, 8 middle_pos."""

    def test_demo_hand_config_expected_keys(self):
        """Document the keys required so an adapter can emit valid config for get_demo_hand_config."""
        from unittest.mock import MagicMock
        sys.modules["rustypot"] = MagicMock()
        sys.modules["rustypot"].Scs0009PyController = MagicMock()
        import common
        required_keys = []
        for name in ("index", "middle", "ring", "thumb"):
            required_keys.append(f"hand_1_{name}_servo_ids")
            required_keys.append(f"hand_1_{name}_middle_pos")
        cfg = {k: [1, 2] if "servo_ids" in k else [0, 0] for k in required_keys}
        cfg["hand_1_index_servo_ids"] = [10, 11]
        cfg["hand_1_index_middle_pos"] = [-1, 1]
        out = common.get_demo_hand_config(cfg, 1)
        self.assertEqual(len(out["servo_ids"]), 8)
        self.assertEqual(len(out["middle_pos"]), 8)
        self.assertEqual(out["servo_ids"][0], 10)
        self.assertEqual(out["servo_ids"][1], 11)
        self.assertEqual(out["middle_pos"][0], -1)
        self.assertEqual(out["middle_pos"][1], 1)


class TestLoadConfigCanonical(unittest.TestCase):
    """Canonical adapter must emit same shape as load_config() for profile.team_julia."""

    def setUp(self):
        from unittest.mock import MagicMock
        if "rustypot" not in sys.modules:
            sys.modules["rustypot"] = MagicMock()
            sys.modules["rustypot"].Scs0009PyController = MagicMock()
        import common as _common
        self.common = _common

    def test_canonical_profile_julia_emits_hand_1_like_legacy(self):
        """load_config_canonical(profile='team_julia') must yield hand_1 servo_ids and middle_pos from calibration."""
        config_root = _EXAMPLE_ROOT.parent / "config"
        if not (config_root / "profiles.toml").exists():
            self.skipTest("canonical config/ not found")
        cfg = self.common.load_config_canonical(profile="team_julia", config_root=config_root)
        out = self.common.get_demo_hand_config(cfg, 1)
        self.assertEqual(out["servo_ids"], [1, 2, 3, 4, 6, 5, 8, 7])
        self.assertEqual(out["middle_pos"], [-2, 0, 1, 2, -3, 8, 8, -8])

    def test_canonical_profile_team_krishan_emits_hand_2(self):
        """load_config_canonical(profile='team_krishan') must yield hand_2 from left calibration."""
        config_root = _EXAMPLE_ROOT.parent / "config"
        if not (config_root / "profiles.toml").exists():
            self.skipTest("canonical config/ not found")
        cfg = self.common.load_config_canonical(profile="team_krishan", config_root=config_root)
        out = self.common.get_demo_hand_config(cfg, 2)
        self.assertEqual(out["servo_ids"], [11, 12, 13, 14, 15, 16, 17, 18])
        self.assertEqual(out["middle_pos"], [3, -3, -1, -10, 5, 2, -7, 3])


if __name__ == "__main__":
    unittest.main()
