##ESP32 based joystick-like control

Micropython code for ESP32


##Setup
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

