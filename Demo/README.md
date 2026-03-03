# Example control for the Pollen Robotics "AmazingHand" (a.k.a. AH!)

## Running with pixi

Prerequisites: install [Pixi](https://pixi.prefix.dev/latest/installation/). Rust is needed for real hardware demos (AHControl). Before running real hardware demos, check the serial port in the dataflow YAML: the default is Linux (`/dev/ttyACM0`); on Windows use your COM port (e.g. `COM3`). Run `pixi run check-devices` to list webcam indices and serial ports.

From the AmazingHand repository root (Git Bash on Windows, or a Unix shell on Linux/macOS):

```bash
pixi install
pixi run dora up   # start daemon (in a separate terminal)
```

Webcam hand tracking (simulation only):

```bash
pixi run dora build Demo/dataflow_tracking_simu.yml   # once
pixi run dora run Demo/dataflow_tracking_simu.yml
```

Webcam hand tracking (real hardware, new config):

```bash
pixi run dora build Demo/dataflow_tracking_real_team_julia.yml   # once
pixi run dora run Demo/dataflow_tracking_real_team_julia.yml
```

Same demo using previous config

```bash
pixi run dora build Demo/dataflow_tracking_real.yml   # once
pixi run dora run Demo/dataflow_tracking_real.yml
```

The hand config is set in the dataflow YAML (hand_controller `args`): change `--config` and `--serialport` as needed. You can use a legacy file under `AHControl/config/r_hand*.toml` or the repo canonical calibration (e.g. `--config config/calibration/r_hand_team_julia.toml` when running from repo root). See [AHControl](AHControl/README.md) and [canonical_hand_config_design.md](../docs/canonical_hand_config_design.md) for details.

Linux: add your user to the `dialout` group for serial port access: `sudo usermod -a -G dialout $USER` (log out and back in). If your hand is on a different port (e.g. `/dev/ttyUSB0`), edit the dataflow YAML and change the `--serialport` arg.

Windows: before running real hardware demos, edit the dataflow YAML (`dataflow_tracking_real.yml`, `dataflow_tracking_real_team_julia.yml`, or `dataflow_tracking_real_2hands.yml`): set `path` to `target/debug/AHControl.exe` (not `AHControl`), and change `--serialport` to your COM port (e.g. `COM3`). Run `pixi run build-ahcontrol` first to build the binary. To find your COM port: `powershell -c "[System.IO.Ports.SerialPort]::getportnames()"` in Git Bash or PowerShell. Use Git Bash or a shell where pixi is available (see [DEVELOPMENT.md](../docs/DEVELOPMENT.md)).

Finger angle control (simulation):

```bash
pixi run dora build Demo/dataflow_angle_simu.yml   # once
pixi run dora run Demo/dataflow_angle_simu.yml
```

The dataflow `build` steps install HandTracking and AHSimulation in editable mode and build AHControl when needed.

## How to use (uv)

Install [Rust](https://www.rust-lang.org/tools/install), [uv](https://docs.astral.sh/uv/getting-started/installation/), and [dora-rs](https://dora-rs.ai/docs/guides/Installation/installing). Clone the repository, start the daemon (`dora up`), and from the Demo directory run:
- `uv venv --python 3.12`
- To run the webcam hand tracking demo in simulation only:
  - `dora build dataflow_tracking_simu.yml --uv` (needs to be done only once)
  - `dora run dataflow_tracking_simu.yml --uv`
- To run the webcam hand tracking demo with real hardware:
  - `dora build dataflow_tracking_real.yml --uv` (needs to be done only once)
  - `dora run dataflow_tracking_real.yml --uv`
  - On Windows: edit the dataflow YAML for `path` (use `AHControl.exe`) and `--serialport` (use your COM port) as in the pixi section above.
- To run a simple example to control the finger angles in simulation:
  - `dora build dataflow_angle_simu.yml --uv` (needs to be done only once)
  - `dora run dataflow_angle_simu.yml --uv`


## Hand Setup

![Motors naming](docs/finger.png "Motors naming for each finger")

![Fingers naming](docs/r_hand.png "Fingers naming for each hand")

Adapt the hand configuration for your setup: either the legacy [r_hand.toml](AHControl/config/r_hand.toml) (and copies like `r_hand_team_julia.toml`) under AHControl/config, or the repo canonical calibration files under `config/calibration/` (see [canonical_hand_config_design.md](../docs/canonical_hand_config_design.md)). Use the tools in [AHControl](AHControl) to calibrate.


## Details

- [AHControl](AHControl) contains a dora-rs node to control the motors, along with some useful tools to configure them.
- [AHSimulation](AHSimulation) contains a dora-rs node to simulate the hand and get the inverse kinematics.
- [HandTracking](HandTracking) contains a dora-rs node to track hands from a webcam and use it as target to control AH!.

