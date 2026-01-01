# gyro_sensor.py
from machine import Pin, I2C
import struct
import math


class MPUSensor:
    # Commentarii Latine: MPU-6050 (accel+gyro+temp) simpliciter legit.
    def __init__(self, i2c_id=1, sda_pin=17, scl_pin=16, freq=400_000, addr=0x68):
        self.addr = addr
        self.i2c = I2C(i2c_id, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=freq)
        self._init_mpu()

    def _writemem(self, reg, val):
        self.i2c.writeto_mem(self.addr, reg, bytes((val,)))

    def _init_mpu(self):
        # Wake + ±2g + ±250 dps
        self._writemem(0x6B, 0x00)  # PWR_MGMT_1
        self._writemem(0x1C, 0x00)  # ACCEL_CONFIG
        self._writemem(0x1B, 0x00)  # GYRO_CONFIG

    def read_raw(self):
        data = self.i2c.readfrom_mem(self.addr, 0x3B, 14)
        return struct.unpack(">7h", data)

    def read(self):
        ax, ay, az, temp, gx, gy, gz = self.read_raw()

        accel = (ax / 16384.0, ay / 16384.0, az / 16384.0)  # g
        gyro = (gx / 131.0, gy / 131.0, gz / 131.0)          # °/s
        temp_c = (temp / 340.0) + 36.53

        return {"accel_g": accel, "gyro_dps": gyro, "temp_c": temp_c}

    def tilt(self):
        # Tilt ex accel: pitch/roll (radiani).
        d = self.read()
        ax, ay, az = d["accel_g"]

        roll = math.atan2(ay, az)
        pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))

        d["tilt_rad"] = (pitch, roll)
        return d

