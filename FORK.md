# Differences from Upstream

See the fork notice in [README.md](README.md). This file documents how this repo differs from [pollen-robotics/AmazingHand](https://github.com/pollen-robotics/AmazingHand).

## Cross-Platform Support (Linux, Windows)

Pixi-based setup; MSVC toolchain for Rust on Windows. See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Canonical Configuration

Shared hand geometry, per-physical-hand calibration, named profiles. See [docs/canonical_hand_config_design.md](docs/canonical_hand_config_design.md).

## AmazingHand SDK

Python package for named poses and raw angles. See [README_PKG.md](README_PKG.md).

## CI

GitHub Actions for lint (pre-commit), SDK, PythonExample, Demo, and AHControl tests. See [.github/workflows/ci.yml](.github/workflows/ci.yml).

## Debug: check-devices

Pixi task `pixi run check-devices` lists webcam indices and serial ports. Use before running demos to verify device paths.

## Tactile Sensing and Haptic Feedback

FSR tactile sensing via the Waveshare ADS1256 24-bit ADC HAT, and PWM-driven haptic feedback via a QYF-740 coin motor. Includes real-time terminal/GUI display, CSV logging, and offline Bokeh visualisation. See [src/amazinghand_sensors/README.md](src/amazinghand_sensors/README.md).

## Other Changes

Pixi for dependency management; unit tests for SDK, PythonExample, Demo, and AHControl; Dora/MuJoCo simulation demos; pre-commit hooks.
