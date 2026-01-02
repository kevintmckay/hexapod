"""
DEPRECATED: This file is for Pi Pico. Use esp32_main.py instead.

The hexapod now uses ESP32 WROOM-32 as the main controller.
This file is kept for reference only.

---

Hexapod Pico Controller (Real-Time) [DEPRECATED]

Runs on Pi Pico W. Handles:
- Servo control via PCA9685
- IMU reading (MPU6050)
- Distance sensing (VL53L0X)
- Battery monitoring (INA219)
- UART command interface with Pi Zero

UART Protocol (115200 baud, 8N1):
    Commands (from Zero):
        W:<dx>,<dy>     Walk in direction (mm)
        T:<angle>       Turn in place (degrees)
        S               Stop
        G:<gait>        Set gait (tripod, wave, ripple)
        H:<height>      Set standing height (mm)
        C               Center all servos
        B               Boot up sequence
        D               Shut down sequence
        ?               Query status

    Responses (to Zero):
        OK
        OK:<data>
        ERR:<message>
        IMU:<roll>,<pitch>,<yaw>
        DIST:<front>,<left>,<right>
        BAT:<voltage>,<current>,<soc>
"""

import time
from machine import Pin, I2C, UART

# I2C0 on GP4/GP5 (for sensors and PCA9685)
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

# UART0 on GP0/GP1 (for Zero communication)
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

# XSHUT pins for VL53L0X sensors
XSHUT_PINS = [Pin(6, Pin.OUT), Pin(7, Pin.OUT), Pin(8, Pin.OUT)]


class PicoController:
    """Main controller for Pico - handles commands and sensors."""

    def __init__(self):
        self.running = True
        self.gait_type = 'tripod'
        self.height = 50
        self.walking = False

        # Initialize components
        self._init_hardware()

    def _init_hardware(self):
        """Initialize all hardware components."""
        print("Initializing hardware...")

        # PCA9685 PWM drivers
        try:
            from pca9685 import PCA9685
            self.pca1 = PCA9685(i2c, address=0x40, freq=50)
            self.pca2 = PCA9685(i2c, address=0x41, freq=50)
            print("  PCA9685 x2: OK")
        except Exception as e:
            print(f"  PCA9685: FAIL - {e}")
            self.pca1 = None
            self.pca2 = None

        # Hexapod and gait controller
        try:
            from hexapod import Hexapod
            from gait import GaitController
            pca_drivers = [self.pca1, self.pca2] if self.pca1 else None
            self.hexapod = Hexapod(pca_drivers=pca_drivers,
                                   simulate=(pca_drivers is None))
            self.gait = GaitController(self.hexapod)
            print("  Hexapod: OK")
        except Exception as e:
            print(f"  Hexapod: FAIL - {e}")
            self.hexapod = None
            self.gait = None

        # MPU6050 IMU
        try:
            from mpu6050 import MPU6050
            self.imu = MPU6050(i2c, address=0x68)
            print("  MPU6050: OK")
        except Exception as e:
            print(f"  MPU6050: FAIL - {e}")
            self.imu = None

        # VL53L0X distance sensors
        try:
            from vl53l0x import VL53L0XArray
            self.distance = VL53L0XArray(i2c, XSHUT_PINS,
                                         addresses=[0x29, 0x30, 0x31])
            print("  VL53L0X x3: OK")
        except Exception as e:
            print(f"  VL53L0X: FAIL - {e}")
            self.distance = None

        # INA219 battery monitor
        try:
            from ina219 import INA219, BatteryMonitor
            ina = INA219(i2c, address=0x44)
            self.battery = BatteryMonitor(ina, cell_count=3)
            print("  INA219: OK")
        except Exception as e:
            print(f"  INA219: FAIL - {e}")
            self.battery = None

        print("Hardware init complete")

    def send_response(self, msg):
        """Send response to Zero via UART."""
        uart.write(f"{msg}\n".encode())

    def handle_command(self, cmd):
        """
        Parse and execute command from Zero.

        Args:
            cmd: Command string (without newline)
        """
        cmd = cmd.strip()
        if not cmd:
            return

        try:
            # Parse command
            if cmd.startswith('W:'):
                # Walk: W:<dx>,<dy>
                parts = cmd[2:].split(',')
                dx = float(parts[0])
                dy = float(parts[1]) if len(parts) > 1 else 0
                self._cmd_walk(dx, dy)

            elif cmd.startswith('T:'):
                # Turn: T:<angle>
                angle = float(cmd[2:])
                self._cmd_turn(angle)

            elif cmd == 'S':
                # Stop
                self._cmd_stop()

            elif cmd.startswith('G:'):
                # Set gait: G:<gait>
                gait = cmd[2:].strip().lower()
                self._cmd_set_gait(gait)

            elif cmd.startswith('H:'):
                # Set height: H:<mm>
                height = int(cmd[2:])
                self._cmd_set_height(height)

            elif cmd == 'C':
                # Center all servos
                self._cmd_center()

            elif cmd == 'B':
                # Boot up
                self._cmd_boot()

            elif cmd == 'D':
                # Shut down
                self._cmd_shutdown()

            elif cmd == '?':
                # Query status
                self._cmd_status()

            elif cmd == 'IMU':
                # Query IMU
                self._cmd_imu()

            elif cmd == 'DIST':
                # Query distance sensors
                self._cmd_dist()

            elif cmd == 'BAT':
                # Query battery
                self._cmd_bat()

            else:
                self.send_response(f"ERR:Unknown command: {cmd}")

        except Exception as e:
            self.send_response(f"ERR:{e}")

    def _cmd_walk(self, dx, dy):
        """Walk command."""
        if not self.gait:
            self.send_response("ERR:Gait controller not available")
            return

        import math
        direction = math.degrees(math.atan2(dy, dx))
        distance = math.sqrt(dx*dx + dy*dy)
        steps = max(1, int(distance / 30))

        if self.gait_type == 'tripod':
            self.gait.walk(direction=direction, steps=steps)
        elif self.gait_type == 'wave':
            self.gait.wave_walk(direction=direction, steps=steps)
        elif self.gait_type == 'ripple':
            from gait import RippleGait
            ripple = RippleGait(self.hexapod)
            ripple.walk(direction=direction, steps=steps)

        self.send_response("OK")

    def _cmd_turn(self, angle):
        """Turn in place command."""
        if not self.gait:
            self.send_response("ERR:Gait controller not available")
            return

        steps = max(1, abs(int(angle / 15)))
        self.gait.rotate(angle=angle/steps, steps=steps)
        self.send_response("OK")

    def _cmd_stop(self):
        """Stop walking and stand."""
        if self.gait:
            self.gait.stand(self.height)
        self.walking = False
        self.send_response("OK")

    def _cmd_set_gait(self, gait):
        """Set gait type."""
        if gait in ['tripod', 'wave', 'ripple']:
            self.gait_type = gait
            self.send_response(f"OK:{gait}")
        else:
            self.send_response(f"ERR:Unknown gait: {gait}")

    def _cmd_set_height(self, height):
        """Set standing height."""
        self.height = max(20, min(80, height))
        if self.gait:
            self.gait.stand_height = self.height
            self.gait.stand(self.height)
        self.send_response(f"OK:{self.height}")

    def _cmd_center(self):
        """Center all servos."""
        if self.hexapod:
            self.hexapod.center_all()
        self.send_response("OK")

    def _cmd_boot(self):
        """Boot up sequence."""
        if self.gait:
            self.gait.boot_up()
        self.send_response("OK")

    def _cmd_shutdown(self):
        """Shutdown sequence."""
        if self.gait:
            self.gait.shut_down()
        self.send_response("OK")

    def _cmd_status(self):
        """Query status."""
        status = {
            'gait': self.gait_type,
            'height': self.height,
            'walking': self.walking,
            'hw': {
                'pca': self.pca1 is not None,
                'imu': self.imu is not None,
                'dist': self.distance is not None,
                'bat': self.battery is not None,
            }
        }
        self.send_response(f"OK:{status}")

    def _cmd_imu(self):
        """Query IMU data."""
        if not self.imu:
            self.send_response("ERR:IMU not available")
            return

        roll, pitch = self.imu.get_roll_pitch()
        self.send_response(f"IMU:{roll:.1f},{pitch:.1f},0")

    def _cmd_dist(self):
        """Query distance sensors."""
        if not self.distance:
            self.send_response("ERR:Distance sensors not available")
            return

        readings = self.distance.read_all()
        self.send_response(f"DIST:{readings[0]},{readings[1]},{readings[2]}")

    def _cmd_bat(self):
        """Query battery status."""
        if not self.battery:
            self.send_response("ERR:Battery monitor not available")
            return

        status = self.battery.get_status()
        self.send_response(f"BAT:{status['voltage']:.2f},{status['current']:.2f},{status['soc_percent']:.0f}")

    def check_balance(self):
        """Check IMU and adjust if tilting too much."""
        if not self.imu:
            return

        roll, pitch = self.imu.get_roll_pitch()

        # If tilting more than 30 degrees, might be falling
        if abs(roll) > 30 or abs(pitch) > 30:
            print(f"Warning: Tilt detected! Roll={roll:.1f}, Pitch={pitch:.1f}")
            # Could implement balance correction here

    def check_battery(self):
        """Check battery and warn if low."""
        if not self.battery:
            return

        if self.battery.is_critical():
            self.send_response("ERR:CRITICAL_BATTERY")
            # Emergency shutdown
            if self.gait:
                self.gait.shut_down()
            self.running = False
        elif self.battery.is_low_battery():
            self.send_response("WARN:LOW_BATTERY")

    def run(self):
        """Main control loop."""
        print("Pico controller starting...")
        self.send_response("READY")

        last_sensor_check = time.ticks_ms()
        sensor_interval = 100  # Check sensors every 100ms

        while self.running:
            # Check for UART commands
            if uart.any():
                line = uart.readline()
                if line:
                    try:
                        cmd = line.decode().strip()
                        self.handle_command(cmd)
                    except Exception as e:
                        self.send_response(f"ERR:Parse error: {e}")

            # Periodic sensor checks
            now = time.ticks_ms()
            if time.ticks_diff(now, last_sensor_check) >= sensor_interval:
                last_sensor_check = now
                self.check_balance()

                # Battery check less frequently
                if now % 5000 < sensor_interval:
                    self.check_battery()

            # Small delay to prevent busy-waiting
            time.sleep(0.01)

        print("Pico controller stopped")


def main():
    """Entry point."""
    controller = PicoController()
    controller.run()


if __name__ == '__main__':
    main()
