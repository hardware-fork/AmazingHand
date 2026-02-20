# Example control for the Pollen Robotics "AmazingHand" (a.k.a. AH!)

## Running with pixi

Prerequisites: install [Pixi](https://pixi.prefix.dev/latest/installation/). Rust is needed for real hardware demos (AHControl).

From the AmazingHand repository root:

```bash
pixi install
pixi run dora up   # start daemon (in a separate terminal)
```

Webcam hand tracking (simulation only):

```bash
pixi run dora build Demo/dataflow_tracking_simu.yml   # once
pixi run dora run Demo/dataflow_tracking_simu.yml
```

Webcam hand tracking (real hardware):

```bash
pixi run dora build Demo/dataflow_tracking_real.yml   # once
pixi run dora run Demo/dataflow_tracking_real_team_julia.yml
```

The config file is set in `Demo/dataflow_tracking_real.yml` (hand_controller `args`: change `--config AHControl/config/...` and `--serialport` as needed).

Linux: add your user to the `dialout` group for serial port access: `sudo usermod -a -G dialout $USER` (log out and back in). If your hand is on a different port (e.g. `/dev/ttyUSB0`), edit `Demo/dataflow_tracking_real.yml` and change the `--serialport` arg.

Finger angle control (simulation):

```bash
pixi run dora build Demo/dataflow_angle_simu.yml   # once
pixi run dora run Demo/dataflow_angle_simu.yml
```

The dataflow `build` steps install HandTracking and AHSimulation in editable mode and build AHControl when needed.

## How to use (uv):
- Install Rust: https://www.rust-lang.org/tools/install
- Install uv: https://docs.astral.sh/uv/getting-started/installation/
- Install dora-rs: https://dora-rs.ai/docs/guides/Installation/installing
  - start the daemon: `dora up`

- Clone this repository and in a console from the directory run:
- `uv venv --python 3.12`
- To run the webcam hand tracking demo in simulation only:
  - `dora build dataflow_tracking_simu.yml --uv` (needs to be done only once)
  - `dora run dataflow_tracking_simu.yml --uv`
- To run the webcam hand tracking demo with real hardware:
  - `dora build dataflow_tracking_real.yml --uv` (needs to be done only once)
  - `dora run dataflow_tracking_real.yml --uv`
- To run a simple example to control the finger angles in simulation:
  - `dora build dataflow_angle_simu.yml --uv` (needs to be done only once)
  - `dora run dataflow_angle_simu.yml --uv`


## Hand Setup

![Motors naming](docs/finger.png "Motors naming for each finger")

![Fingers naming](docs/r_hand.png "Fingers naming for each hand")

Be sure to adapt the configuration file [r_hand.toml](AHControl/config/r_hand.toml) for your particular hand.
You can use the software tools located in [AHControl](AHControl).


## Details

- [AHControl](AHControl) contains a dora-rs node to control the motors, along with some useful tools to configure them.
- [AHSimulation](AHSimulation) contains a dora-rs node to simulate the hand and get the inverse kinematics.
- [HandTracking](HandTracking) contains a dora-rs node to track hands from a webcam and use it as target to control AH!.

