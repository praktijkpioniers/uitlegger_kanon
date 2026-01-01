# Uitlegger Kanon – ESP32 Protocol (Current)

## Transport
- Serial (UART / USB-CDC / stdin)
- UDP
- Same message format for all transports

## Framing
Each message is one line:

    @MUSE#J=<JSON>\n

- Prefix (mandatory): @MUSE#J=
- Encoding: UTF-8
- JSON must not contain newlines
- Lines without prefix are ignored

Example (single line):

    @MUSE#J={"type":"sensor","ts_ms":123456,"distance_mm":842}

---

## ESP32 → Host (Telemetry)

### Common fields

Field | Type | Notes
----- | ---- | -----
type | string | Always "sensor"
ts_ms | int | Milliseconds since boot

---

### Distance sensor (ToF)

Example:

    {"type":"sensor","ts_ms":123456,"distance_mm":842}

Field | Type
----- | ----
distance_mm | int

---

### IMU / Gyro

Example:

    {"type":"sensor","ts_ms":123789,"tilt":[1.2,-0.4,0.1],"accel_g":[0.01,0.98,0.02],"gyro_dps":[0.3,-0.1,0.0],"temp_c":32.5}

Field | Type | Notes
----- | ---- | -----
tilt | float[3] | Orientation vector
accel_g | float[3] | Acceleration in g
gyro_dps | float[3] | Degrees per second
temp_c | float | Celsius

Notes:
- Fields may be omitted if unavailable
- Arrays are always length 3 when present

---

## Host → ESP32 (Commands)

### General command format

    {"cmd":"<string>"}

Field | Type
----- | ----
cmd | string

---

### LED effects (cmd = fx)

Fuse effect:

    {"cmd":"fx","fx":"fuse","duration_s":8.0}

Field | Type | Notes
----- | ---- | -----
fx | string | "fuse"
duration_s | float | seconds
duration | float | accepted alias

Flash effect:

    {"cmd":"fx","fx":"flash","points":[0.2,0.6,1.0]}

Field | Type
----- | ----
points | float[]

Stop effects:

    {"cmd":"fx","fx":"stop"}

---

### Relay control

    {"cmd":"relay","index":0,"state":1,"timeout_s":5}

Field | Type
----- | ----
index | int
state | int | 0 or 1
timeout_s | float

Relay count and wiring are firmware-defined.

---

## UDP specifics
- Each UDP datagram contains one full line
- Source IP/port is stored internally and not transmitted
- No acknowledgements are sent

---

## Error handling
- Invalid JSON is dropped
- Unknown commands are ignored
- No error or ACK messages are emitted

---

## Forward (non-normative)
- Optional protocol/version field
- Optional command ACK or error messages
- Capability discovery command
- Explicit device ID field

End of document.
