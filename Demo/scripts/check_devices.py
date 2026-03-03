#!/usr/bin/env python3
# Copyright (C) 2026 Julia Jia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Check webcam indices and serial ports. Run before demos to verify devices."""

import os
import sys

_MAX_CAMERA_PROBE = 3


def check_webcams():
    """Probe camera indices 0..N and report which open successfully."""
    try:
        import cv2
    except ImportError:
        print("Webcam: opencv-python not installed (pip install opencv-python)")
        return
    available = []
    devnull = os.open(os.devnull, os.O_WRONLY)
    stderr_fd = os.dup(2)
    try:
        os.dup2(devnull, 2)
        for i in range(_MAX_CAMERA_PROBE):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                available.append((i, w, h))
                cap.release()
    finally:
        os.dup2(stderr_fd, 2)
        os.close(stderr_fd)
        os.close(devnull)
    if available:
        print("Webcam indices:")
        for idx, w, h in available:
            print(f"  {idx}: {w}x{h}")
        print("  Use index 0 in HandTracking unless you have multiple cameras.")
        if len(available) >= 2:
            print("  Note: indices 0 and 1 may be the same camera (Linux exposes multiple /dev/video* nodes). Try 0 first; if wrong, try 1.")
    else:
        print(f"Webcam: no cameras found (indices 0..{_MAX_CAMERA_PROBE - 1})")


def _is_usb_port(device):
    """Prefer USB serial devices (hand controller) over built-in ttyS."""
    d = device.upper()
    return "ACM" in d or "USB" in d or d.startswith("COM")


def _port_status(device):
    """Try opening port. Return 'available', 'in_use', or 'no_permission'."""
    try:
        import serial
    except ImportError:
        return None
    try:
        ser = serial.Serial(device, timeout=0.1)
        ser.close()
        return "available"
    except OSError as e:
        if e.errno == 16:  # EBUSY
            return "in_use"
        if e.errno in (13, 1):  # EACCES, EPERM
            return "no_permission"
        return None
    except Exception as e:
        msg = str(e).lower()
        if "busy" in msg or "in use" in msg or "resource" in msg:
            return "in_use"
        if "denied" in msg or "permission" in msg or "access" in msg:
            return "no_permission"
        return None


def check_serial_ports():
    """List serial ports. Linux: /dev/ttyACM*, /dev/ttyUSB*. Windows: COM*."""
    try:
        import serial.tools.list_ports
    except ImportError:
        print("Serial: pyserial not installed (pip install pyserial)")
        return
    ports = list(serial.tools.list_ports.comports())
    usb = [p for p in ports if _is_usb_port(p.device)]
    other = [p for p in ports if p not in usb]
    shown = usb or other
    if shown:
        print("Serial ports:")
        for p in sorted(shown, key=lambda x: (not _is_usb_port(x.device), x.device)):
            desc = p.description or ""
            note = " (USB, likely hand)" if _is_usb_port(p.device) else ""
            status = _port_status(p.device)
            if status == "in_use":
                note += " [IN USE by another process]"
            elif status == "no_permission":
                note += " [no permission; Linux: add user to dialout group]"
            print(f"  {p.device}: {desc}{note}")
        if usb:
            print("  Use the USB device in dataflow YAML --serialport.")
    else:
        print("Serial: no serial ports found. Connect the hand via USB and ensure drivers are installed.")


def main():
    print("=== AmazingHand device check ===\n")
    check_webcams()
    print()
    check_serial_ports()
    return 0


if __name__ == "__main__":
    sys.exit(main())
