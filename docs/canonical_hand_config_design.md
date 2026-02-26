# Canonical Hand Configuration Design (Proposal)

A single source of truth for hand configuration.

## Problem

- Hand config (servo IDs, rest/middle positions, offsets) lives in two places: Demo/AHControl (e.g. `r_hand.toml`) and hardcoded in PythonExample. Values can drift.
- Servo IDs are only known after assembly and testing, so assignment is per physical hand.
- There is no support for multiple setups (e.g. team_julia, team_krishan).

## Goals

- One canonical definition per logical hand (right, left) so AHControl, PythonExample, and others read the same data.
- Support multiple profiles (connection + which hands) without duplicating hand geometry.
- Use logical roles everywhere; physical servo IDs only in per-physical-hand calibration files.

## Proposed Structure

1. Logical roles

The hand is defined by a fixed set of logical roles (e.g. index_m0, index_m1, middle_m0, middle_m1, ring_m0, ring_m1, thumb_m0, thumb_m1). Application code and shared config refer only to these roles. Physical servo IDs appear only in calibration files.

2. Shared hand geometry (one source of truth)

One file defines the structure common to both hands: which roles exist (finger order). Geometry is identical for right and left, so one file suffices. No physical servo IDs. Implemented as `config/hand_geometry.toml` (key `fingers = ["index", "middle", "ring", "thumb"]`). AHControl and the Python canonical adapter read it; rest positions stay in per-physical-hand calibration.

3. Per-physical-hand calibration

After assembly and testing, one small file (or section) per physical hand contains only:
- Mapping: logical role → physical servo ID
- Rest/middle position or offset per role

Rust (radians) and Python (degrees) can derive units from this single rest value at load time or via a thin adapter.

4. Named profiles

A main config (e.g. for PythonExample and/or launchers) uses named profiles (e.g. `[profile.team_julia]`, `[profile.team_krishan]`) that specify only:
- Connection: port, baudrate, timeout, etc.
- Which physical hand calibration to use for right and left (e.g. by file name or id)
- Demo-specific options (side, hand_test_id, speeds, etc.)

Select the active profile by env var, CLI flag, or a key like `active_profile = "team_krishan"`.

## Layout

- Format and location: TOML. Single file `config/hand_geometry.toml` (key `fingers`); calibration under `config/calibration/`; profiles in `config/profiles.toml`.
- Naming: use anatomical role names (index, middle, ring, thumb) in the canonical config and in application-facing APIs. Each stack keeps internal names (e.g. r_finger1) only inside adapters that map from canonical roles.
- Loader strategy: small adapters in AHControl and PythonExample. Each adapter reads the canonical TOML (shared geometry + chosen calibration) and emits the shape that stack expects; no shared cross-language loader initially. AHControl resolves the geometry path from the calibration file path (e.g. `config/calibration/foo.toml` → `config/hand_geometry.toml`), so no fixed paths and it works for any user or clone.

- `config/hand_geometry.toml`: shared hand geometry (finger order for both hands); no IDs.
- `config/calibration/`: one file per physical hand (e.g. `r_hand_team_julia.toml`, `l_hand_team_krishan.toml`) containing role → id and rest/middle per role.
- `config/profiles.toml`: profiles that reference calibration files and set connection/demo options.

AHControl loads shared hand geometry plus the chosen calibration file(s). PythonExample does the same. Both resolve logical roles to IDs at load time.

## Calibration procedures

Zero, rest, and middle position all refer to the same thing: the reference pose you choose for each joint. In calibration TOML this is stored as `rest_deg` per finger; in Python demos it appears as `middle_pos`. The canonical adapter maps `rest_deg` to `hand_*_*_middle_pos` so there is a single source of truth.

get_zeros (AHControl binary): Used after assembly to record the current physical pose as the reference. Connect the hand, run with the chosen calibration file (e.g. `config/calibration/r_hand_team_julia.toml`). Torque is turned off; you move the hand into the desired zero/rest pose, press Enter, and the tool reads each motor’s present position and overwrites the rest values in memory. It then prints the updated TOML in canonical form (`[index]`, `[middle]`, etc. with `ids` and `rest_deg`). Save that output as the calibration file so that file remains the single source of truth. get_zeros should take a path under `config/calibration/` and resolve geometry from the same config root.

set_zeros (AHControl binary): Moves all motors to the rest pose defined in the given calibration file. Use it to verify or to bring the hand to the same zero pose without manually moving it. It should also use canonical calibration files under `config/calibration/`.

Profiles in `config/profiles.toml` only point at which calibration file to use (`right_hand_calibration`, `left_hand_calibration`). The calibration tools do not need to read profiles; they operate on the calibration file that a profile references. Optionally, profile options like `finger_test_servo_ids` and `finger_test_middle_pos` can be derived from the selected hand’s calibration for one finger to avoid duplicating rest values.

Recommended steps:

0. Verify motor IDs: Run `set_zeros` or `goto` with your calibration file and port. If the wrong finger moves for a given config entry, the ID in the calibration file does not match the physical motor. Fix with the AHControl `change_id` binary, or use the [Feetech debug tool](https://github.com/Robot-Maker-SAS/FeetechServo/tree/main/feetech%20debug%20tool%20master/FD1.9.8.2) to scan the bus. Expected result for `set_zeros`: the hand moves all fingers to their zero pose (from config), holds about 1 second, then relaxes (torque off).

1. Create or copy a calibration file (e.g. `config/calibration/r_hand_team_julia.toml`) with one section per finger: `[index]`, `[middle]`, `[ring]`, `[thumb]`. Each section must have `ids = [id1, id2]` (physical servo IDs for that finger) and `rest_deg = [d1, d2]` (initial values; can be zeros). Use the same port and baudrate as in your profile.

2. get_zeros — record the current physical pose as the reference: From the repo root, run the AHControl get_zeros binary with the calibration file and connection args (e.g. `--config config/calibration/r_hand_team_julia.toml --serialport /dev/ttyACM0`). When the hand goes compliant, move it into the desired zero/rest pose (e.g. open, relaxed), then press Enter. The tool reads each motor position and prints a full canonical TOML. Save the printed TOML into the same calibration file (or a new file under `config/calibration/`), then add or update a profile in `config/profiles.toml` to reference that file.

3. set_zeros — move the hand to the stored rest pose: Run the set_zeros binary with the same calibration file and port/baudrate. The hand moves all joints to the `rest_deg` values in that file. Use this to verify calibration or to reset the hand to zero without moving it by hand.

4. Run demos or AHControl with a profile: set `AMAZINGHAND_PROFILE` (or pass the profile name to your loader) to the profile that references the calibration file you used. PythonExample and AHControl will load that calibration as the single source of truth for IDs and rest/middle positions.

## Alternative: self-contained profiles

Each profile could stay self-contained (hand_1, hand_2, connection in one section) with duplicated geometry. That avoids refactoring to shared geometry and calibration files but keeps two sources of truth and more duplication.
