# Python Examples

Tutorial for settings IDs with Feetech Software, and Serial bus driver : [https://www.robot-maker.com/forum/tutorials/article/168-brancher-et-controler-le-servomoteur-feetech-sts3032-360/]


Use Feetech software to set IDs : [https://github.com/Robot-Maker-SAS/FeetechServo/tree/main/feetech%20debug%20tool%20master/FD1.9.8.2)]

## Setup Environment

See [DEVELOPMENT.md](../docs/DEVELOPMENT.md) for Pixi installation and full setup. From the repository root (where `pixi.toml` lives), in Git Bash (Windows) or a Unix shell (Linux/macOS):

```bash
pixi install
export AMAZINGHAND_PROFILE=team_julia   # optional
pixi run python PythonExample/AmazingHand_FingerTest.py
```

To run another script, replace the filename, e.g. `PythonExample/AmazingHand_Hand_FingerMiddlePos.py` or `PythonExample/AmazingHand_Demo.py`.

Profiles and hand calibration live in `config/profiles.toml` and `config/calibration/`; see [canonical_hand_config_design.md](../docs/canonical_hand_config_design.md). The hand must be connected via USB; the profile's `port` must match your system (e.g. `COM3` on Windows, `/dev/ttyACM0` on Linux). To override the port, edit `config/profiles.toml` and change the `port` key in your profile (e.g. `[profile.team_julia]` has `port = "/dev/ttyACM0"`; on Windows use `port = "COM4"` or whatever your device uses).

- To find the COM port on Windows, run `powershell -c "[System.IO.Ports.SerialPort]::getportnames()"` in Git bash shell.

## Run Python Examples

### Hand Demo

Runs a loop of gestures (open/close, spread, point, victory, etc.) on one hand. Which hand is controlled by the profile's `hand_test_id` or `side`, or override with `--side`:

```bash
pixi run python PythonExample/AmazingHand_Demo.py
pixi run python PythonExample/AmazingHand_Demo.py --side 1   # right (1) or left (2)
```

Set `AMAZINGHAND_PROFILE` first (see Setup). The profile loads servo IDs and rest/middle positions from `config/calibration/`. See [canonical_hand_config_design.md](../docs/canonical_hand_config_design.md).

For unit tests and pre-commit, see [maintainer.md](../docs/maintainer.md).
