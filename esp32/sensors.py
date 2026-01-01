# sensors.py
import time

import pins_io
from tof_sensor import ToFSensor
from gyro_sensor import MPUSensor

SENSORS_CACHE_DEFAULT = True

FIELD_TYPE = "sensor"
FIELD_TS_MS = "ts_ms"
FIELD_DISTANCE_MM = "distance_mm"
FIELD_TILT = "tilt"
FIELD_ACCEL_G = "accel_g"
FIELD_GYRO_DPS = "gyro_dps"
FIELD_TEMP_C = "temp_c"


class Sensors:
    # Commentarii Latine: sensoria colligit et structuram unicam reddit.
    def __init__(
        self,
        tof_cfg=None,
        mpu_cfg=None,
        rate_hz=pins_io.SENSORS_RATE_HZ,
        enable_cache=SENSORS_CACHE_DEFAULT,
        field_names=None,
    ):
        # Default cfg from pins_io, override by passing dicts
        tof_default = {
            "i2c_id": pins_io.TOF_I2C_ID,
            "sda_pin": pins_io.TOF_SDA_PIN,
            "scl_pin": pins_io.TOF_SCL_PIN,
            "freq": pins_io.TOF_I2C_FREQ,
            "budget_us": pins_io.TOF_BUDGET_US,
            "pre_pclk": pins_io.TOF_PRE_PCLK,
            "final_pclk": pins_io.TOF_FINAL_PCLK,
        }
        mpu_default = {
            "i2c_id": pins_io.MPU_I2C_ID,
            "sda_pin": pins_io.MPU_SDA_PIN,
            "scl_pin": pins_io.MPU_SCL_PIN,
            "freq": pins_io.MPU_I2C_FREQ,
            "addr": pins_io.MPU_ADDR,
        }
        if tof_cfg:
            tof_default.update(tof_cfg)
        if mpu_cfg:
            mpu_default.update(mpu_cfg)

        self.tof = ToFSensor(**tof_default)
        self.mpu = MPUSensor(**mpu_default)

        self.rate_hz = int(rate_hz) if rate_hz is not None else int(pin_io.SENSORS_RATE_HZ)
        if self.rate_hz < 1:
            self.rate_hz = 1
        self.period_ms = int(1000 // self.rate_hz)

        self.enable_cache = bool(enable_cache)
        self._last_ms = time.ticks_ms()
        self._cache = None

        fn = field_names or {}
        self.F_TYPE = fn.get("type", FIELD_TYPE)
        self.F_TS = fn.get("ts_ms", FIELD_TS_MS)
        self.F_DIST = fn.get("distance_mm", FIELD_DISTANCE_MM)
        self.F_TILT = fn.get("tilt", FIELD_TILT)
        self.F_ACCEL = fn.get("accel_g", FIELD_ACCEL_G)
        self.F_GYRO = fn.get("gyro_dps", FIELD_GYRO_DPS)
        self.F_TEMP = fn.get("temp_c", FIELD_TEMP_C)

    def due(self, now_ms=None):
        now = time.ticks_ms() if now_ms is None else int(now_ms)
        return time.ticks_diff(now, self._last_ms) >= self.period_ms

    def read(self, force=False, now_ms=None):
        now = time.ticks_ms() if now_ms is None else int(now_ms)

        if (not force) and self.enable_cache and self._cache is not None:
            if time.ticks_diff(now, self._last_ms) < self.period_ms:
                return self._cache

        self._last_ms = now

        dist = self.tof.read_mm()
        m = self.mpu.tilt()

        pitch, roll = m.get("tilt_rad", (None, None))
        ax, ay, az = m.get("accel_g", (None, None, None))
        gx, gy, gz = m.get("gyro_dps", (None, None, None))

        payload = {
            "type": self.F_TYPE,
            self.F_TS: now,
            self.F_DIST: dist,
            self.F_TILT: {"pitch_rad": pitch, "roll_rad": roll},
            self.F_ACCEL: {"x": ax, "y": ay, "z": az},
            self.F_GYRO: {"x": gx, "y": gy, "z": gz},
            self.F_TEMP: m.get("temp_c"),
        }

        if self.enable_cache:
            self._cache = payload
        return payload

