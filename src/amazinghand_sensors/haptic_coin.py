from time import sleep

from gpiozero import PWMLED
from loguru import logger


class HapticCoin:
    """
    Controls a haptic coin motor (QYF-740) via PWM on a Raspberry Pi GPIO pin.
    """

    def __init__(self, gpio_pin: int = 19):
        if gpio_pin is None:
            logger.warning("GPIO pin not specified — HapticCoin will not function")
            self.motor = None
            return
        self.gpio_pin = gpio_pin
        self.motor = PWMLED(self.gpio_pin)
        logger.info("HapticCoin initialised on GPIO pin {}", gpio_pin)

    def vibrate_once(self, intensity: float = 1.0, duration_s: float = 1.0):
        """Vibrate at *intensity* (0.0–1.0) for *duration_s* seconds, then pause equally."""
        if self.motor is None:
            return
        logger.debug("vibrate_once intensity={} duration={}s", intensity, duration_s)
        self.motor.value = intensity
        sleep(duration_s)
        self.motor.value = 0.0
        sleep(duration_s)

    def modulate_vibration(self, step: int = 5, delay_s: float = 0.05, pause_s: float = 1.0):
        """
        Ramp intensity up and down continuously until KeyboardInterrupt.

        :param step:    Duty-cycle increment in percent (1–100).
        :param delay_s: Delay between steps (s).
        :param pause_s: Pause between ramp cycles (s).
        """
        if self.motor is None:
            return
        try:
            while True:
                logger.debug("Ramping up")
                for duty in range(0, 101, step):
                    self.motor.value = duty / 100.0
                    sleep(delay_s)
                logger.debug("Ramping down")
                for duty in range(100, -1, -step):
                    self.motor.value = duty / 100.0
                    sleep(delay_s)
                sleep(pause_s)
        except KeyboardInterrupt:
            logger.info("modulate_vibration stopped by user")
        finally:
            self.cleanup()

    def vibration_magnitude(self, intensity: float = 1.0, timing_interval_s: float = 1.0):
        """Vibrate continuously at *intensity* until KeyboardInterrupt."""
        if self.motor is None:
            return
        try:
            while True:
                self.vibrate_once(intensity, timing_interval_s)
        except KeyboardInterrupt:
            logger.info("vibration_magnitude stopped by user")
        finally:
            self.cleanup()

    def cleanup(self):
        """Turn off the motor and release GPIO resources."""
        if self.motor is None:
            return
        self.motor.off()
        self.motor.close()
        logger.info("HapticCoin GPIO released")
