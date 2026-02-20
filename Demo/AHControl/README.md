# Motor control node

The motor configuration is set in a TOML file (cf. [r_hand.toml](config/r_hand.toml)).
In this file you can set the motors ID, and angle offsets for each finger.

# Tools
- *change_id*: to help you change the id of a motor. `cargo run --bin=change_id -- -h` for a list of parameters
- *goto*: to move a single motor to a given position. `cargo run --bin=goto -- -h` for a list of parameters
- *get_zeros*: to help you set the motor zeros, it sets the motors in the compliant mode and write the TOML file to the console. `cargo run --bin=get_zeros -- -h` for a list of parameters
- *set_zeros*: to move the hand in the "zero" position according to the config file. `cargo run --bin=set_zeros -- -h` for a list of parameters

# Calibration steps

1. Verify IDs: run `set_zeros` or `goto` per motor; if the wrong finger moves, the ID in config does not match the physical motor. Fix with `change_id`, or use [Feetech debug tool](https://github.com/Robot-Maker-SAS/FeetechServo/tree/main/feetech%20debug%20tool%20master/FD1.9.8.2) to scan the bus.

- Expected result for `set_zeros`: the hand moves all fingers to their zero pose (from config offsets), holds ~1 second, then relaxes (torque off). If the wrong finger moves for a given config entry, the motor IDs are mismatched.

2. Calibrate offsets: run `get_zeros`. Put motors in compliant mode, manually position each finger to its zero pose, press Enter. Copy the printed TOML into your config file (e.g. `Demo/AHControl/config/r_hand_julia.toml`).

# Commands

Run from the project root. If you use pixi for Rust, run `pixi shell` first so `cargo` is in PATH. Set `PORT` to your serial device (e.g. `/dev/ttyACM0` on Linux, `COM3` on Windows). Set `CONFIG_PREFIX` to your config name (e.g. `team_julia`, `team_krishan`); the config file is `Demo/AHControl/config/r_hand_${CONFIG_PREFIX}.toml`. Copy `r_hand.toml` to `r_hand_<prefix>.toml` if needed.

Linux:

```bash
export PORT=/dev/ttyACM0
export CONFIG_PREFIX="team_julia"
export CFG="Demo/AHControl/config/r_hand_${CONFIG_PREFIX}.toml"
cargo run --manifest-path Demo/Cargo.toml --bin=set_zeros -- --serialport $PORT --config $CFG
cargo run --manifest-path Demo/Cargo.toml --bin=goto -- --serialport $PORT --id 1 --pos 0.0
cargo run --manifest-path Demo/Cargo.toml --bin=change_id -- --serialport $PORT --old-id 1 --new-id 2
cargo run --manifest-path Demo/Cargo.toml --bin=get_zeros -- --serialport $PORT --config $CFG
```

Windows (PowerShell):

```powershell
$PORT = "COM3"
$CONFIG_PREFIX = "team_krishan"
$CFG = "Demo/AHControl/config/r_hand_$CONFIG_PREFIX.toml"
cargo run --manifest-path Demo/Cargo.toml --bin=set_zeros -- --serialport $PORT --config $CFG
cargo run --manifest-path Demo/Cargo.toml --bin=goto -- --serialport $PORT --id 1 --pos 0.0
cargo run --manifest-path Demo/Cargo.toml --bin=change_id -- --serialport $PORT --old-id 1 --new-id 2
cargo run --manifest-path Demo/Cargo.toml --bin=get_zeros -- --serialport $PORT --config $CFG
```
