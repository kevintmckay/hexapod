"""
Hexapod Gait Patterns

Ported from mithi/hexy (Python 2) to Python 3.
Provides walking, rotation, and body movement patterns.
"""

from time import sleep


class GaitController:
    """
    Gait controller for hexapod locomotion.

    Implements tripod gait (fastest), wave gait (most stable),
    and various body movements.
    """

    def __init__(self, hexapod):
        """
        Args:
            hexapod: Hexapod instance with legs and movement methods
        """
        self.hex = hexapod

        # Leg groupings for tripod gait
        # Tripod 1: L1, R2, L3 (front-left, mid-right, back-left)
        # Tripod 2: R1, L2, R3 (front-right, mid-left, back-right)
        self.tripod1 = ['L1', 'R2', 'L3']
        self.tripod2 = ['R1', 'L2', 'R3']

        self.left_legs = ['L1', 'L2', 'L3']
        self.right_legs = ['R1', 'R2', 'R3']

        self.front_legs = ['L1', 'R1']
        self.middle_legs = ['L2', 'R2']
        self.back_legs = ['L3', 'R3']

        # Default positions (x, y, z) relative to each leg's origin
        self.stand_height = 50  # mm below coxa
        self.stance_width = 80  # mm out from body

    # =========================================================================
    # Basic Movements
    # =========================================================================

    def stand(self, height=None):
        """Move to neutral standing position."""
        h = height or self.stand_height
        for leg in self.hex.leg_positions.keys():
            x, y, _ = self.hex.leg_positions[leg]
            self.hex.move_leg(leg, x, y, -h)

    def sit(self, height=20):
        """Lower body to sitting position."""
        self.stand(height)

    def squat(self, angle_offset=0):
        """
        Squat by bending knees uniformly.

        Args:
            angle_offset: Positive = lower, negative = higher
        """
        base_z = -self.stand_height - angle_offset
        for leg in self.hex.leg_positions.keys():
            x, y, _ = self.hex.leg_positions[leg]
            self.hex.move_leg(leg, x, y, base_z)

    # =========================================================================
    # Tripod Gait (Walking)
    # =========================================================================

    def walk(self, direction=0, steps=4, step_length=40, step_height=30,
             cycle_time=0.4):
        """
        Walk using tripod gait.

        Args:
            direction: Movement direction in degrees (0=forward, 180=backward)
            steps: Number of complete gait cycles
            step_length: How far each step moves (mm)
            step_height: How high to lift legs (mm)
            cycle_time: Time for one complete cycle (seconds)
        """
        import math

        # Convert direction to x/y components
        rad = math.radians(direction)
        dx = step_length * math.cos(rad)
        dy = step_length * math.sin(rad)

        half_cycle = cycle_time / 2

        for _ in range(steps):
            # Phase 1: Tripod 1 swings forward, Tripod 2 pushes back
            self._tripod_step(self.tripod1, self.tripod2, dx, dy,
                            step_height, half_cycle)

            # Phase 2: Tripod 2 swings forward, Tripod 1 pushes back
            self._tripod_step(self.tripod2, self.tripod1, dx, dy,
                            step_height, half_cycle)

    def _tripod_step(self, swing_legs, stance_legs, dx, dy, lift_height, t):
        """
        Execute one half of tripod gait cycle.

        Args:
            swing_legs: Legs that lift and swing forward
            stance_legs: Legs that stay on ground and push back
            dx, dy: Step direction components
            lift_height: How high to lift swing legs
            t: Time for this phase
        """
        # Lift swing legs
        for leg in swing_legs:
            x, y, z = self.hex.leg_positions[leg]
            self.hex.move_leg(leg, x, y, z + lift_height)

        sleep(t / 3)

        # Swing forward while stance legs push back
        for leg in swing_legs:
            x, y, z = self.hex.leg_positions[leg]
            # Move forward (swing)
            self.hex.move_leg(leg, x + dx/2, y + dy/2, z)

        for leg in stance_legs:
            x, y, z = self.hex.leg_positions[leg]
            # Push back (propel body forward)
            self.hex.move_leg(leg, x - dx/2, y - dy/2, z)

        sleep(t / 3)

        # Lower swing legs
        for leg in swing_legs:
            x, y, z = self.hex.leg_positions[leg]
            self.hex.move_leg(leg, x, y, -self.stand_height)

        sleep(t / 3)

    # =========================================================================
    # Rotation
    # =========================================================================

    def rotate(self, angle=30, steps=4, step_height=25, cycle_time=0.4):
        """
        Rotate in place using tripod gait.

        Args:
            angle: Rotation per cycle in degrees (positive=CCW, negative=CW)
            steps: Number of rotation cycles
            step_height: How high to lift legs
            cycle_time: Time for one cycle
        """
        import math

        half_cycle = cycle_time / 2
        rad = math.radians(angle / 2)

        for _ in range(steps):
            # Phase 1: Lift tripod 1, rotate tripod 2
            self._rotate_tripod(self.tripod1, self.tripod2, rad,
                              step_height, half_cycle)

            # Phase 2: Lift tripod 2, rotate tripod 1
            self._rotate_tripod(self.tripod2, self.tripod1, rad,
                              step_height, half_cycle)

    def _rotate_tripod(self, swing_legs, stance_legs, rad, lift_height, t):
        """Execute rotation with one tripod lifted."""
        import math

        # Lift swing legs
        for leg in swing_legs:
            x, y, z = self.hex.leg_positions[leg]
            self.hex.move_leg(leg, x, y, z + lift_height)

        sleep(t / 2)

        # Rotate positions
        cos_r, sin_r = math.cos(rad), math.sin(rad)

        for leg in swing_legs:
            x, y, z = self.hex.leg_positions[leg]
            # Rotate swing legs in direction of turn
            new_x = x * cos_r - y * sin_r
            new_y = x * sin_r + y * cos_r
            self.hex.move_leg(leg, new_x, new_y, -self.stand_height)

        for leg in stance_legs:
            x, y, z = self.hex.leg_positions[leg]
            # Rotate stance legs opposite (pushes body)
            new_x = x * cos_r + y * sin_r
            new_y = -x * sin_r + y * cos_r
            self.hex.move_leg(leg, new_x, new_y, z)

        sleep(t / 2)

    # =========================================================================
    # Body Movements (from hexy)
    # =========================================================================

    def tilt_forward(self, angle=20):
        """Tilt body forward (front down, back up)."""
        front_z = -self.stand_height - angle
        back_z = -self.stand_height + angle
        mid_z = -self.stand_height

        for leg in self.front_legs:
            x, y, _ = self.hex.leg_positions[leg]
            self.hex.move_leg(leg, x, y, front_z)
        for leg in self.middle_legs:
            x, y, _ = self.hex.leg_positions[leg]
            self.hex.move_leg(leg, x, y, mid_z)
        for leg in self.back_legs:
            x, y, _ = self.hex.leg_positions[leg]
            self.hex.move_leg(leg, x, y, back_z)

    def tilt_back(self, angle=20):
        """Tilt body backward (front up, back down)."""
        self.tilt_forward(-angle)

    def tilt_left(self, angle=20):
        """Tilt body left (left side down)."""
        left_z = -self.stand_height - angle
        right_z = -self.stand_height + angle

        for leg in self.left_legs:
            x, y, _ = self.hex.leg_positions[leg]
            self.hex.move_leg(leg, x, y, left_z)
        for leg in self.right_legs:
            x, y, _ = self.hex.leg_positions[leg]
            self.hex.move_leg(leg, x, y, right_z)

    def tilt_right(self, angle=20):
        """Tilt body right (right side down)."""
        self.tilt_left(-angle)

    def twist(self, angle=15):
        """
        Twist body (rotate hips without moving feet).

        Args:
            angle: Twist angle in degrees (positive=CCW)
        """
        import math
        rad = math.radians(angle)
        cos_r, sin_r = math.cos(rad), math.sin(rad)

        for leg in self.hex.leg_positions.keys():
            x, y, z = self.hex.leg_positions[leg]
            new_x = x * cos_r - y * sin_r
            new_y = x * sin_r + y * cos_r
            self.hex.move_leg(leg, new_x, new_y, z)

    # =========================================================================
    # Wave Gait (slower but more stable)
    # =========================================================================

    def wave_walk(self, direction=0, steps=2, step_length=30, step_height=30,
                  leg_time=0.15):
        """
        Walk using wave gait (one leg at a time).

        More stable than tripod but slower. Good for rough terrain.

        Args:
            direction: Movement direction (0=forward)
            steps: Number of complete cycles
            step_length: Step size in mm
            step_height: Lift height in mm
            leg_time: Time per leg movement
        """
        import math

        rad = math.radians(direction)
        dx = step_length * math.cos(rad)
        dy = step_length * math.sin(rad)

        # Wave sequence: R3, R2, R1, L3, L2, L1
        sequence = ['R3', 'R2', 'R1', 'L3', 'L2', 'L1']

        for _ in range(steps):
            for leg in sequence:
                self._single_leg_step(leg, dx, dy, step_height, leg_time)

            # After full wave, shift all legs back to prepare for next cycle
            self._shift_all_legs(-dx, -dy, leg_time)

    def _single_leg_step(self, leg, dx, dy, lift_height, t):
        """Move single leg forward."""
        x, y, z = self.hex.leg_positions[leg]

        # Lift
        self.hex.move_leg(leg, x, y, z + lift_height)
        sleep(t / 3)

        # Swing forward
        self.hex.move_leg(leg, x + dx, y + dy, z + lift_height)
        sleep(t / 3)

        # Plant
        self.hex.move_leg(leg, x + dx, y + dy, -self.stand_height)
        sleep(t / 3)

    def _shift_all_legs(self, dx, dy, t):
        """Shift all legs (body moves opposite direction)."""
        for leg in self.hex.leg_positions.keys():
            x, y, z = self.hex.leg_positions[leg]
            self.hex.move_leg(leg, x + dx, y + dy, z)
        sleep(t)

    # =========================================================================
    # Startup / Shutdown Sequences
    # =========================================================================

    def boot_up(self, t=0.3):
        """
        Startup sequence - unfold from curled position.
        Ported from hexy boot_up().
        """
        # Start curled
        self._curl_up()
        sleep(t)

        # Flatten out
        self._lie_flat()
        sleep(t)

        # Stand up
        self._get_up()
        sleep(t)

    def shut_down(self, t=0.3):
        """
        Shutdown sequence - fold into curled position.
        """
        # Lie down
        self._lie_down()
        sleep(t)

        # Curl up
        self._curl_up()
        sleep(t)

        # Disable servos
        self.hex.shutdown()

    def _curl_up(self):
        """Curl all legs inward (compact storage position)."""
        for leg in self.hex.leg_positions.keys():
            # Tuck legs under body
            self.hex.move_leg(leg, 30, 0, -20)

    def _lie_flat(self):
        """Extend legs flat on ground."""
        for leg in self.hex.leg_positions.keys():
            self.hex.move_leg(leg, self.stance_width, 0, -10)

    def _get_up(self):
        """Rise from lying flat to standing."""
        for height in range(10, self.stand_height + 1, 10):
            for leg in self.hex.leg_positions.keys():
                x, y, _ = self.hex.leg_positions[leg]
                self.hex.move_leg(leg, x, y, -height)
            sleep(0.1)

    def _lie_down(self):
        """Lower from standing to lying flat."""
        for height in range(self.stand_height, 9, -10):
            for leg in self.hex.leg_positions.keys():
                x, y, _ = self.hex.leg_positions[leg]
                self.hex.move_leg(leg, x, y, -height)
            sleep(0.1)


class RippleGait:
    """
    Ripple gait - legs move in wave-like pattern.

    Sequence: R1 -> R2 -> R3 -> L3 -> L2 -> L1
    Always 4+ legs on ground for maximum stability.
    """

    def __init__(self, hexapod):
        self.hex = hexapod
        self.sequence = ['R1', 'R2', 'R3', 'L3', 'L2', 'L1']
        self.stand_height = 50

    def walk(self, direction=0, steps=2, step_length=25, step_height=25,
             phase_time=0.1):
        """
        Ripple walk - smoother than wave, more stable than tripod.
        """
        import math

        rad = math.radians(direction)
        dx = step_length * math.cos(rad)
        dy = step_length * math.sin(rad)

        for _ in range(steps):
            for i, leg in enumerate(self.sequence):
                # Move this leg
                self._step_leg(leg, dx, dy, step_height, phase_time)

                # Simultaneously shift other legs slightly back
                for other in self.sequence:
                    if other != leg:
                        x, y, z = self.hex.leg_positions[other]
                        shift = step_length / 6  # Small shift
                        self.hex.move_leg(other, x - dx/6, y - dy/6, z)

    def _step_leg(self, leg, dx, dy, lift, t):
        """Single leg step in ripple pattern."""
        x, y, z = self.hex.leg_positions[leg]

        # Lift and swing
        self.hex.move_leg(leg, x + dx, y + dy, z + lift)
        sleep(t)

        # Plant
        self.hex.move_leg(leg, x + dx, y + dy, -self.stand_height)
        sleep(t / 2)


if __name__ == '__main__':
    print("Gait module - requires Hexapod instance")
    print("Usage:")
    print("  from hexapod import Hexapod")
    print("  from gait import GaitController")
    print("  hex = Hexapod(drivers)")
    print("  gait = GaitController(hex)")
    print("  gait.stand()")
    print("  gait.walk(direction=0, steps=4)")
