"""
PCA9685 PWM Driver

Works with both MicroPython (Pi Pico) and CPython (Pi Zero/Pi 4).
Includes I2C error handling with retry logic for reliability on mobile robots.
"""

import time

# Try to import the appropriate I2C library
try:
    # MicroPython (Pi Pico)
    from machine import I2C, Pin
    MICROPYTHON = True
except ImportError:
    # CPython with smbus2
    try:
        import smbus2
        MICROPYTHON = False
    except ImportError:
        print("Warning: No I2C library found. Running in simulation mode.")
        smbus2 = None
        MICROPYTHON = False

# PCA9685 registers
MODE1 = 0x00
MODE2 = 0x01
PRESCALE = 0xFE
LED0_ON_L = 0x06
LED0_ON_H = 0x07
LED0_OFF_L = 0x08
LED0_OFF_H = 0x09

# I2C retry settings
I2C_RETRIES = 3
I2C_RETRY_DELAY = 0.01  # 10ms between retries


class I2CError(Exception):
    """Custom exception for I2C communication failures."""
    pass


class PCA9685:
    """PCA9685 16-channel PWM driver with I2C error handling."""

    def __init__(self, i2c=None, address=0x40, freq=50, simulate=False,
                 on_error=None):
        """
        Args:
            i2c: I2C bus instance (MicroPython) or bus number (CPython)
            address: I2C address (0x40 default, 0x41 if A0 jumpered)
            freq: PWM frequency in Hz (50 for servos)
            simulate: If True, don't access hardware
            on_error: Optional callback function(address, error) for error handling
        """
        self.address = address
        self.freq = freq
        self.simulate = simulate or (smbus2 is None and not MICROPYTHON)
        self.on_error = on_error
        self._error_count = 0

        if self.simulate:
            print(f"PCA9685 @ 0x{address:02X}: Simulation mode")
            self._pwm_values = [0] * 16
            return

        if MICROPYTHON:
            self.i2c = i2c or I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
        else:
            bus_num = i2c if isinstance(i2c, int) else 1
            self.bus = smbus2.SMBus(bus_num)

        self._init_device()

    def _handle_error(self, operation, error):
        """Handle I2C error - log and optionally call callback."""
        self._error_count += 1
        msg = f"PCA9685 @ 0x{self.address:02X}: {operation} failed - {error}"
        print(f"Warning: {msg}")
        if self.on_error:
            try:
                self.on_error(self.address, error)
            except Exception:
                pass  # Don't let callback errors propagate

    def _write_byte(self, reg, value):
        """Write single byte to register with retry logic."""
        if self.simulate:
            return True

        for attempt in range(I2C_RETRIES):
            try:
                if MICROPYTHON:
                    self.i2c.writeto_mem(self.address, reg, bytes([value]))
                else:
                    self.bus.write_byte_data(self.address, reg, value)
                return True
            except (OSError, IOError) as e:
                if attempt < I2C_RETRIES - 1:
                    time.sleep(I2C_RETRY_DELAY)
                else:
                    self._handle_error(f"write reg 0x{reg:02X}", e)
                    return False
        return False

    def _read_byte(self, reg):
        """Read single byte from register with retry logic."""
        if self.simulate:
            return 0

        for attempt in range(I2C_RETRIES):
            try:
                if MICROPYTHON:
                    return self.i2c.readfrom_mem(self.address, reg, 1)[0]
                else:
                    return self.bus.read_byte_data(self.address, reg)
            except (OSError, IOError) as e:
                if attempt < I2C_RETRIES - 1:
                    time.sleep(I2C_RETRY_DELAY)
                else:
                    self._handle_error(f"read reg 0x{reg:02X}", e)
                    return 0
        return 0

    def _write_block(self, reg, data):
        """Write multiple bytes to register with retry logic."""
        if self.simulate:
            return True

        for attempt in range(I2C_RETRIES):
            try:
                if MICROPYTHON:
                    self.i2c.writeto_mem(self.address, reg, bytes(data))
                else:
                    self.bus.write_i2c_block_data(self.address, reg, data)
                return True
            except (OSError, IOError) as e:
                if attempt < I2C_RETRIES - 1:
                    time.sleep(I2C_RETRY_DELAY)
                else:
                    self._handle_error(f"write block reg 0x{reg:02X}", e)
                    return False
        return False

    def _init_device(self):
        """Initialize the PCA9685."""
        # Reset
        self._write_byte(MODE1, 0x00)
        time.sleep(0.005)

        # Set frequency
        self.set_frequency(self.freq)

        # Auto-increment enabled
        self._write_byte(MODE1, 0x20)
        time.sleep(0.005)

    def set_frequency(self, freq):
        """Set PWM frequency (24-1526 Hz)."""
        # prescale = round(25MHz / (4096 * freq)) - 1 (per PCA9685 datasheet)
        prescale = round(25000000.0 / (4096.0 * freq)) - 1
        prescale = max(3, min(255, prescale))

        old_mode = self._read_byte(MODE1)
        # Sleep mode to set prescale
        self._write_byte(MODE1, (old_mode & 0x7F) | 0x10)
        self._write_byte(PRESCALE, prescale)
        self._write_byte(MODE1, old_mode)
        time.sleep(0.005)
        # Restart
        self._write_byte(MODE1, old_mode | 0x80)

    def set_pwm(self, channel, pulse_us):
        """
        Set PWM pulse width for channel.

        Args:
            channel: 0-15
            pulse_us: Pulse width in microseconds (0 to disable)

        Returns:
            True if successful, False if I2C error occurred
        """
        if channel < 0 or channel > 15:
            return False

        if self.simulate:
            self._pwm_values[channel] = pulse_us
            return True

        if pulse_us == 0:
            # Full off
            on = 0
            off = 4096
        else:
            # Convert us to 12-bit value (at 50Hz, period = 20000us)
            period_us = 1000000.0 / self.freq
            off = int(pulse_us * 4096 / period_us)
            off = max(0, min(4095, off))
            on = 0

        reg = LED0_ON_L + 4 * channel
        return self._write_block(reg, [
            on & 0xFF, on >> 8, off & 0xFF, off >> 8
        ])

    def set_angle(self, channel, angle, min_pulse=500, max_pulse=2500):
        """
        Set servo angle.

        Args:
            channel: 0-15
            angle: 0-180 degrees
            min_pulse: Pulse width at 0 degrees (us)
            max_pulse: Pulse width at 180 degrees (us)
        """
        angle = max(0, min(180, angle))
        pulse = min_pulse + (angle / 180.0) * (max_pulse - min_pulse)
        self.set_pwm(channel, int(pulse))

    def disable(self, channel):
        """Disable PWM output (servo goes limp)."""
        self.set_pwm(channel, 0)

    def disable_all(self):
        """Disable all channels."""
        for ch in range(16):
            self.disable(ch)


if __name__ == '__main__':
    # Test
    print("PCA9685 Driver Test")
    print("=" * 40)

    # Create driver (simulation mode if no hardware)
    pca = PCA9685(address=0x40, simulate=True)

    # Test servo positions
    print("\nSetting channel 0 to 90 degrees...")
    pca.set_angle(0, 90)
    print(f"Pulse value: {pca._pwm_values[0]} us")

    print("\nSetting channel 0 to 0 degrees...")
    pca.set_angle(0, 0)
    print(f"Pulse value: {pca._pwm_values[0]} us")

    print("\nSetting channel 0 to 180 degrees...")
    pca.set_angle(0, 180)
    print(f"Pulse value: {pca._pwm_values[0]} us")
