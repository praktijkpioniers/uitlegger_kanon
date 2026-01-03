## ESP32 based joystick-like control

Micropython code for ESP32


## Protocol
For protocol details, see protocol.md

The device will send ouput over serial and UDP.
Example format:

@MUSE#J={"ts_ms":712744,"edge":"pressed","prev_raw":0,"raw":1,"value":1,"type":"
button"}
@MUSE#J={"type":"sensor","ts_ms":712893,"tilt":{"roll_rad":1.9682385,"pitch_rad"
:-0.41146304},"distance_mm":21,"accel_g":{"x":0.40185548,"z":-0.3564453,"y":0.84
91211},"gyro_dps":{"x":4.7099236,"z":-0.412213736,"y":-1.2366412},"temp_c":36.29
4704}
@MUSE#J={"ts_ms":712928,"edge":"released","prev_raw":1,"raw":0,"value":0,"type":
"button"}
@MUSE#J={"type":"sensor","ts_ms":713896,"tilt":{"roll_rad":1.974683,"pitch_rad":
-0.404492032},"distance_mm":17,"accel_g":{"x":0.3959961,"z":-0.3635254,"y":0.850
58592},"gyro_dps":{"x":5.0076336,"z":-0.488549632,"y":-1.6335878},"temp_c":36.43
5884}



## Setup
```text
┌───────────────┐        ┌───────────────┐
│   ROOK        │  FOG   │   RELAIS      │
│  MACHINE      ├────────►  (MAINS SW)   │
└───────────────┘        └──────┬────────┘
                                │
                                │ FOG_RELAY_CTRL
                        ┌───────▼───────────┐
                        │      ESP32        │
                        │                   │
   START_BTN  ─────────►│ START_IN          │
                        │                   │
   X_SENSOR   ─────────►│ X_AXIS_IN         │
                        │                   │
   Z_SENSOR   ─────────►│ Z_AXIS_IN         │
                        │                   │
                        │ FOG_RELAY_OUT ────┴─────► to RELAIS coil
                        │ LONTLICHT_OUT ─────────► fuse light
                        │ STRIP_END_OUT ────────► end-of-strip light
                        │ USB_SERIAL_TX/RX ─────┬───────────────┐
                        └───────────────────────┘               │
                                                                │
                                                        ┌───────▼────────┐
                                                        │   PC GAME      │
                                                        │    APP / PC    │
                                                        │                │
                             HDMI_OUT ──────────────────►                │
                                                        │                │
                             USB_SERIAL (ESP32) ◄───────┤                │
                                                        │ AUDIO_OUT ─────┴─────┐
                                                        │ ETH / NETWORK ◄─────►│
                                                        │  (optional)          │
                                                        └──────────────────────┘
                                                                   │
                                                                   │
                                                          ┌────────▼───────┐
                                                          │   AUDIO AMP    │
                                                          └──────┬─────────┘
                                                                 │
                                                         SPEAKER_OUT
                                                                 │
                                                    ┌────────────▼───────┐
                                                    │  SPEAKER /         │
                                                    │   BOOMBOX          │
                                                    └────────────────────┘

┌───────────────┐
│   BEAMER      │
│ (PROJECTOR)   │
└───────▲───────┘
        │
   HDMI_IN  ◄──────────── from PC HDMI_OUT
```
