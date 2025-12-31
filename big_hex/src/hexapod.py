"""
Big Hex - Hexapod Robot Controller

Main controller for 18-servo hexapod using LX-16A serial bus servos.
Includes inverse kinematics and leg coordination.
"""

import json
import os
from math import atan2, acos, sqrt, degrees, radians, cos, sin
from typing import Dict, List, Optional, Tuple

from lx16a import LX16A, BROADCAST_ID


# =============================================================================
# Geometry (from CAD - leg.scad)
# =============================================================================

COXA_LENGTH = 50    # mm - hip segment
FEMUR_LENGTH = 80   # mm - upper leg
TIBIA_LENGTH = 120  # mm - lower leg
BODY_RADIUS = 175   # mm - center to leg mount

# Leg positions around body (degrees from front, counterclockwise)
# Front is 0°, looking down from above
#
#      FRONT (0°)
#   L1 (30°)    R1 (330°)
#   L2 (90°)    R2 (270°)
#   L3 (150°)   R3 (210°)
#      REAR (180°)

LEG_ANGLES = {
    'L1': 30,   'R1': 330,
    'L2': 90,   'R2': 270,
    'L3': 150,  'R3': 210,
}

# Default servo ID mapping
# Each leg has 3 servos: coxa (hip), femur (upper), tibia (lower)
DEFAULT_SERVO_IDS = {
    'L1': {'coxa': 1,  'femur': 2,  'tibia': 3},
    'L2': {'coxa': 4,  'femur': 5,  'tibia': 6},
    'L3': {'coxa': 7,  'femur': 8,  'tibia': 9},
    'R1': {'coxa': 10, 'femur': 11, 'tibia': 12},
    'R2': {'coxa': 13, 'femur': 14, 'tibia': 15},
    'R3': {'coxa': 16, 'femur': 17, 'tibia': 18},
}

# Servo direction (1 = normal, -1 = reversed)
# Right side legs are mirrored
DEFAULT_SERVO_DIR = {
    'L1': {'coxa': 1, 'femur': 1, 'tibia': 1},
    'L2': {'coxa': 1, 'femur': 1, 'tibia': 1},
    'L3': {'coxa': 1, 'femur': 1, 'tibia': 1},
    'R1': {'coxa': -1, 'femur': -1, 'tibia': -1},
    'R2': {'coxa': -1, 'femur': -1, 'tibia': -1},
    'R3': {'coxa': -1, 'femur': -1, 'tibia': -1},
}


# =============================================================================
# Utility Functions
# =============================================================================

def clamp(val: float, min_val: float, max_val: float) -> float:
    """Clamp value to range."""
    return max(min_val, min(max_val, val))


def leg_ik(x: float, y: float, z: float,
           coxa_len: float = COXA_LENGTH,
           femur_len: float = FEMUR_LENGTH,
           tibia_len: float = TIBIA_LENGTH) -> Optional[Tuple[float, float, float]]:
    """
    Inverse kinematics for single leg.

    Coordinate system (leg's local frame):
        x: Forward/back from coxa pivot (positive = forward)
        y: Left/right from coxa pivot (positive = outward from body)
        z: Up/down from coxa pivot (negative = down)

    Args:
        x, y, z: Target foot position in mm
        coxa_len, femur_len, tibia_len: Link lengths in mm

    Returns:
        (coxa_angle, femur_angle, tibia_angle) in degrees (0-240 range for LX-16A)
        Returns None if target is unreachable.
    """
    # Handle edge case: target at origin
    if x == 0 and y == 0:
        x = 0.1

    # Coxa angle (rotation in XY plane)
    coxa_angle = degrees(atan2(y, x))

    # Horizontal distance from coxa pivot to foot
    xy_dist = sqrt(x**2 + y**2) - coxa_len

    if xy_dist < 0:
        xy_dist = 1  # Minimum reach

    # Direct distance from femur pivot to foot
    foot_dist = sqrt(xy_dist**2 + z**2)

    # Check reachability
    max_reach = femur_len + tibia_len
    min_reach = abs(femur_len - tibia_len)

    if foot_dist > max_reach or foot_dist < min_reach:
        # Clamp to nearest valid distance
        foot_dist = clamp(foot_dist, min_reach + 1, max_reach - 1)

    # Tibia angle (law of cosines)
    cos_tibia = (femur_len**2 + tibia_len**2 - foot_dist**2) / (2 * femur_len * tibia_len)
    tibia_angle = degrees(acos(clamp(cos_tibia, -1, 1)))

    # Femur angle
    cos_femur = (femur_len**2 + foot_dist**2 - tibia_len**2) / (2 * femur_len * foot_dist)
    femur_angle = degrees(atan2(-z, xy_dist)) + degrees(acos(clamp(cos_femur, -1, 1)))

    # Convert to servo angles
    # LX-16A range is 0-240° (position 0-1000), center at 120° (position 500)
    coxa_servo = 120 + coxa_angle
    femur_servo = femur_angle + 30  # Offset for mechanical zero
    tibia_servo = 240 - tibia_angle  # Inverted

    # Clamp to valid range
    coxa_servo = clamp(coxa_servo, 0, 240)
    femur_servo = clamp(femur_servo, 0, 240)
    tibia_servo = clamp(tibia_servo, 0, 240)

    return coxa_servo, femur_servo, tibia_servo


# =============================================================================
# Hexapod Controller
# =============================================================================

class Hexapod:
    """
    Main hexapod robot controller.

    Controls 18 LX-16A servos (6 legs × 3 joints) with inverse kinematics.
    """

    def __init__(self, port: str = '/dev/serial0', config_file: str = 'config.json',
                 simulation: bool = False):
        """
        Initialize hexapod controller.

        Args:
            port: Serial port for LX-16A bus
            config_file: Path to configuration JSON file
            simulation: If True, run without hardware
        """
        self.simulation = simulation
        self.config_file = config_file

        # Initialize servo bus
        self.bus = LX16A(port=port, simulation=simulation)

        # Load configuration
        self.config = self._load_config()

        # Geometry from config or defaults
        self.coxa_len = self.config.get('geometry', {}).get('coxa_length', COXA_LENGTH)
        self.femur_len = self.config.get('geometry', {}).get('femur_length', FEMUR_LENGTH)
        self.tibia_len = self.config.get('geometry', {}).get('tibia_length', TIBIA_LENGTH)
        self.body_radius = self.config.get('geometry', {}).get('body_radius', BODY_RADIUS)

        # Servo mapping
        self.servo_ids = self.config.get('servo_ids', DEFAULT_SERVO_IDS)
        self.servo_dir = self.config.get('servo_directions', DEFAULT_SERVO_DIR)

        # Calibration offsets (position offset for each servo)
        self.calibration = self.config.get('calibration', {})

        # Body pose
        self.body_height = 80  # mm
        self.body_pitch = 0    # degrees
        self.body_roll = 0     # degrees
        self.body_yaw = 0      # degrees

        # Current leg positions (local coordinates)
        self.leg_positions: Dict[str, Tuple[float, float, float]] = {}
        self._reset_positions()

    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config: {e}")
        return {}

    def save_config(self):
        """Save current configuration to JSON file."""
        config = {
            'serial_port': self.bus.port,
            'geometry': {
                'coxa_length': self.coxa_len,
                'femur_length': self.femur_len,
                'tibia_length': self.tibia_len,
                'body_radius': self.body_radius,
            },
            'servo_ids': self.servo_ids,
            'servo_directions': self.servo_dir,
            'calibration': self.calibration,
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def _reset_positions(self):
        """Reset all leg positions to default standing pose."""
        for leg in LEG_ANGLES:
            # Default: foot at comfortable stance position
            self.leg_positions[leg] = (100, 0, -self.body_height)

    # =========================================================================
    # Servo Control
    # =========================================================================

    def _angle_to_position(self, angle: float, servo_id: int, leg: str, joint: str) -> int:
        """
        Convert angle (0-240°) to servo position (0-1000).

        Applies direction and calibration offset.
        """
        # Apply direction
        direction = self.servo_dir.get(leg, {}).get(joint, 1)
        if direction < 0:
            angle = 240 - angle

        # Convert to position
        position = int(angle * 1000 / 240)

        # Apply calibration offset
        offset = self.calibration.get(str(servo_id), {}).get('offset', 0)
        position += offset

        return clamp(position, 0, 1000)

    def set_servo(self, leg: str, joint: str, angle: float, time_ms: int = 0):
        """
        Set a single servo angle.

        Args:
            leg: Leg name ('L1', 'L2', 'L3', 'R1', 'R2', 'R3')
            joint: Joint name ('coxa', 'femur', 'tibia')
            angle: Target angle in degrees (0-240)
            time_ms: Move time in milliseconds (0 = max speed)
        """
        servo_id = self.servo_ids[leg][joint]
        position = self._angle_to_position(angle, servo_id, leg, joint)
        self.bus.move(servo_id, position, time_ms)

    def set_leg_angles(self, leg: str, coxa: float, femur: float, tibia: float,
                       time_ms: int = 0):
        """
        Set all three servo angles for a leg.

        Args:
            leg: Leg name
            coxa, femur, tibia: Joint angles in degrees (0-240)
            time_ms: Move time in milliseconds
        """
        self.set_servo(leg, 'coxa', coxa, time_ms)
        self.set_servo(leg, 'femur', femur, time_ms)
        self.set_servo(leg, 'tibia', tibia, time_ms)

    # =========================================================================
    # Leg Movement (with IK)
    # =========================================================================

    def move_leg(self, leg: str, x: float, y: float, z: float, time_ms: int = 0):
        """
        Move leg to position using inverse kinematics.

        Args:
            leg: Leg name
            x, y, z: Target foot position in leg's local coordinates (mm)
            time_ms: Move time in milliseconds
        """
        angles = leg_ik(x, y, z, self.coxa_len, self.femur_len, self.tibia_len)

        if angles is None:
            print(f"Warning: Position ({x}, {y}, {z}) unreachable for {leg}")
            return

        coxa, femur, tibia = angles
        self.set_leg_angles(leg, coxa, femur, tibia, time_ms)
        self.leg_positions[leg] = (x, y, z)

    def move_leg_relative(self, leg: str, dx: float, dy: float, dz: float,
                          time_ms: int = 0):
        """Move leg relative to current position."""
        x, y, z = self.leg_positions[leg]
        self.move_leg(leg, x + dx, y + dy, z + dz, time_ms)

    def move_all_legs(self, positions: Dict[str, Tuple[float, float, float]],
                      time_ms: int = 0):
        """
        Move multiple legs simultaneously.

        Uses prepared moves for synchronization.

        Args:
            positions: Dict mapping leg names to (x, y, z) positions
            time_ms: Move time in milliseconds
        """
        for leg, (x, y, z) in positions.items():
            angles = leg_ik(x, y, z, self.coxa_len, self.femur_len, self.tibia_len)
            if angles is None:
                continue

            coxa, femur, tibia = angles

            # Prepare moves (don't execute yet)
            for joint, angle in [('coxa', coxa), ('femur', femur), ('tibia', tibia)]:
                servo_id = self.servo_ids[leg][joint]
                position = self._angle_to_position(angle, servo_id, leg, joint)
                self.bus.move_prepare(servo_id, position, time_ms)

            self.leg_positions[leg] = (x, y, z)

        # Execute all prepared moves simultaneously
        self.bus.move_start()

    # =========================================================================
    # Body Poses
    # =========================================================================

    def stand(self, height: float = None, time_ms: int = 500):
        """
        Move to standing position.

        Args:
            height: Body height in mm (default: self.body_height)
            time_ms: Move time
        """
        h = height or self.body_height
        positions = {}

        for leg, angle_deg in LEG_ANGLES.items():
            # Stance position: foot below and outward from leg mount
            angle_rad = radians(angle_deg)
            x = 100 * cos(angle_rad)  # Forward component
            y = 100 * sin(angle_rad)  # Sideways component
            z = -h

            # Convert from body coords to leg local coords
            # For now, simplified: just use distance from body
            positions[leg] = (100, 0, -h)

        self.move_all_legs(positions, time_ms)
        self.body_height = h

    def sit(self, time_ms: int = 500):
        """Lower body to sitting position."""
        self.stand(height=30, time_ms=time_ms)

    def center_all(self, time_ms: int = 500):
        """Move all servos to center position (120°)."""
        for leg in LEG_ANGLES:
            for joint in ['coxa', 'femur', 'tibia']:
                servo_id = self.servo_ids[leg][joint]
                self.bus.move_prepare(servo_id, 500, time_ms)  # 500 = center
        self.bus.move_start()

    # =========================================================================
    # Servo Management
    # =========================================================================

    def load_all(self):
        """Enable torque on all servos."""
        for leg in LEG_ANGLES:
            for joint in ['coxa', 'femur', 'tibia']:
                servo_id = self.servo_ids[leg][joint]
                self.bus.load(servo_id)

    def unload_all(self):
        """Disable torque on all servos (can be moved by hand)."""
        for leg in LEG_ANGLES:
            for joint in ['coxa', 'femur', 'tibia']:
                servo_id = self.servo_ids[leg][joint]
                self.bus.unload(servo_id)

    def read_all_positions(self) -> Dict[str, Dict[str, int]]:
        """
        Read current position of all servos.

        Returns:
            Dict mapping leg -> joint -> position
        """
        positions = {}
        for leg in LEG_ANGLES:
            positions[leg] = {}
            for joint in ['coxa', 'femur', 'tibia']:
                servo_id = self.servo_ids[leg][joint]
                pos = self.bus.read_position(servo_id)
                positions[leg][joint] = pos
        return positions

    def read_all_voltages(self) -> Dict[int, float]:
        """Read voltage from all servos (useful for diagnosing power issues)."""
        voltages = {}
        for leg in LEG_ANGLES:
            for joint in ['coxa', 'femur', 'tibia']:
                servo_id = self.servo_ids[leg][joint]
                voltage = self.bus.read_voltage(servo_id)
                if voltage is not None:
                    voltages[servo_id] = voltage
        return voltages

    def close(self):
        """Close serial connection."""
        self.bus.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# =============================================================================
# Main (Test)
# =============================================================================

if __name__ == '__main__':
    print("Big Hex Controller Test (Simulation Mode)")
    print("=" * 50)

    with Hexapod(simulation=True) as hex:
        print("\nStanding up...")
        hex.stand(height=80, time_ms=1000)

        print("\nReading leg positions:")
        for leg, pos in hex.leg_positions.items():
            print(f"  {leg}: {pos}")

        print("\nMoving L1 forward...")
        hex.move_leg('L1', 120, 0, -80, 500)

        print("\nCentering all servos...")
        hex.center_all(500)

        print("\nSitting down...")
        hex.sit(1000)

    print("\n" + "=" * 50)
    print("Simulation test complete!")
