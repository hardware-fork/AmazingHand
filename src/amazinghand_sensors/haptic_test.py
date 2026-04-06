"""
haptic_test.py — Interactive test script for HapticCoin (QYF-740 motor).

Run with:
    python haptic_test.py [--pin 19]

Uses Ctrl-C to exit any continuous mode.
"""

import argparse
import sys
from loguru import logger
from .haptic_coin import HapticCoin


def parse_args():
    parser = argparse.ArgumentParser(description="HapticCoin test script")
    parser.add_argument("--pin", type=int, default=19, help="GPIO pin (default: 19)")
    return parser.parse_args()


def print_menu():
    print("\n--- HapticCoin Test Menu ---")
    print("1. Single vibration pulse")
    print("2. Vibration at custom intensity")
    print("3. Continuous vibration (Ctrl-C to stop)")
    print("4. Ramp modulation (Ctrl-C to stop)")
    print("q. Quit")
    print("----------------------------")


def main():
    args = parse_args()
    haptic = HapticCoin(gpio_pin=args.pin)

    while True:
        print_menu()
        choice = input("Select option: ").strip().lower()

        if choice == "1":
            haptic.vibrate_once(intensity=1.0, duration_s=0.5)
            logger.info("Single pulse done")

        elif choice == "2":
            try:
                intensity = float(input("Intensity (0.0–1.0): "))
                duration = float(input("Duration (seconds): "))
                haptic.vibrate_once(intensity=intensity, duration_s=duration)
            except ValueError:
                print("Invalid input — enter numeric values.")

        elif choice == "3":
            try:
                intensity = float(input("Intensity (0.0–1.0): "))
                interval = float(input("On/off interval (seconds): "))
            except ValueError:
                print("Invalid input — enter numeric values.")
                continue
            logger.info("Starting continuous vibration — press Ctrl-C to stop")
            haptic.vibration_magnitude(intensity=intensity, timing_interval_s=interval)

        elif choice == "4":
            logger.info("Starting ramp modulation — press Ctrl-C to stop")
            haptic.modulate_vibration(step=5, delay_s=0.05, pause_s=1.0)

        elif choice == "q":
            haptic.cleanup()
            logger.info("Exiting")
            sys.exit(0)

        else:
            print("Unknown option — try again.")


if __name__ == "__main__":
    main()
