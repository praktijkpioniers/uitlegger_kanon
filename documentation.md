# Uitlegger Kanon – ESP32 Firmware

## Goal

This project contains the **ESP32 MicroPython firmware** for the *Uitlegger Kanon* installation.

The firmware turns an ESP32 into a **sensor + actuator node** that:
- reads physical sensors (distance, IMU),
- drives outputs (LED effects, relays),
- communicates with a host game or controller
  via a small, robust, text-based protocol over **Serial and UDP**.

The design favors:
- simplicity over abstraction,
- explicit state over hidden magic,
- resilience against serial noise and partial failures,
- easy inspection with logs and `screen`/`nc`.

---

## High-level Architecture

```
           ┌────────────┐
           │   Host     │
           │ (Game /    │
           │ Controller)│
           └─────┬──────┘
                 │
        NDJSON + magic prefix
          (Serial / UDP)
                 │
           ┌─────▼──────┐
           │   ESP32    │
           │ MicroPython│
           └────────────┘
```

The ESP32 is intentionally **stateless at the protocol level**.
Each message stands on its own.

---

## Module Overview

### `main.py`
**Entry point**.

Responsibilities:
- Bootstraps hardware
- Initializes sensors and outputs
- Starts serial and UDP listeners
- Runs the main polling loop

Notes:
- Uses cooperative polling (no preemption)
- Avoids dynamic imports inside loops

---

### `ndjson_prefix.py`
**Protocol framing and parsing**.

Responsibilities:
- Defines the magic prefix (`@MUSE#J=`)
- Encodes JSON messages with prefix
- Parses incoming lines safely
- Drops malformed or non-protocol input

Why this exists:
- Serial lines may contain noise
- REPL output must not break parsing
- Prefix allows trivial filtering on host side

---

### `sensors.py`
**Sensor aggregation and emission**.

Responsibilities:
- Reads physical sensors
- Normalizes values
- Emits telemetry messages

Implemented sensors:
- Distance sensor (ToF)
- IMU / gyro (tilt, accel, gyro, temperature)

Notes:
- Sensors may be absent or fail silently
- Missing sensors simply omit fields
- All timestamps are `ts_ms` (int, milliseconds)

---

### `outputs.py`
**Command dispatcher for outputs**.

Responsibilities:
- Receives parsed command objects
- Routes them to LEDs, relays, etc.
- Acts as a thin command-to-action layer

Design choice:
- No protocol validation beyond basic structure
- Unknown commands are ignored, not rejected

---

### `ledfx.py`
**LED effect engine**.

Responsibilities:
- Implements time-based LED animations
- Manages effect lifecycle (start/stop)
- Non-blocking updates from main loop

Current effects:
- Fuse effect
- Flash effect
- Stop / clear

Notes:
- Effects are cooperative (no threads)
- Time-based using monotonic ticks
- Designed to survive partial command input

---

### `relays.py`
**Relay control abstraction**.

Responsibilities:
- Controls one or more relays
- Supports timed activation
- Keeps relay logic separate from protocol

Notes:
- Relay count and wiring are board-specific
- Timeouts are optional but supported

---

### `pins_io.py`
**Hardware pin mapping**.

Responsibilities:
- Central definition of GPIO usage
- Separates hardware wiring from logic

Why this matters:
- Makes board swaps feasible
- Prevents pin conflicts
- Keeps logic files hardware-agnostic

---

## Communication Model

- Messages are **line-based**
- One JSON object per line
- Same format for Serial and UDP
- No acknowledgements
- No retries
- Host is assumed to be tolerant

This keeps the ESP32 firmware:
- small,
- predictable,
- easy to debug.

See `protocol.md` for the exact wire format.

---

## MicroPython-Specific Notes

This code intentionally works *with* MicroPython’s constraints:

- No threads
- Limited heap
- Garbage collection pauses
- Slower JSON parsing than CPython

Design responses:
- Short-lived objects
- Minimal allocations in loops
- No recursion
- Simple lists and dicts only
- Explicit timing instead of callbacks

---

## Debugging & Development

Common tools:
- `screen` / `picocom` for serial
- `nc -u` for UDP testing
- Raw text inspection (no binary framing)

Typical workflow:
1. Flash firmware
2. Observe raw NDJSON output
3. Inject commands manually
4. Integrate host-side logic later

---

## Non-goals

Explicitly *not* in scope:
- Reliable delivery
- Encryption or authentication
- Binary protocols
- Automatic discovery
- Complex state machines

Those belong on the host side.

---

## Future Directions (Non-binding)

Possible future extensions (not implemented):
- Protocol version field
- Device ID field
- Optional ACK / error messages
- Capability discovery command

All of these can be added without breaking existing hosts.

---

End of document.
