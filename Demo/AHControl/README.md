# Motor control node

Use canonical calibration from the repo `config/calibration/` (recommended): e.g. `--config ../../config/calibration/r_hand_team_julia.toml` when running from Demo/AHControl. See [canonical_hand_config_design.md](../../docs/canonical_hand_config_design.md). Finger order is read from `config/hand_geometry.toml` when using a calibration file under `config/calibration/`. Alternatively, a legacy TOML under AHControl `config/` (e.g. [r_hand.toml](config/r_hand.toml)) is still supported for motor IDs and angle offsets.

# Tools
- *change_id*: to help you change the id of a motor. `cargo run --bin=change_id -- -h` for a list of parameters
- *goto*: to move a single motor to a given position. `cargo run --bin=goto -- -h` for a list of parameters
- *get_zeros*: to help you set the motor zeros, it sets the motors in the compliant mode and write the TOML file to the console. `cargo run --bin=get_zeros -- -h` for a list of parameters
- *set_zeros*: to move the hand in the "zero" position according to the config file. `cargo run --bin=set_zeros -- -h` for a list of parameters

# Calibration

Full procedure (verify IDs, create calibration file, get_zeros, set_zeros, run with profile) is in [docs/canonical_hand_config_design.md](../../docs/canonical_hand_config_design.md) under "Calibration procedures".

# Commands

Run from the project root. If you use pixi for Rust, run `pixi shell` first. Set `PORT` to your serial device (e.g. `/dev/ttyACM0` on Linux, `COM3` on Windows). For canonical calibration use a file under `config/calibration/` (e.g. `config/calibration/r_hand_team_julia.toml`).

Linux:

```bash
export PORT=/dev/ttyACM0
export CFG="config/calibration/r_hand_team_julia.toml"
cargo run --manifest-path Demo/Cargo.toml --bin=set_zeros -- --serialport $PORT --config $CFG
cargo run --manifest-path Demo/Cargo.toml --bin=goto -- --serialport $PORT --id 1 --pos 0.0
cargo run --manifest-path Demo/Cargo.toml --bin=change_id -- --serialport $PORT --old-id 1 --new-id 2
cargo run --manifest-path Demo/Cargo.toml --bin=get_zeros -- --serialport $PORT --config $CFG
```

Windows (PowerShell):

```powershell
$PORT = "COM3"
$CFG = "config/calibration/r_hand_team_krishan.toml"
cargo run --manifest-path Demo/Cargo.toml --bin=set_zeros -- --serialport $PORT --config $CFG
cargo run --manifest-path Demo/Cargo.toml --bin=goto -- --serialport $PORT --id 1 --pos 0.0
cargo run --manifest-path Demo/Cargo.toml --bin=change_id -- --serialport $PORT --old-id 1 --new-id 2
cargo run --manifest-path Demo/Cargo.toml --bin=get_zeros -- --serialport $PORT --config $CFG
```
