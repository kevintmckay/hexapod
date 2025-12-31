"""
LX-16A Serial Bus Servo Driver

Python driver for LewanSoul/Hiwonder LX-16A serial bus servos.
Protocol reference: lewansoul.cpp from Sawppy project.

Hardware:
- TTL Serial, half-duplex
- 115200 baud (default)
- Position range: 0-1000 (maps to 0-240°)
"""

import time
from typing import Optional, Tuple

try:
    import serial
except ImportError:
    serial = None  # Allow running in simulation mode without pyserial


# Command codes
CMD_MOVE_TIME_WRITE = 1
CMD_MOVE_TIME_READ = 2
CMD_MOVE_TIME_WAIT_WRITE = 7
CMD_MOVE_START = 11
CMD_MOVE_STOP = 12
CMD_ID_WRITE = 13
CMD_ID_READ = 14
CMD_ANGLE_OFFSET_ADJUST = 17
CMD_ANGLE_OFFSET_WRITE = 18
CMD_ANGLE_OFFSET_READ = 19
CMD_ANGLE_LIMIT_WRITE = 20
CMD_ANGLE_LIMIT_READ = 21
CMD_VIN_LIMIT_WRITE = 22
CMD_VIN_LIMIT_READ = 23
CMD_TEMP_MAX_LIMIT_WRITE = 24
CMD_TEMP_MAX_LIMIT_READ = 25
CMD_TEMP_READ = 26
CMD_VIN_READ = 27
CMD_POS_READ = 28
CMD_MOTOR_MODE_WRITE = 29
CMD_MOTOR_MODE_READ = 30
CMD_LOAD_OR_UNLOAD_WRITE = 31
CMD_LOAD_OR_UNLOAD_READ = 32
CMD_LED_CTRL_WRITE = 33
CMD_LED_CTRL_READ = 34
CMD_LED_ERROR_WRITE = 35
CMD_LED_ERROR_READ = 36

# Frame header
FRAME_HEADER = 0x55

# Broadcast ID (all servos)
BROADCAST_ID = 254


class LX16A:
    """
    Driver for LX-16A serial bus servos.

    Args:
        port: Serial port path (e.g., '/dev/serial0')
        baudrate: Serial baud rate (default 115200)
        timeout: Read timeout in seconds
        simulation: If True, print commands instead of sending to serial
    """

    def __init__(self, port: str = '/dev/serial0', baudrate: int = 115200,
                 timeout: float = 0.1, simulation: bool = False):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.simulation = simulation
        self.serial: Optional[serial.Serial] = None

        if not simulation:
            if serial is None:
                raise ImportError("pyserial is required. Install with: pip install pyserial")
            self._open()

    def _open(self):
        """Open serial port."""
        if self.simulation:
            return
        self.serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
            write_timeout=self.timeout
        )
        # Clear any pending data
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

    def close(self):
        """Close serial port."""
        if self.serial:
            self.serial.close()
            self.serial = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def _checksum(data: bytes) -> int:
        """
        Calculate LX-16A checksum.
        Sum bytes from index 2 to (length + 2), then bitwise NOT.
        """
        length = data[3]
        total = sum(data[2:length + 2])
        return (~total) & 0xFF

    def _build_packet(self, servo_id: int, cmd: int, params: bytes = b'') -> bytes:
        """
        Build a command packet.

        Frame format: [0x55, 0x55, ID, LENGTH, CMD, PARAMS..., CHECKSUM]
        LENGTH = number of bytes from CMD through PARAMS + 3
        """
        length = len(params) + 3  # CMD + params + checksum byte counted in length
        packet = bytes([
            FRAME_HEADER,
            FRAME_HEADER,
            servo_id,
            length,
            cmd
        ]) + params

        checksum = self._checksum(packet + b'\x00')  # Placeholder for checksum calc
        packet += bytes([checksum])

        return packet

    def _send(self, packet: bytes):
        """Send packet to serial port."""
        if self.simulation:
            print(f"[SIM] TX: {packet.hex(' ')}")
            return

        self.serial.reset_input_buffer()
        self.serial.write(packet)
        self.serial.flush()

    def _receive(self, expected_length: int) -> Optional[bytes]:
        """
        Receive response packet.

        Returns None if no valid response received.
        """
        if self.simulation:
            print(f"[SIM] RX: (simulation - no response)")
            return None

        # Wait for frame header
        start_time = time.time()
        header_count = 0

        while time.time() - start_time < self.timeout:
            if self.serial.in_waiting > 0:
                byte = self.serial.read(1)
                if byte == bytes([FRAME_HEADER]):
                    header_count += 1
                    if header_count == 2:
                        break
                else:
                    header_count = 0

        if header_count < 2:
            return None

        # Read ID and length
        header = self.serial.read(2)
        if len(header) < 2:
            return None

        servo_id, length = header[0], header[1]

        # Read remaining data (length - 1 bytes: cmd + params + checksum - already counted ID)
        remaining = length
        data = self.serial.read(remaining)
        if len(data) < remaining:
            return None

        # Reconstruct full packet for checksum validation
        packet = bytes([FRAME_HEADER, FRAME_HEADER, servo_id, length]) + data

        # Validate checksum
        received_checksum = packet[-1]
        calculated_checksum = self._checksum(packet[:-1] + b'\x00')

        if received_checksum != calculated_checksum:
            print(f"Checksum mismatch: received {received_checksum}, calculated {calculated_checksum}")
            return None

        return packet

    # =========================================================================
    # Motion Commands
    # =========================================================================

    def move(self, servo_id: int, position: int, time_ms: int = 0):
        """
        Move servo to position.

        Args:
            servo_id: Servo ID (1-253, or 254 for broadcast)
            position: Target position (0-1000, maps to 0-240°)
            time_ms: Move duration in milliseconds (0 = max speed)
        """
        position = max(0, min(1000, position))
        time_ms = max(0, min(30000, time_ms))

        params = bytes([
            position & 0xFF,
            (position >> 8) & 0xFF,
            time_ms & 0xFF,
            (time_ms >> 8) & 0xFF
        ])

        packet = self._build_packet(servo_id, CMD_MOVE_TIME_WRITE, params)
        self._send(packet)

    def move_prepare(self, servo_id: int, position: int, time_ms: int = 0):
        """
        Prepare servo move (doesn't execute until move_start called).

        Args:
            servo_id: Servo ID
            position: Target position (0-1000)
            time_ms: Move duration in milliseconds
        """
        position = max(0, min(1000, position))
        time_ms = max(0, min(30000, time_ms))

        params = bytes([
            position & 0xFF,
            (position >> 8) & 0xFF,
            time_ms & 0xFF,
            (time_ms >> 8) & 0xFF
        ])

        packet = self._build_packet(servo_id, CMD_MOVE_TIME_WAIT_WRITE, params)
        self._send(packet)

    def move_start(self, servo_id: int = BROADCAST_ID):
        """
        Start prepared moves.

        Args:
            servo_id: Servo ID (default: broadcast to all)
        """
        packet = self._build_packet(servo_id, CMD_MOVE_START)
        self._send(packet)

    def move_stop(self, servo_id: int):
        """Stop servo motion."""
        packet = self._build_packet(servo_id, CMD_MOVE_STOP)
        self._send(packet)

    # =========================================================================
    # Read Commands
    # =========================================================================

    def read_position(self, servo_id: int) -> Optional[int]:
        """
        Read current position.

        Returns:
            Position (0-1000) or None if read failed
        """
        packet = self._build_packet(servo_id, CMD_POS_READ)
        self._send(packet)

        response = self._receive(8)
        if response is None:
            return None

        # Position is in bytes 5-6 (little-endian)
        pos_low = response[5]
        pos_high = response[6]
        position = pos_low | (pos_high << 8)

        # Handle signed value (can be negative if servo moved past limit)
        if position > 32767:
            position -= 65536

        return position

    def read_voltage(self, servo_id: int) -> Optional[float]:
        """
        Read input voltage.

        Returns:
            Voltage in volts, or None if read failed
        """
        packet = self._build_packet(servo_id, CMD_VIN_READ)
        self._send(packet)

        response = self._receive(8)
        if response is None:
            return None

        # Voltage is in bytes 5-6 (little-endian), in millivolts
        vin_low = response[5]
        vin_high = response[6]
        millivolts = vin_low | (vin_high << 8)

        return millivolts / 1000.0

    def read_temperature(self, servo_id: int) -> Optional[int]:
        """
        Read temperature.

        Returns:
            Temperature in Celsius, or None if read failed
        """
        packet = self._build_packet(servo_id, CMD_TEMP_READ)
        self._send(packet)

        response = self._receive(7)
        if response is None:
            return None

        return response[5]

    def read_id(self, servo_id: int = BROADCAST_ID) -> Optional[int]:
        """
        Read servo ID.

        Use with single servo connected to discover its ID.

        Returns:
            Servo ID, or None if read failed
        """
        packet = self._build_packet(servo_id, CMD_ID_READ)
        self._send(packet)

        response = self._receive(7)
        if response is None:
            return None

        return response[5]

    # =========================================================================
    # Configuration Commands
    # =========================================================================

    def set_id(self, old_id: int, new_id: int):
        """
        Change servo ID.

        Args:
            old_id: Current servo ID
            new_id: New servo ID (1-253)
        """
        new_id = max(1, min(253, new_id))
        params = bytes([new_id])
        packet = self._build_packet(old_id, CMD_ID_WRITE, params)
        self._send(packet)

    def load(self, servo_id: int):
        """Enable servo torque (motor powered)."""
        params = bytes([1])
        packet = self._build_packet(servo_id, CMD_LOAD_OR_UNLOAD_WRITE, params)
        self._send(packet)

    def unload(self, servo_id: int):
        """Disable servo torque (motor unpowered, can be moved by hand)."""
        params = bytes([0])
        packet = self._build_packet(servo_id, CMD_LOAD_OR_UNLOAD_WRITE, params)
        self._send(packet)

    def set_angle_limits(self, servo_id: int, min_pos: int, max_pos: int):
        """
        Set servo angle limits.

        Args:
            servo_id: Servo ID
            min_pos: Minimum position (0-1000)
            max_pos: Maximum position (0-1000)
        """
        min_pos = max(0, min(1000, min_pos))
        max_pos = max(0, min(1000, max_pos))

        params = bytes([
            min_pos & 0xFF,
            (min_pos >> 8) & 0xFF,
            max_pos & 0xFF,
            (max_pos >> 8) & 0xFF
        ])

        packet = self._build_packet(servo_id, CMD_ANGLE_LIMIT_WRITE, params)
        self._send(packet)

    def set_angle_offset(self, servo_id: int, offset: int):
        """
        Set servo angle offset (trim).

        Args:
            servo_id: Servo ID
            offset: Offset value (-125 to 125)
        """
        offset = max(-125, min(125, offset))
        if offset < 0:
            offset = 256 + offset  # Convert to unsigned byte

        params = bytes([offset])
        packet = self._build_packet(servo_id, CMD_ANGLE_OFFSET_ADJUST, params)
        self._send(packet)

    def save_angle_offset(self, servo_id: int):
        """Save current angle offset to servo EEPROM."""
        packet = self._build_packet(servo_id, CMD_ANGLE_OFFSET_WRITE)
        self._send(packet)

    def set_led(self, servo_id: int, on: bool):
        """
        Control servo LED.

        Args:
            servo_id: Servo ID
            on: True to turn LED on, False to turn off
        """
        params = bytes([0 if on else 1])  # 0 = on, 1 = off (inverted)
        packet = self._build_packet(servo_id, CMD_LED_CTRL_WRITE, params)
        self._send(packet)

    def set_motor_mode(self, servo_id: int, speed: int):
        """
        Set continuous rotation mode.

        Args:
            servo_id: Servo ID
            speed: Rotation speed (-1000 to 1000, 0 = stop)
        """
        speed = max(-1000, min(1000, speed))

        # Convert signed speed to unsigned
        if speed < 0:
            speed_unsigned = 65536 + speed
        else:
            speed_unsigned = speed

        params = bytes([
            1,  # Mode 1 = motor mode
            0,  # Reserved
            speed_unsigned & 0xFF,
            (speed_unsigned >> 8) & 0xFF
        ])

        packet = self._build_packet(servo_id, CMD_MOTOR_MODE_WRITE, params)
        self._send(packet)

    def set_servo_mode(self, servo_id: int):
        """Set servo mode (position control, default)."""
        params = bytes([0, 0, 0, 0])  # Mode 0 = servo mode
        packet = self._build_packet(servo_id, CMD_MOTOR_MODE_WRITE, params)
        self._send(packet)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def position_to_angle(self, position: int) -> float:
        """Convert position (0-1000) to angle in degrees (0-240)."""
        return position * 240.0 / 1000.0

    def angle_to_position(self, angle: float) -> int:
        """Convert angle in degrees (0-240) to position (0-1000)."""
        return int(angle * 1000.0 / 240.0)

    def scan(self, start_id: int = 1, end_id: int = 253) -> list:
        """
        Scan for connected servos.

        Args:
            start_id: First ID to scan
            end_id: Last ID to scan

        Returns:
            List of found servo IDs
        """
        found = []
        original_timeout = self.timeout
        self.timeout = 0.05  # Shorter timeout for scanning

        if self.serial:
            self.serial.timeout = self.timeout

        for servo_id in range(start_id, end_id + 1):
            pos = self.read_position(servo_id)
            if pos is not None:
                found.append(servo_id)
                print(f"Found servo ID {servo_id} at position {pos}")

        self.timeout = original_timeout
        if self.serial:
            self.serial.timeout = self.timeout

        return found


# =============================================================================
# Convenience functions
# =============================================================================

def create_bus(port: str = '/dev/serial0', simulation: bool = False) -> LX16A:
    """Create an LX-16A servo bus instance."""
    return LX16A(port=port, simulation=simulation)


if __name__ == '__main__':
    # Simple test in simulation mode
    print("LX-16A Driver Test (Simulation Mode)")
    print("=" * 40)

    bus = LX16A(simulation=True)

    # Test move command
    print("\nMove servo 1 to position 500 over 1000ms:")
    bus.move(1, 500, 1000)

    # Test prepared moves
    print("\nPrepare moves for servos 1-3:")
    bus.move_prepare(1, 300, 500)
    bus.move_prepare(2, 500, 500)
    bus.move_prepare(3, 700, 500)
    print("Start all prepared moves:")
    bus.move_start()

    # Test read commands
    print("\nRead position from servo 1:")
    bus.read_position(1)

    print("\nRead voltage from servo 1:")
    bus.read_voltage(1)

    # Test configuration
    print("\nSet servo 1 angle limits (100-900):")
    bus.set_angle_limits(1, 100, 900)

    print("\nUnload servo 1 (disable torque):")
    bus.unload(1)

    print("\n" + "=" * 40)
    print("Simulation test complete!")
