# Python Examples

Tutorial for settings IDs with Feetech Software, and Serial bus driver : [https://www.robot-maker.com/forum/tutorials/article/168-brancher-et-controler-le-servomoteur-feetech-sts3032-360/]


Use Feetech software to set IDs : [https://github.com/Robot-Maker-SAS/FeetechServo/tree/main/feetech%20debug%20tool%20master/FD1.9.8.2)]

## Setup Environment

**Install pixi** (if not already installed):

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

Restart your shell or run `source ~/.bashrc` (or the equivalent for your shell) so the `pixi` command is available.

**With pixi (recommended)**
From the repository root (where `pixi.toml` lives):

```bash
pixi install   # one time setup
# Optional: export AMAZINGHAND_PROFILE=team_julia
pixi run python PythonExample/AmazingHand_FingerTest.py
```

To run another script, replace the filename, e.g. `PythonExample/AmazingHand_Hand_FingerMiddlePos.py` or `PythonExample/AmazingHand_Demo.py`.

Set `AMAZINGHAND_PROFILE` to choose a profile (e.g. `team_julia`, `team_krishan`). Profiles and hand calibration live in `config/profiles.toml` and `config/calibration/`; see [canonical_hand_config_design.md](../docs/canonical_hand_config_design.md). The hand must be connected via USB; the profile's `port` must match your system (e.g. `COM3` on Windows, `/dev/ttyACM0` on Linux). If the port is wrong or the device is unplugged, the script will fail with "No such file or directory".

## Run Python Examples

### Hand Demo

Runs a loop of gestures (open/close, spread, point, victory, etc.) on one hand. Which hand is controlled by the profile's `hand_test_id` or `side`, or override with `--side`:

```bash
# export AMAZINGHAND_PROFILE=team_julia
pixi run python PythonExample/AmazingHand_Demo.py
# Right hand (1) or left hand (2):
pixi run python PythonExample/AmazingHand_Demo.py --side 1
```

Set `AMAZINGHAND_PROFILE` (e.g. `team_julia`); the profile loads servo IDs and rest/middle positions from `config/calibration/`. See [canonical_hand_config_design.md](../docs/canonical_hand_config_design.md).

## Run Unit Tests

From the repository root:

```bash
pixi run test-demo
```

## Pre-commit (optional)

To run lint and tests before each commit, install the git hooks:

```bash
pixi run pre-commit install
```

Hooks are limited to `PythonExample/`. Run manually with `pixi run pre-commit run --all-files`.
