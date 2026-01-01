# tof_sensor.py
from machine import Pin, I2C
from vl53l0x import VL53L0X


class ToFSensor:
    # Commentarii Latine: sensorem distantiae (VL53L0X) regit.
    def __init__(
        self,
        i2c_id=0,
        sda_pin=21,
        scl_pin=22,
        freq=400_000,
        budget_us=40_000,
        pre_pclk=18,
        final_pclk=14,
    ):
        self.i2c = I2C(i2c_id, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=freq)
        self.tof = VL53L0X(self.i2c)

        # Optiones “best effort” — si library variant est, non frangimus.
        try:
            self.tof.set_measurement_timing_budget(budget_us)
        except Exception:
            pass

        try:
            self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[0], int(pre_pclk))
            self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[1], int(final_pclk))
        except Exception:
            pass

    def scan(self):
        return self.i2c.scan()

    def read_mm(self):
        # Redit distantiam in millimetris (int), vel None si error.
        try:
            return int(self.tof.ping())
        except Exception:
            return None

