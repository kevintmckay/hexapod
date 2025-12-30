"""
Hexapod Robot Controller
For Pi Pico (MicroPython) or Pi Zero (CPython)

Hardware:
- 2x PCA9685 PWM drivers (I2C 0x40, 0x41)
- 18x Tower Pro SG90 servos (all joints: coxa, femur, tibia)
- 3S Li-Ion battery (11.1V) with 5V BEC
"""

import json
import os
from math import atan2, acos, sqrt, degrees, radians, cos, sin

# Leg geometry (mm) - adjust to match your 3D printed parts
COXA_LENGTH = 25
FEMUR_LENGTH = 55
TIBIA_LENGTH = 75

# Servo PWM defaults (overridden by calibration file)
SERVO_MIN = 500   # 0 degrees
SERVO_MAX = 2500  # 180 degrees
SERVO_CENTER = 1500  # 90 degrees

# Leg numbering (top view, front is 0 degrees)
#      FRONT (0)
#   L1       R1    (330, 30)
#   L2--[B]--R2    (270, 90)
#   L3       R3    (210, 150)
#      REAR (180)

LEG_ANGLES = {
    'L1': 330, 'R1': 30,
    'L2': 270, 'R2': 90,
    'L3': 210, 'R3': 150,
}

# Default servo channel mapping (pca_index, channel)
# Channels 0-15 on PCA9685 #1 (0x40), 16-31 on #2 (0x41)
DEFAULT_SERVO_MAP = {
    'L1': {'coxa': (0, 0), 'femur': (0, 1), 'tibia': (0, 2)},
    'L2': {'coxa': (0, 3), 'femur': (0, 4), 'tibia': (0, 5)},
    'L3': {'coxa': (0, 6), 'femur': (0, 7), 'tibia': (0, 8)},
    'R1': {'coxa': (0, 9), 'femur': (0, 10), 'tibia': (0, 11)},
    'R2': {'coxa': (1, 0), 'femur': (1, 1), 'tibia': (1, 2)},
    'R3': {'coxa': (1, 3), 'femur': (1, 4), 'tibia': (1, 5)},
}

# Default servo directions (1 or -1 to flip)
DEFAULT_SERVO_DIR = {
    'L1': {'coxa': 1, 'femur': 1, 'tibia': 1},
    'L2': {'coxa': 1, 'femur': 1, 'tibia': 1},
    'L3': {'coxa': 1, 'femur': 1, 'tibia': 1},
    'R1': {'coxa': -1, 'femur': -1, 'tibia': -1},
    'R2': {'coxa': -1, 'femur': -1, 'tibia': -1},
    'R3': {'coxa': -1, 'femur': -1, 'tibia': -1},
}


def clamp(val, min_val, max_val):
    """Clamp value to range."""
    return max(min_val, min(max_val, val))


def leg_ik(x, y, z, coxa_len=COXA_LENGTH, femur_len=FEMUR_LENGTH, tibia_len=TIBIA_LENGTH):
    """
    Inverse kinematics for single leg.

    Args:
        x: Forward/back from coxa pivot (mm)
        y: Left/right from coxa pivot (mm)
        z: Up/down from coxa pivot (mm, negative = down)
        coxa_len, femur_len, tibia_len: Link lengths (mm)

    Returns:
        (coxa_angle, femur_angle, tibia_angle) in degrees
        Angles are servo positions (0-180, 90 = center)
        Returns None if target is completely unreachable.
    """
    # Handle edge case: target at origin
    if x == 0 and y == 0:
        x = 0.1  # Small offset to avoid atan2(0,0)

    # Coxa angle (rotation in XY plane)
    coxa_angle = degrees(atan2(y, x))

    # Horizontal distance from coxa to foot
    xy_dist = sqrt(x**2 + y**2) - coxa_len

    # Handle case where target is inside coxa length
    if xy_dist < 0:
        xy_dist = 1  # Minimum reach

    # Direct distance from femur pivot to foot
    foot_dist = sqrt(xy_dist**2 + z**2)

    # Check reachability
    max_reach = femur_len + tibia_len
    min_reach = abs(femur_len - tibia_len)

    clamped = False
    if foot_dist > max_reach or foot_dist < min_reach:
        # Out of reach - clamp to nearest valid
        foot_dist = clamp(foot_dist, min_reach + 1, max_reach - 1)
        clamped = True

    # Tibia angle (law of cosines)
    cos_tibia = (femur_len**2 + tibia_len**2 - foot_dist**2) / \
                (2 * femur_len * tibia_len)
    tibia_angle = degrees(acos(clamp(cos_tibia, -1, 1)))

    # Femur angle
    cos_femur = (femur_len**2 + foot_dist**2 - tibia_len**2) / \
                (2 * femur_len * foot_dist)
    femur_angle = degrees(atan2(-z, xy_dist)) + degrees(acos(clamp(cos_femur, -1, 1)))

    # Convert to servo angles (centered at 90)
    coxa_servo = 90 + coxa_angle
    femur_servo = femur_angle
    tibia_servo = 180 - tibia_angle  # Tibia typically inverted

    # Clamp all angles to valid servo range (0-180)
    coxa_servo = clamp(coxa_servo, 0, 180)
    femur_servo = clamp(femur_servo, 0, 180)
    tibia_servo = clamp(tibia_servo, 0, 180)

    if clamped:
        print(f"Warning: IK target ({x:.1f}, {y:.1f}, {z:.1f}) out of reach, clamped")

    return coxa_servo, femur_servo, tibia_servo


class Hexapod:
    """Main hexapod controller class."""

    def __init__(self, pca_drivers=None, calibration_file='calibration.json', simulate=False):
        """
        Args:
            pca_drivers: List of 2 PCA9685 driver instances (or None for simulation)
            calibration_file: Path to calibration JSON file
            simulate: If True, don't access hardware
        """
        self.simulate = simulate or pca_drivers is None
        self.pca = pca_drivers or [None, None]

        # Load calibration or use defaults
        self.calibration = self._load_calibration(calibration_file)

        # Build servo map from calibration
        self._build_servo_map()

        # Track leg positions (x, y, z) for each leg
        self.leg_positions = {}
        for leg in self.servo_map.keys():
            self.leg_positions[leg] = (80, 0, -50)  # Default standing

    def _load_calibration(self, calibration_file):
        """Load calibration from JSON file."""
        if os.path.exists(calibration_file):
            try:
                with open(calibration_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load calibration: {e}")
        return None

    def _build_servo_map(self):
        """Build servo map from calibration or defaults."""
        self.servo_map = {}
        self.servo_dir = {}
        self.servo_range = {}

        legs = ['L1', 'L2', 'L3', 'R1', 'R2', 'R3']
        joints = ['coxa', 'femur', 'tibia']

        for leg in legs:
            self.servo_map[leg] = {}
            self.servo_dir[leg] = {}
            self.servo_range[leg] = {}

            for joint in joints:
                if self.calibration and leg in self.calibration:
                    cal = self.calibration[leg][joint]
                    channel = cal['channel']
                    pca_idx = 0 if channel < 16 else 1
                    ch = channel if channel < 16 else channel - 16

                    self.servo_map[leg][joint] = (pca_idx, ch)
                    self.servo_dir[leg][joint] = cal.get('direction', 1)
                    self.servo_range[leg][joint] = {
                        'min': cal.get('min', SERVO_MIN),
                        'max': cal.get('max', SERVO_MAX),
                        'center': cal.get('center', SERVO_CENTER),
                    }
                else:
                    # Use defaults
                    self.servo_map[leg][joint] = DEFAULT_SERVO_MAP[leg][joint]
                    self.servo_dir[leg][joint] = DEFAULT_SERVO_DIR[leg][joint]
                    self.servo_range[leg][joint] = {
                        'min': SERVO_MIN,
                        'max': SERVO_MAX,
                        'center': SERVO_CENTER,
                    }

    def angle_to_pulse(self, leg, joint, angle):
        """Convert angle (0-180) to calibrated PWM pulse width (us)."""
        angle = clamp(angle, 0, 180)
        sr = self.servo_range[leg][joint]

        # Map 0-180 to min-max pulse range
        pulse = sr['min'] + (angle / 180.0) * (sr['max'] - sr['min'])
        return int(pulse)

    def set_servo(self, leg, joint, angle):
        """Set single servo to angle (0-180 degrees)."""
        pca_idx, channel = self.servo_map[leg][joint]
        direction = self.servo_dir[leg][joint]

        # Apply direction (flip if needed)
        if direction < 0:
            angle = 180 - angle

        pulse = self.angle_to_pulse(leg, joint, angle)

        if self.simulate:
            # Just track the position
            pass
        else:
            self.pca[pca_idx].set_pwm(channel, pulse)

    def move_leg(self, leg, x, y, z):
        """Move single leg to position using IK."""
        coxa, femur, tibia = leg_ik(x, y, z)

        self.set_servo(leg, 'coxa', coxa)
        self.set_servo(leg, 'femur', femur)
        self.set_servo(leg, 'tibia', tibia)

        self.leg_positions[leg] = (x, y, z)

    def stand(self, height=50):
        """
        Move to standing position.

        Coordinate System:
        - Each leg's IK uses a local coordinate frame where:
          - X axis points outward from the body along the leg's mounting angle
          - Y axis is perpendicular to X in the horizontal plane
          - Z axis points up (negative Z = down toward ground)
        - The LEG_ANGLES define each leg's mounting angle in world frame
        - We calculate (x, y) in world frame then pass to move_leg()
        - The IK interprets these as leg-local coordinates
        """
        for leg in self.servo_map.keys():
            # Position legs outward based on their mounting angle
            # This creates a symmetric stance where each leg points outward
            angle_rad = radians(LEG_ANGLES[leg])
            x = 80 * cos(angle_rad)
            y = 80 * sin(angle_rad)
            self.move_leg(leg, x, y, -height)

    def center_all(self):
        """Move all servos to 90 degrees (calibration position)."""
        for leg in self.servo_map.keys():
            for joint in ['coxa', 'femur', 'tibia']:
                self.set_servo(leg, joint, 90)

    def shutdown(self):
        """Disable all servos (no holding torque)."""
        if self.simulate:
            return

        # Disable only the channels we're actually using
        for leg in self.servo_map:
            for joint in self.servo_map[leg]:
                pca_idx, channel = self.servo_map[leg][joint]
                if self.pca[pca_idx]:
                    self.pca[pca_idx].set_pwm(channel, 0)

    def get_leg_position(self, leg):
        """Get current (x, y, z) position of leg."""
        return self.leg_positions.get(leg, (80, 0, -50))


def create_hexapod(simulate=False):
    """
    Factory function to create a Hexapod with drivers initialized.

    Args:
        simulate: If True, run without hardware

    Returns:
        Hexapod instance
    """
    if simulate:
        return Hexapod(pca_drivers=None, simulate=True)

    try:
        from pca9685 import PCA9685
        pca1 = PCA9685(address=0x40, freq=50)
        pca2 = PCA9685(address=0x41, freq=50)
        return Hexapod(pca_drivers=[pca1, pca2])
    except Exception as e:
        print(f"Hardware init failed: {e}")
        print("Running in simulation mode")
        return Hexapod(pca_drivers=None, simulate=True)


if __name__ == '__main__':
    # Test IK calculations
    print("Hexapod IK Test")
    print("=" * 40)

    test_positions = [
        (80, 0, -50),   # Default stand
        (100, 0, -30),  # Leg extended forward
        (60, 30, -60),  # Leg to side and down
        (50, 0, -80),   # Leg tucked under
    ]

    for x, y, z in test_positions:
        angles = leg_ik(x, y, z)
        print(f"\nPosition ({x}, {y}, {z}):")
        print(f"  Coxa:  {angles[0]:.1f} deg")
        print(f"  Femur: {angles[1]:.1f} deg")
        print(f"  Tibia: {angles[2]:.1f} deg")

    # Test hexapod in simulation
    print("\n" + "=" * 40)
    print("Creating hexapod (simulation mode)...")
    hex = create_hexapod(simulate=True)
    hex.stand()
    print("Standing position set")
    print(f"L1 position: {hex.get_leg_position('L1')}")
