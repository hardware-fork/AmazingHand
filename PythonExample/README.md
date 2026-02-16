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
# Optional: export AMAZINGHAND_TEAM=julia
pixi run python PythonExample/AmazingHand_FingerTest.py
```

To run another script, replace the filename, e.g. `PythonExample/AmazingHand_Hand_FingerMiddlePos.py` or `PythonExample/AmazingHand_Demo.py`.

Set `AMAZINGHAND_TEAM` to choose config (e.g. `export AMAZINGHAND_TEAM=krishan`). Edit `PythonExample/config.toml` for serial port and finger settings.

The hand must be connected via USB and the serial port in `config.toml` must match your system (e.g. `COM3` on Windows, `/dev/ttyUSB0` or `/dev/ttyACM0` on Linux). Leave `port = ""` to use the default for your OS. If the port is wrong or the device is unplugged, the script will fail with "No such file or directory".

## Run Python Examples

### Hand Demo

Runs a loop of gestures (open/close, spread, point, victory, etc.) on one hand. Which hand is controlled by config (`hand_test_id` or `side` in `config.toml`) or by `AMAZINGHAND_TEAM`. Override from the command line with `--side`:

```bash
pixi run python PythonExample/AmazingHand_Demo.py
# Right hand (1) or left hand (2):
pixi run python PythonExample/AmazingHand_Demo.py --side 1
```

Ensure the chosen hand's servo IDs and middle positions are set in `config.toml` for your team (see `hand_1_*` / `hand_2_*`).

## Run Unit Tests

From the repository root:

```bash
pixi run test
```

## Pre-commit (optional)

To run lint and tests before each commit, install the git hooks:

```bash
pixi run pre-commit install
```

Hooks are limited to `PythonExample/`. Run manually with `pixi run pre-commit run --all-files`.
