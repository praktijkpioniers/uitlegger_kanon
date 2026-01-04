# interface.py
import pins_io
import ndjson_prefix as ndj

import time

CLIENT_TTL_MS = 3 * 60 * 1000  # 3 minutes

SPAM_SERIAL = False #Set to true for sensor data on serial port

class ClientRegistry:
    def __init__(self):
        # key: (ip, port) -> last_seen_ms
        self._clients = {}

    def note_seen(self, addr):
        # addr = (ip, port)
        now = time.ticks_ms()
        self._clients[addr] = now

    def prune(self):
        now = time.ticks_ms()
        dead = []
        for addr, last in self._clients.items():
            if time.ticks_diff(now, last) > CLIENT_TTL_MS:
                dead.append(addr)
        for addr in dead:
            del self._clients[addr]

    def active(self):
        self.prune()
        return list(self._clients.keys())

clients = ClientRegistry()
        
        
class Interface:
    def __init__(self, prefix=pins_io.NDJSON_PREFIX):
        self.prefix = prefix
        self.debug = bool(getattr(pins_io, "DEBUG_IO", False))

        self._uart = None
        self._stdin_poller = None
        self._stdin = None

        # --- Serial backend: UART or stdin
        if getattr(pins_io, "SERIAL_USE_UART", False):
            try:
                from machine import UART, Pin
                txp = getattr(pins_io, "SERIAL_TX_PIN", None)
                rxp = getattr(pins_io, "SERIAL_RX_PIN", None)

                if txp is None and rxp is None:
                    self._uart = UART(pins_io.SERIAL_UART_ID, pins_io.SERIAL_BAUD)
                else:
                    tx = Pin(txp) if txp is not None else None
                    rx = Pin(rxp) if rxp is not None else None
                    self._uart = UART(pins_io.SERIAL_UART_ID, pins_io.SERIAL_BAUD, tx=tx, rx=rx)
            except Exception as e:
                self._uart = None
                if self.debug:
                    print("UART init failed:", repr(e))

        if self._uart is None:
            # stdin fallback (USB REPL stdout)
            try:
                import sys, uselect
                self._stdin = sys.stdin
                poller = uselect.poll()
                poller.register(self._stdin, uselect.POLLIN)
                self._stdin_poller = poller
            except Exception as e:
                self._stdin_poller = None
                self._stdin = None
                if self.debug:
                    print("stdin poll init failed:", repr(e))

        # --- UDP backend (optional)
        self._udp = None
        if getattr(pins_io, "UDP_ENABLED", False):
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.setblocking(False)
                s.bind(("0.0.0.0", pins_io.UDP_BIND_PORT))
                if getattr(pins_io, "UDP_BROADCAST", False):
                    try:
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    except Exception:
                        pass
                self._udp = s
            except Exception as e:
                self._udp = None
                if self.debug:
                    print("UDP init failed:", repr(e))

        self._rx_buf = b""

        # One-time announce so you can see where output went
        self.emit({
            "type": "iface",
            "uart": self._uart is not None,
            "udp": self._udp is not None,
            "prefix": self.prefix,
            "uart_id": getattr(pins_io, "SERIAL_UART_ID", None),
            "baud": getattr(pins_io, "SERIAL_BAUD", None),
            "tx": getattr(pins_io, "SERIAL_TX_PIN", None),
            "rx": getattr(pins_io, "SERIAL_RX_PIN", None),
        })

    def emit(self, obj):
        line = ndj.encode_line(obj, prefix=self.prefix)

        # serial out
        if self._uart is not None:
            try:
                if SPAM_SERIAL:
                    self._uart.write(line.encode("utf-8") + b"\n")
            except Exception as e:
                if self.debug:
                    print("UART write failed:", repr(e))
        else:
            # USB REPL stdout
            try:
                if SPAM_SERIAL:
                    print(line)
            except Exception as e:
                if self.debug:
                    # last resort: nothing else we can do
                    pass

        # udp out
        if self._udp is not None:
            try:
                payload = ndj.encode_bytes(obj, prefix=self.prefix)
                self._udp.sendto(payload, (pins_io.UDP_SEND_HOST, pins_io.UDP_SEND_PORT))
                for addr in clients.active():
                    self._udp.sendto(payload, addr)
                
            except Exception as e:
                if self.debug:
                    print("UDP send failed:", repr(e))

    def poll_messages(self):
        msgs = []
        msgs.extend(self._poll_serial_msgs())
        msgs.extend(self._poll_udp_msgs())
        return msgs

    def _poll_serial_msgs(self):
        out = []

        # UART mode
        if self._uart is not None:
            try:
                n = self._uart.any()
            except Exception:
                n = 0

            if n:
                try:
                    data = self._uart.read(n) or b""
                except Exception:
                    data = b""

                if data:
                    self._rx_buf += data
                    while b"\n" in self._rx_buf:
                        raw, self._rx_buf = self._rx_buf.split(b"\n", 1)
                        st, obj = ndj.try_parse_line(raw, prefix=self.prefix)
                        if st == "ok" and isinstance(obj, dict):
                            out.append(obj)
            return out

        # stdin mode
        if self._stdin_poller is None or self._stdin is None:
            return out

        try:
            if not self._stdin_poller.poll(0):
                return out
            while self._stdin_poller.poll(0):
                line = self._stdin.readline()
                if not line:
                    break
                st, obj = ndj.try_parse_line(line, prefix=self.prefix)
                if st == "ok" and isinstance(obj, dict):
                    out.append(obj)
        except Exception:
            pass

        return out

    def _poll_udp_msgs(self):
        out = []
        if self._udp is None:
            return out

        for _ in range(4):
            try:
                data, addr = self._udp.recvfrom(2048)
            except Exception:
                break

            clients.note_seen(addr)
            print (f"Received {data=}")
                
            st, obj = ndj.try_parse_line(data, prefix=self.prefix)
            if st == "ok" and isinstance(obj, dict):
                print (f"Accepted command {obj=}")            
                obj["_src"] = {"udp": addr}
                out.append(obj)
            else:
                print (f"Failed parse {obj=}")

        return out




