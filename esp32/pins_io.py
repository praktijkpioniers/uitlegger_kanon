# pin_io.py
# Commentarii Latine: hic est fons veritatis (pins + protocol defaults).

# NDJSON prefix
NDJSON_PREFIX = "@MUSE#J="

# --- I2C: ToF (VL53L0X)
TOF_I2C_ID = 0
TOF_SDA_PIN = 21
TOF_SCL_PIN = 22
TOF_I2C_FREQ = 400_000
TOF_BUDGET_US = 40_000
TOF_PRE_PCLK = 18
TOF_FINAL_PCLK = 14

# --- I2C: MPU-6050 (gyro/accel)
MPU_I2C_ID = 1
MPU_SDA_PIN = 17
MPU_SCL_PIN = 16
MPU_I2C_FREQ = 400_000
MPU_ADDR = 0x68

# --- Sensors cadence
SENSORS_RATE_HZ = 1

# --- Button
BUTTON_PIN = 14
BUTTON_PULL = "down" #"up"          # "up" or "down"
BUTTON_ACTIVE_LEVEL = 1     # pull-up => pressed is usually 0
BUTTON_DEBOUNCE_MS = 35
BUTTON_SAMPLE_MS = 5

# --- Relays
RELAYS_PINS = [18, 19]                # edit
RELAYS_ACTIVE_HIGH = [False, False]   # edit (active-low relay boards are common)
RELAY_SAFE_OFF = 0
RELAYS_DEFAULT_TIMEOUT_S = 15 * 60

# --- LEDFX pins/lengths (match your ledfx defaults unless you override)
LED_PIN_SHORT = 27
LED_NUM_SHORT = 12
LED_PIN_LONG  = 25
LED_NUM_LONG  = 60

# --- Serial (UART) transport config (optional)
SERIAL_USE_UART = True   # if True: use UART; if False: stdin fallback
SERIAL_UART_ID = 0
SERIAL_BAUD = 115200
SERIAL_TX_PIN = None      # set if needed
SERIAL_RX_PIN = None      # set if needed

# --- UDP transport config (optional)
UDP_ENABLED = False
UDP_BIND_PORT = 7777
UDP_SEND_HOST = "255.255.255.255"
UDP_SEND_PORT = 7777
UDP_BROADCAST = True

DEMO_REPEAT = False #True

DEMO_FUSE_S = 8.0

DEMO_RELAY_A = 2     # smoke
DEMO_RELAY_B = 3     # fan

DEMO_SMOKE_S = 0.5
DEMO_FAN_S = 5.0
DEMO_FAN_LEAD_S = 0.5




