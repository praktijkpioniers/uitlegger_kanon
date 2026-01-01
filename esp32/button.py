# button.py
from machine import Pin
import time
import pins_io

EVT_BUTTON = "button"
EVT_PRESSED = "pressed"
EVT_RELEASED = "released"


class Button:
    # Commentarii Latine: de-bounce + edge detection; nullam "politicam" continet.
    def __init__(
        self,
        pin=None,
        pull=None,
        active_level=None,
        debounce_ms=None,
        sample_ms=None,
    ):
        self.pin_no = int(pins_io.BUTTON_PIN if pin is None else pin)
        self.pull = pins_io.BUTTON_PULL if pull is None else pull
        self.active_level = (1 if pins_io.BUTTON_ACTIVE_LEVEL else 0) if active_level is None else (1 if active_level else 0)
        self.debounce_ms = int(pins_io.BUTTON_DEBOUNCE_MS if debounce_ms is None else debounce_ms)
        self.sample_ms = int(pins_io.BUTTON_SAMPLE_MS if sample_ms is None else sample_ms)

        pull_mode = Pin.PULL_UP if self.pull == "up" else Pin.PULL_DOWN
        self.pin = Pin(self.pin_no, Pin.IN, pull_mode)

        self._stable = self.pin.value()
        self._last_raw = self._stable
        self._last_change_ms = time.ticks_ms()
        self._last_sample_ms = self._last_change_ms

    def tick(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_sample_ms) < self.sample_ms:
            return None
        self._last_sample_ms = now

        r = self.pin.value()
        if r != self._last_raw:
            self._last_raw = r
            self._last_change_ms = now
            return None

        if r != self._stable and time.ticks_diff(now, self._last_change_ms) >= self.debounce_ms:
            prev = self._stable
            self._stable = r

            pressed = (self._stable == self.active_level)
            return {
                "type": EVT_BUTTON,
                "ts_ms": now,
                "value": 1 if pressed else 0,
                "edge": EVT_PRESSED if pressed else EVT_RELEASED,
                "prev_raw": prev,
                "raw": r,
            }

        return None


