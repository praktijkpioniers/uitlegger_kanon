# bootgame.py
import time

import net_setup

import pins_io
from interface import Interface
from sensors import Sensors
from outputs import Outputs
from button import Button

# esp32 standalone demo / hardware check.
DEMO_MODE = True


def _ms(s):
    return int(float(s) * 1000.0)


def main():
    iface = Interface(prefix=pins_io.NDJSON_PREFIX)
    sensors = Sensors(rate_hz=getattr(pins_io, "SENSORS_RATE_HZ", 5))
    outputs = Outputs()
    button = Button()

    DEMO = bool(DEMO_MODE)
    REPEAT = False #bool(getattr(pins_io, "DEMO_REPEAT", True))

    # Timeline knobs
    FUSE_S = float(getattr(pins_io, "DEMO_FUSE_S", 8.0))
    FUSE_MS = _ms(FUSE_S)

    RELAY_A = int(getattr(pins_io, "DEMO_RELAY_A", 0))     # smoke
    RELAY_B = int(getattr(pins_io, "DEMO_RELAY_B", 1))     # fan

    SMOKE_MS = _ms(getattr(pins_io, "DEMO_SMOKE_S", 0.5))  # relay A pulse
    FAN_MS = _ms(getattr(pins_io, "DEMO_FAN_S", 5.0))      # relay B pulse
    FAN_LEAD_MS = _ms(getattr(pins_io, "DEMO_FAN_LEAD_S", 0.5))  # before flash

    iface.emit({"type": "boot", "ts_ms": time.ticks_ms(), "demo": DEMO})

    demo_state = "idle"
    demo_t0 = time.ticks_ms()
    did_fan = False

    def demo_set_state(st):
        nonlocal demo_state, demo_t0, did_fan
        demo_state = st
        demo_t0 = time.ticks_ms()
        did_fan = False
        iface.emit({"type": "demo", "state": demo_state, "ts_ms": demo_t0})

    def start_cycle():
        nonlocal demo_state, demo_t0, did_fan
        demo_state = "fuse"
        demo_t0 = time.ticks_ms()
        did_fan = False
        iface.emit({"type": "demo", "state": demo_state, "ts_ms": demo_t0})

        # Stage 1: fuse + smoke
        outputs.handle_cmd({"cmd": "led", "fx": "fuse", "duration_s": FUSE_S})
        outputs.handle_cmd({"cmd": "relay_pulse", "id": RELAY_A, "ms": SMOKE_MS})

    if DEMO:
        start_cycle()

    last_yield = time.ticks_ms()
    while True:
        outputs.tick()

        if sensors.due():
            iface.emit(sensors.read())

        evt = button.tick()
        if evt:
            iface.emit(evt)

        if not DEMO: 
            for msg in iface.poll_messages():
                if isinstance(msg, dict) and "cmd" in msg:
                    ok = outputs.handle_cmd(msg)
                    if not ok:
                        iface.emit({"type": "warn", "what": "unknown_cmd", "msg": msg})
        else:
            _ = iface.poll_messages()  # drain only

            now = time.ticks_ms()
            dt = time.ticks_diff(now, demo_t0)

            if demo_state == "fuse":
                # Stage 2 prep: fan starts FAN_LEAD_MS before flash
                if (not did_fan) and dt >= (FUSE_MS - FAN_LEAD_MS):
                    outputs.handle_cmd({"cmd": "relay_pulse", "id": RELAY_B, "ms": FAN_MS})
                    iface.emit({"type": "demo", "event": "fan_pulse", "ms": FAN_MS, "ts_ms": now})
                    did_fan = True

                # Stage 2: flash at end of fuse window
                if dt >= FUSE_MS:
                    outputs.handle_cmd({"cmd": "led", "fx": "flash"})
                    demo_set_state("flash")

            elif demo_state == "flash":
                # We don't track flash completion here; effect runs its own envelope.
                #if REPEAT:
                #    start_cycle()
                #else:
                #    demo_set_state("idle")
                demo_set_state("idle")
                DEMO = False

        now = time.ticks_ms()
        if time.ticks_diff(now, last_yield) >= 5:
            last_yield = now
            time.sleep_ms(1)


main()



