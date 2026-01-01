# relays.py
from machine import Pin
import time


class RelayBank:
    # Commentarii Latine: canales → GPIO; pulse + latch cum timeout (keep-alive).
    def __init__(self, pins, active_high=None, safe_off=0, default_timeout_s=None):
        self.pins = list(pins or [])
        self.active_high = list(active_high or [])
        while len(self.active_high) < len(self.pins):
            self.active_high.append(True)

        self.safe_off = 1 if safe_off else 0
        self.default_timeout_ms = None if default_timeout_s is None else int(float(default_timeout_s) * 1000.0)

        self._io = [Pin(p, Pin.OUT) for p in self.pins]

        # Per-channel timers/state
        self._pulse_until = [None] * len(self._io)   # ts_ms when pulse ends
        self._latch_until = [None] * len(self._io)   # ts_ms when latch expires (keep-alive)

        self.all_off()

    def _level(self, ch, logical_on):
        v = 1 if logical_on else 0
        return v if self.active_high[ch] else (0 if v else 1)

    def _write(self, ch, logical_on):
        self._io[ch].value(self._level(ch, logical_on))

    def channel_count(self):
        return len(self._io)

    def all_off(self):
        for ch in range(len(self._io)):
            self.off(ch)

    def off(self, ch):
        if ch < 0 or ch >= len(self._io):
            return False
        self._pulse_until[ch] = None
        self._latch_until[ch] = None
        self._write(ch, 0 if self.safe_off == 0 else 0)  # safe_off means "logical off"
        return True

    def on(self, ch, timeout_s=None):
        """
        Latch ON. If timeout_s is provided (or default_timeout_s set),
        it will auto-off unless refreshed (keep_alive()).
        """
        if ch < 0 or ch >= len(self._io):
            return False

        self._pulse_until[ch] = None
        self._write(ch, 1)

        ms = None
        if timeout_s is not None:
            ms = int(float(timeout_s) * 1000.0)
        elif self.default_timeout_ms is not None:
            ms = self.default_timeout_ms

        if ms is None:
            self._latch_until[ch] = None
        else:
            self._latch_until[ch] = time.ticks_add(time.ticks_ms(), ms)
        return True

    def keep_alive(self, ch, timeout_s=None):
        """
        Refresh the latch timeout. Does not change ON/OFF state;
        but practically you call it for channels meant to be kept on.
        """
        if ch < 0 or ch >= len(self._io):
            return False
        if self._latch_until[ch] is None and timeout_s is None and self.default_timeout_ms is None:
            # no timeout mode; nothing to refresh
            return True

        ms = None
        if timeout_s is not None:
            ms = int(float(timeout_s) * 1000.0)
        elif self.default_timeout_ms is not None:
            ms = self.default_timeout_ms

        if ms is not None:
            self._latch_until[ch] = time.ticks_add(time.ticks_ms(), ms)
        return True

    def pulse(self, ch, duration_ms=250):
        """
        Pulse ON for duration_ms then OFF.
        If channel is latched, pulse overrides latch until done.
        """
        if ch < 0 or ch >= len(self._io):
            return False

        d = int(duration_ms)
        if d < 1:
            d = 1

        self._latch_until[ch] = None
        self._write(ch, 1)
        self._pulse_until[ch] = time.ticks_add(time.ticks_ms(), d)
        return True

    def tick(self):
        """
        Non-blocking timer maintenance. Call often.
        """
        now = time.ticks_ms()
        for ch in range(len(self._io)):
            pu = self._pulse_until[ch]
            if pu is not None and time.ticks_diff(now, pu) >= 0:
                self._pulse_until[ch] = None
                self._write(ch, 0)

            lu = self._latch_until[ch]
            if lu is not None and time.ticks_diff(now, lu) >= 0:
                # latch expired
                self._latch_until[ch] = None
                self._write(ch, 0)

