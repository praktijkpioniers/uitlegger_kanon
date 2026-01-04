# outputs.py
import pins_io
from ledfx import LedFx
from relays import RelayBank

CMD_KEY = "cmd"


class Outputs:
    def __init__(self, led_cfg=None):
        self.relays = RelayBank(
            pins=getattr(pins_io, "RELAYS_PINS", []),
            active_high=getattr(pins_io, "RELAYS_ACTIVE_HIGH", []),
            safe_off=getattr(pins_io, "RELAY_SAFE_OFF", 0),
            default_timeout_s=getattr(pins_io, "RELAYS_DEFAULT_TIMEOUT_S", None),
        )

        led_default = {
            "pin_short": getattr(pins_io, "LED_PIN_SHORT", None),
            "num_short": getattr(pins_io, "LED_NUM_SHORT", 0),
            "pin_long": getattr(pins_io, "LED_PIN_LONG", None),
            "num_long": getattr(pins_io, "LED_NUM_LONG", 0),
        }
        if led_cfg:
            led_default.update(led_cfg)
        self.led = LedFx(**led_default)

    def tick(self):
        self.relays.tick()
        self.led.tick()

    # ──────────────────────────────────────────────────────────────────────────
    # Command handling
    # ──────────────────────────────────────────────────────────────────────────

    def handle_cmd(self, msg):
        print (f"Received command {msg=}")
        c = msg.get(CMD_KEY)
        try:

            # Relay commands:
            # 1) {"cmd":"relay","id":0,"value":1,"timeout_s":900}
            # 2) {"cmd":"relay_pulse","id":0,"ms":250}
            # 3) {"cmd":"relay_keepalive","id":0,"timeout_s":900}
            # 4) {"cmd":"relays_all","value":0}
            if c == "relay":
                ch = int(msg.get("id", -1))
                val = 1 if msg.get("value", 0) else 0
                if val:
                    return self.relays.on(ch, timeout_s=msg.get("timeout_s"))
                else:
                    return self.relays.off(ch)
    
            if c == "relay_pulse":
                ch = int(msg.get("id", -1))
                ms = int(msg.get("ms", 250))
                return self.relays.pulse(ch, duration_ms=ms)
    
            if c == "relay_keepalive":
                ch = int(msg.get("id", -1))
                return self.relays.keep_alive(ch, timeout_s=msg.get("timeout_s"))
    
            if c == "relays_all":
                val = 1 if msg.get("value", 0) else 0
                if val:
                    # on all, with optional timeout
                    ok = True
                    for ch in range(self.relays.channel_count()):
                        ok = self.relays.on(ch, timeout_s=msg.get("timeout_s")) and ok
                    return ok
                else:
                    self.relays.all_off()
                    return True
    
            # LED commands:
            # {"cmd":"led","fx":"fuse","duration_s":8}
            # {"cmd":"led","fx":"flash"}
            # {"cmd":"led","fx":"stop"}
            if c == "led":
                fx = msg.get("fx")
                if fx == "fuse":
                    dur = msg.get("duration_s", msg.get("duration", 8.0))
                    self.led.start_fuse(duration_s=dur)
                    return True
                if fx == "flash":
                    self.led.start_flash(points=msg.get("points"))
                    return True
                if fx == "stop":
                    self.led.stop_all()
                    return True
                return False
        except Exception as e:
            print (f"Exception parsing command {e=}")
    
        return False


