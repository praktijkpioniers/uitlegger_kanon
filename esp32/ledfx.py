# ledfx.py
from machine import Pin
import neopixel
import time

# ─────────────────────────────────────────────────────────────────────────────
# Hardware defaults
# ─────────────────────────────────────────────────────────────────────────────

PIN_SHORT = 27
NUM_SHORT = 12

PIN_LONG  = 25
NUM_LONG  = 60

# ─────────────────────────────────────────────────────────────────────────────
# Fuse config
# ─────────────────────────────────────────────────────────────────────────────

BURN_DURATION_S = 8.0
SMOOTH_MODE = True   # False = 2 LEDs, True = 3 LEDs smooth mix

HOT_RGB   = (255, 180, 20)   # RGB
EMBER_RGB = (255, 40, 0)     # RGB

HOT_V   = 90
EMBER_V = 80

# ─────────────────────────────────────────────────────────────────────────────
# Flash config
# ─────────────────────────────────────────────────────────────────────────────

FLASH_POINTS_DEFAULT = [
    (0.00, (0,   0,   0)),
    (0.50, (128, 96,  0)),
    (0.08, (0,   0,  255)),
    (0.06, (255, 255, 255)),
    (0.40, (255, 120, 0)),
    (1.00, (255, 0,   0)),
    (3.00, (0,   0,   0)),
]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def clamp(x):
    return 0 if x < 0 else 255 if x > 255 else x

def scale(rgb, v):
    r, g, b = rgb
    return (clamp(r * v // 255), clamp(g * v // 255), clamp(b * v // 255))

def clear(np):
    for i in range(len(np)):
        np[i] = (0, 0, 0)

def fill(np, rgb):
    for i in range(len(np)):
        np[i] = rgb
    np.write()

def mix_rgb(a, b, t01):
    ar, ag, ab = a
    br, bg, bb = b
    return (
        clamp(int(ar + (br - ar) * t01)),
        clamp(int(ag + (bg - ag) * t01)),
        clamp(int(ab + (bb - ab) * t01)),
    )

def _dt_ms_fallback(last_ms):
    now = time.ticks_ms()
    dt = time.ticks_diff(now, last_ms)
    return now, 0 if dt < 0 else dt

# ─────────────────────────────────────────────────────────────────────────────
# Fuse effect (non-blocking)
# ─────────────────────────────────────────────────────────────────────────────

class FuseEffect:
    def __init__(self, np):
        self.np = np
        self.n = len(np)
        self.active = False
        self._elapsed_ms = 0
        self._duration_ms = int(BURN_DURATION_S * 1000)
        self._last_ms = time.ticks_ms()

    def start(self, duration_s=BURN_DURATION_S):
        self._duration_ms = int(max(0.001, float(duration_s)) * 1000)
        self._elapsed_ms = 0
        self._last_ms = time.ticks_ms()
        self.active = True

    def stop(self, clear_strip=True):
        self.active = False
        if clear_strip:
            clear(self.np)
            self.np.write()

    def tick(self, dt=None):
        if not self.active:
            if dt is None:
                self._last_ms = time.ticks_ms()
            return False

        if dt is None:
            self._last_ms, dt_ms = _dt_ms_fallback(self._last_ms)
        else:
            dt_ms = dt if isinstance(dt, int) else int(float(dt) * 1000)
            if dt_ms < 0:
                dt_ms = 0

        if dt_ms > 250:
            dt_ms = 250

        self._elapsed_ms += dt_ms
        t01 = self._elapsed_ms / self._duration_ms

        if t01 >= 1.0:
            self.stop(clear_strip=True)
            return True

        self.render(t01)
        return True

    def render(self, t01):
        # Commentarii Latine: hic render “preservatus” est (non-blocking tick).
        clear(self.np)

        pos = (self.n - 1) * (1.0 - t01)
        i = int(pos)
        f = pos - i
        F = 1.0 - f

        if not SMOOTH_MODE:
            if 0 <= i < self.n:
                self.np[i] = scale(HOT_RGB, HOT_V)
            if 0 <= i + 1 < self.n:
                self.np[i + 1] = scale(EMBER_RGB, EMBER_V)
        else:
            if 0 <= i + 2 < self.n:
                c0 = scale(HOT_RGB, int(0.5 * f * HOT_V))
                self.np[i + 2] = c0

            if 0 <= i + 1 < self.n:
                hot_part   = scale(HOT_RGB,   int(F * HOT_V))
                ember_part = scale(EMBER_RGB, int(f * EMBER_V))
                self.np[i + 1] = (
                    clamp(hot_part[0] + ember_part[0]),
                    clamp(hot_part[1] + ember_part[1]),
                    clamp(hot_part[2] + ember_part[2]),
                )

            if 0 <= i + 0 < self.n:
                c2 = scale(EMBER_RGB, int(F * EMBER_V))
                self.np[i + 0] = c2

        self.np.write()

# ─────────────────────────────────────────────────────────────────────────────
# Flash effect (non-blocking envelope)
# ─────────────────────────────────────────────────────────────────────────────

class FlashEffect:
    def __init__(self, np):
        self.np = np
        self.active = False
        self._points = None
        self._seg = 0
        self._seg_t = 0
        self._seg_ms = 0
        self._last_ms = time.ticks_ms()

    def start(self, points=None):
        pts = points if points is not None else FLASH_POINTS_DEFAULT
        if not pts or len(pts) < 2:
            self.stop(clear_strip=False)
            return

        norm = []
        for dur_s, rgb in pts:
            dur_ms = int(max(0.0, float(dur_s)) * 1000.0)
            norm.append((dur_ms, (int(rgb[0]), int(rgb[1]), int(rgb[2]))))

        self._points = norm
        self._seg = 0
        self._seg_t = 0
        self._seg_ms = self._points[1][0]
        self._last_ms = time.ticks_ms()
        self.active = True
        fill(self.np, self._points[0][1])

    def stop(self, clear_strip=True):
        self.active = False
        self._points = None
        self._seg = 0
        self._seg_t = 0
        self._seg_ms = 0
        if clear_strip:
            clear(self.np)
            self.np.write()

    def tick(self, dt=None):
        if not self.active or not self._points:
            if dt is None:
                self._last_ms = time.ticks_ms()
            return False

        if dt is None:
            self._last_ms, dt_ms = _dt_ms_fallback(self._last_ms)
        else:
            dt_ms = dt if isinstance(dt, int) else int(float(dt) * 1000)
            if dt_ms < 0:
                dt_ms = 0

        if dt_ms > 250:
            dt_ms = 250

        while dt_ms > 0 and self.active:
            a_rgb = self._points[self._seg][1]
            b_rgb = self._points[self._seg + 1][1]
            seg_ms = self._seg_ms

            if seg_ms <= 0:
                fill(self.np, b_rgb)
                self._seg += 1
                self._seg_t = 0
                if self._seg >= len(self._points) - 1:
                    self.stop(clear_strip=False)
                    return True
                self._seg_ms = self._points[self._seg + 1][0]
                continue

            remaining = seg_ms - self._seg_t
            step = remaining if dt_ms >= remaining else dt_ms

            self._seg_t += step
            dt_ms -= step

            t01 = self._seg_t / seg_ms
            fill(self.np, mix_rgb(a_rgb, b_rgb, t01))

            if self._seg_t >= seg_ms:
                self._seg += 1
                self._seg_t = 0
                if self._seg >= len(self._points) - 1:
                    self.stop(clear_strip=False)
                    return True
                self._seg_ms = self._points[self._seg + 1][0]

        return True

# ─────────────────────────────────────────────────────────────────────────────
# Manager: both effects can run concurrently (overlap)
# ─────────────────────────────────────────────────────────────────────────────

class LedFx:
    def __init__(
        self,
        pin_short=PIN_SHORT, num_short=NUM_SHORT,
        pin_long=PIN_LONG,   num_long=NUM_LONG,
    ):
        self.np_short = neopixel.NeoPixel(Pin(pin_short, Pin.OUT), num_short) if pin_short is not None else None
        self.np_long  = neopixel.NeoPixel(Pin(pin_long,  Pin.OUT), num_long)  if pin_long  is not None else None

        if self.np_short:
            clear(self.np_short); self.np_short.write()
        if self.np_long:
            clear(self.np_long);  self.np_long.write()

        self.fuse  = FuseEffect(self.np_short) if self.np_short else None
        self.flash = FlashEffect(self.np_long)  if self.np_long  else None

    def start_fuse(self, duration_s=BURN_DURATION_S):
        if self.fuse:
            self.fuse.start(duration_s)

    def start_flash(self, points=None):
        if self.flash:
            self.flash.start(points)

    def stop_fuse(self, clear_strip=True):
        if self.fuse:
            self.fuse.stop(clear_strip=clear_strip)

    def stop_flash(self, clear_strip=True):
        if self.flash:
            self.flash.stop(clear_strip=clear_strip)

    def stop_all(self):
        if self.fuse:
            self.fuse.stop(clear_strip=True)
        if self.flash:
            self.flash.stop(clear_strip=True)

    def tick(self, dt=None):
        did = False
        if self.fuse:
            did = self.fuse.tick(dt) or did
        if self.flash:
            did = self.flash.tick(dt) or did
        return did

