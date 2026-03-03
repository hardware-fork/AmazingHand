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

"""Amazing Hand SDK - control robotic hand poses and gestures."""

from amazinghand.client import AmazingHand
from amazinghand.config import get_config_root, load_config
from amazinghand.poses import list_poses

__all__ = ["AmazingHand", "load_config", "get_config_root", "list_poses"]
__version__ = "0.1.0"
