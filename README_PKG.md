# amazinghand

Python SDK for Amazing Hand robotic hand (Pollen Robotics). Control the hand via named poses and raw angles.

## Install

```bash
pip install amazinghand
```

## Quick start

```python
from amazinghand import AmazingHand, list_poses

print("Available poses:", list_poses())
hand = AmazingHand(profile="default")
hand.apply_pose("rock")
hand.apply_pose("paper")
hand.apply_pose("scissors")
```

## Configuration

Set `AMAZINGHAND_CONFIG` to your config directory, or place config under `~/.config/amazinghand` (Linux) / `%LOCALAPPDATA%\amazinghand` (Windows).

Config resolution order:

1. `AMAZINGHAND_CONFIG` env
2. `config_root` argument to `AmazingHand()`
3. Repo config when running from source
4. User config dir
5. Bundled config (pip-installed)

Environment variables:

- `AMAZINGHAND_CONFIG`: path to directory with `profiles.toml` and `calibration/`
- `AMAZINGHAND_PROFILE`: profile name (default: `default`)

To add a calibration: copy `calibration/right_hand.toml` to your file, fill in servo IDs and `rest_deg`, add a profile in `profiles.toml`, and reference it via `right_hand_calibration` / `left_hand_calibration`.

## License

Apache 2.0
