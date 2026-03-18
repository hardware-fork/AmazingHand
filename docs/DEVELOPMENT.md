# Development Workflow

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup (Linux and Windows)](#setup-linux-and-windows)
- [Setup (Raspberry Pi)](#setup-raspberry-pi)
- [Run Demos](#run-demos)
  - [Start Dora Daemon](#start-dora-daemon)
  - [Run a simple "finger angle" gesture demo in simulation](#run-a-simple-finger-angle-gesture-demo-in-simulation)
  - [Run Python Example](#run-python-example)
  - [Run Demo with Physical Hands](#run-demo-with-physical-hands)
- [Appendix](#appendix)
  - [Install Microsoft Visual C++ (MSVC) Build Tools](#install-microsoft-visual-c-msvc-build-tools)

## Prerequisites

Install the following tools:

- Install Pixi: https://pixi.prefix.dev/latest/installation/. 
  - On Windows, to use pixi in Git Bash, add `export PATH="$HOME/.pixi/bin:$PATH"` to `~/.bashrc`, then run `source ~/.bashrc`.
  - Verify installation: `pixi --version`
- Rust and cargo are installed via pixi (included in `pixi.toml`).

## Setup (Linux and Windows)

On regular Ubuntu (24.04) or Windows (Windows 11) machine, install the pixi environment (includes all Python dependencies). On Windows, Git Bash is tested.

```bash
# From repository root
pixi install
```

Optionally, verify the installation by running unit tests:

```bash
pixi run test-python-example 
pixi run test-demo
pixi run test-ahcontrol
```

Windows only (Rust / test-ahcontrol): `pixi.toml` adds `vs2022_win-64` for win-64, which activates the MSVC toolchain (via vcvars64) when you run `pixi shell` or `pixi run`. You must have Visual Studio or Build Tools installed first (see Appendix). If you get a linker error (e.g. "extra operand", "link.exe not found"), install Build Tools per the Appendix, then run `pixi install` to refresh the environment. As a fallback, run `pixi run test-ahcontrol` from "x64 Native Tools Command Prompt for VS" (Start menu).

## Setup (Raspberry Pi)
Raspberry Pi support is experimental and focuses on the haptic/tactile demos.

On Raspberry Pi OS (Debian-based), install system GPIO dependencies first:

```bash
sudo apt-get update
sudo apt-get install liblgpio-dev
```

Then create the pixi environment from the repository root:

```bash
pixi install
```

You can now run the haptic/tactile sensor test (from the repo root):

```bash
pixi run python -m Demo.Sensors.haptic_test
```

## Run Demos

Tested on Ubuntu 24.04 and Windows 11 (Git Bash).

### Start Dora Daemon

Start the dora daemon using pixi:

```bash
pixi run dora up
```

### Run a simple "finger angle" gesture demo in simulation

This runs `AHSimulation/examples/finger_angle_control.py` and streams targets into the MuJoCo viewer nodes. From the repository root:

```bash
pixi run dora-build-angle-simu   # once
pixi run dora-run-angle-simu
```

Note: Dora/MuJoCo demos are tested on Linux and Windows. 

Start an interactive shell in the pixi environment:
```bash
pixi shell
```
### Run Python Example

See [PythonExample/README.md](../PythonExample/README.md).

### Run Demo with Physical Hands

See [Demo/README.md](../Demo/README.md). On Linux, add your user to the `dialout` group for serial port access. On Windows, edit the dataflow YAML for the COM port and `AHControl.exe` path.

## Appendix

### Install Microsoft Visual C++ (MSVC) Build Tools

Required for building the Rust crate (`test-ahcontrol`) on Windows. The `vs2022_win-64` package in `pixi.toml` activates this toolchain automatically; you must install Build Tools first. Download and install:

1. Download the Build Tools installer from: https://visualstudio.microsoft.com/visual-cpp-build-tools (or direct: https://aka.ms/vs/17/release/vs_BuildTools.exe).

2. Run `vs_BuildTools.exe`. If the Visual Studio Installer is not installed, it will install first.

3. In the installer, select the workload "Desktop development with C++". This includes the MSVC compiler, linker (`link.exe`), and Windows SDK.

4. On the right-hand "Installation details" panel, ensure "MSVC v143 - VS 2022 C++ x64/x86 build tools" and "Windows 10/11 SDK" (or similar) are checked. Click Install.

5. After installation, run `pixi install` (if needed) and `pixi run test-ahcontrol`. The `vs2022_win-64` package locates your install via vswhere and runs vcvars64 so the correct linker is on PATH.

