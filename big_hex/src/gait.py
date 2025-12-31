"""
Big Hex - Gait Controller

Walking patterns for hexapod locomotion.
Adapted from small hexapod project.
"""

import math
import time
from typing import List, Dict, Tuple

from hexapod import Hexapod, LEG_ANGLES


class GaitController:
    """
    Gait controller for hexapod locomotion.

    Implements tripod gait (fastest) and wave gait (most stable).
    """

    def __init__(self, hexapod: Hexapod):
        """
        Initialize gait controller.

        Args:
            hexapod: Hexapod controller instance
        """
        self.hex = hexapod

        # Leg groupings for tripod gait
        # Tripod 1: L1, R2, L3 (front-left, mid-right, back-left)
        # Tripod 2: R1, L2, R3 (front-right, mid-left, back-right)
        self.tripod1 = ['L1', 'R2', 'L3']
        self.tripod2 = ['R1', 'L2', 'R3']

        # Other groupings
        self.left_legs = ['L1', 'L2', 'L3']
        self.right_legs = ['R1', 'R2', 'R3']
        self.all_legs = list(LEG_ANGLES.keys())

        # Wave gait sequence (one leg at a time)
        self.wave_sequence = ['L1', 'R1', 'L2', 'R2', 'L3', 'R3']

        # Default parameters
        self.stand_height = 80   # mm - default standing height
        self.step_height = 40    # mm - how high to lift legs
        self.step_length = 60    # mm - how far each step moves
        self.cycle_time = 0.6    # seconds - time for one gait cycle

    # =========================================================================
    # Basic Poses
    # =========================================================================

    def stand(self, height: float = None, time_ms: int = 500):
        """
        Move to neutral standing position.

        Args:
            height: Body height in mm
            time_ms: Movement time
        """
        h = height or self.stand_height
        self.hex.stand(height=h, time_ms=time_ms)
        self.stand_height = h

    def sit(self, time_ms: int = 500):
        """Lower body to sitting position."""
        self.hex.sit(time_ms=time_ms)

    def home(self, time_ms: int = 1000):
        """Return all legs to home position."""
        self.stand(time_ms=time_ms)

    # =========================================================================
    # Tripod Gait (Walking)
    # =========================================================================

    def walk(self, direction: float = 0, steps: int = 4,
             step_length: float = None, step_height: float = None,
             cycle_time: float = None):
        """
        Walk using tripod gait.

        Tripod gait moves 3 legs at a time (alternating sets),
        providing fast movement with good stability.

        Args:
            direction: Movement direction in degrees (0=forward, 90=left, 180=back, 270=right)
            steps: Number of complete gait cycles
            step_length: Distance per step in mm (default: self.step_length)
            step_height: Leg lift height in mm (default: self.step_height)
            cycle_time: Time per cycle in seconds (default: self.cycle_time)
        """
        sl = step_length or self.step_length
        sh = step_height or self.step_height
        ct = cycle_time or self.cycle_time

        # Convert direction to x/y components
        rad = math.radians(direction)
        dx = sl * math.cos(rad)
        dy = sl * math.sin(rad)

        half_cycle = ct / 2
        move_time = int(half_cycle * 1000 / 3)  # ms per sub-phase

        for _ in range(steps):
            # Phase 1: Tripod 1 swings forward, Tripod 2 pushes back
            self._tripod_step(self.tripod1, self.tripod2, dx, dy, sh, move_time)

            # Phase 2: Tripod 2 swings forward, Tripod 1 pushes back
            self._tripod_step(self.tripod2, self.tripod1, dx, dy, sh, move_time)

    def _tripod_step(self, swing_legs: List[str], stance_legs: List[str],
                     dx: float, dy: float, lift_height: float, move_time: int):
        """
        Execute one half of tripod gait cycle.

        Args:
            swing_legs: Legs that lift and swing forward
            stance_legs: Legs that stay on ground and push back
            dx, dy: Step direction components in mm
            lift_height: How high to lift swing legs in mm
            move_time: Time per sub-phase in ms
        """
        # Sub-phase 1: Lift swing legs
        positions = {}
        for leg in swing_legs:
            x, y, z = self.hex.leg_positions[leg]
            positions[leg] = (x, y, z + lift_height)
        self.hex.move_all_legs(positions, move_time)
        time.sleep(move_time / 1000)

        # Sub-phase 2: Swing forward + push back
        positions = {}
        for leg in swing_legs:
            x, y, z = self.hex.leg_positions[leg]
            positions[leg] = (x + dx, y + dy, z)

        for leg in stance_legs:
            x, y, z = self.hex.leg_positions[leg]
            positions[leg] = (x - dx/2, y - dy/2, z)

        self.hex.move_all_legs(positions, move_time)
        time.sleep(move_time / 1000)

        # Sub-phase 3: Lower swing legs
        positions = {}
        for leg in swing_legs:
            x, y, z = self.hex.leg_positions[leg]
            positions[leg] = (x, y, -self.stand_height)
        self.hex.move_all_legs(positions, move_time)
        time.sleep(move_time / 1000)

    def walk_forward(self, steps: int = 4):
        """Walk forward."""
        self.walk(direction=0, steps=steps)

    def walk_backward(self, steps: int = 4):
        """Walk backward."""
        self.walk(direction=180, steps=steps)

    def strafe_left(self, steps: int = 4):
        """Strafe left."""
        self.walk(direction=90, steps=steps)

    def strafe_right(self, steps: int = 4):
        """Strafe right."""
        self.walk(direction=270, steps=steps)

    # =========================================================================
    # Rotation
    # =========================================================================

    def rotate(self, angle: float = 30, steps: int = 4,
               step_height: float = None, cycle_time: float = None):
        """
        Rotate in place using tripod gait.

        Args:
            angle: Rotation per cycle in degrees (positive=CCW/left, negative=CW/right)
            steps: Number of rotation cycles
            step_height: Leg lift height in mm
            cycle_time: Time per cycle in seconds
        """
        sh = step_height or self.step_height
        ct = cycle_time or self.cycle_time

        half_cycle = ct / 2
        move_time = int(half_cycle * 1000 / 2)
        rad = math.radians(angle / 2)

        for _ in range(steps):
            # Phase 1: Lift tripod 1, rotate
            self._rotate_tripod(self.tripod1, self.tripod2, rad, sh, move_time)

            # Phase 2: Lift tripod 2, rotate
            self._rotate_tripod(self.tripod2, self.tripod1, rad, sh, move_time)

    def _rotate_tripod(self, swing_legs: List[str], stance_legs: List[str],
                       rad: float, lift_height: float, move_time: int):
        """Execute rotation with one tripod lifted."""
        # Lift swing legs
        positions = {}
        for leg in swing_legs:
            x, y, z = self.hex.leg_positions[leg]
            positions[leg] = (x, y, z + lift_height)
        self.hex.move_all_legs(positions, move_time)
        time.sleep(move_time / 1000)

        # Rotate positions
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        positions = {}

        for leg in swing_legs:
            x, y, z = self.hex.leg_positions[leg]
            # Rotate swing legs in direction of turn
            new_x = x * cos_r - y * sin_r
            new_y = x * sin_r + y * cos_r
            positions[leg] = (new_x, new_y, -self.stand_height)

        for leg in stance_legs:
            x, y, z = self.hex.leg_positions[leg]
            # Rotate stance legs opposite (pushes body)
            new_x = x * cos_r + y * sin_r
            new_y = -x * sin_r + y * cos_r
            positions[leg] = (new_x, new_y, z)

        self.hex.move_all_legs(positions, move_time)
        time.sleep(move_time / 1000)

    def turn_left(self, angle: float = 90):
        """Turn left (counterclockwise)."""
        steps = max(1, int(abs(angle) / 30))
        self.rotate(angle=30, steps=steps)

    def turn_right(self, angle: float = 90):
        """Turn right (clockwise)."""
        steps = max(1, int(abs(angle) / 30))
        self.rotate(angle=-30, steps=steps)

    # =========================================================================
    # Wave Gait (Slow but stable)
    # =========================================================================

    def wave_walk(self, direction: float = 0, cycles: int = 2,
                  step_length: float = None, step_height: float = None):
        """
        Walk using wave gait.

        Wave gait moves one leg at a time, providing maximum stability
        at the cost of speed. Good for rough terrain or heavy loads.

        Args:
            direction: Movement direction in degrees
            cycles: Number of complete cycles (all 6 legs move once per cycle)
            step_length: Distance per step in mm
            step_height: Leg lift height in mm
        """
        sl = step_length or self.step_length
        sh = step_height or self.step_height

        rad = math.radians(direction)
        dx = sl * math.cos(rad)
        dy = sl * math.sin(rad)

        move_time = 150  # ms per movement

        for _ in range(cycles):
            for leg in self.wave_sequence:
                # Lift leg
                x, y, z = self.hex.leg_positions[leg]
                self.hex.move_leg(leg, x, y, z + sh, move_time)
                time.sleep(move_time / 1000)

                # Swing forward
                self.hex.move_leg(leg, x + dx, y + dy, z + sh, move_time)
                time.sleep(move_time / 1000)

                # Lower leg
                self.hex.move_leg(leg, x + dx, y + dy, -self.stand_height, move_time)
                time.sleep(move_time / 1000)

                # All other legs push slightly
                push_dx = -dx / 5
                push_dy = -dy / 5
                for other_leg in self.all_legs:
                    if other_leg != leg:
                        ox, oy, oz = self.hex.leg_positions[other_leg]
                        self.hex.move_leg(other_leg, ox + push_dx, oy + push_dy, oz, move_time)

    # =========================================================================
    # Body Movements
    # =========================================================================

    def body_shift(self, dx: float = 0, dy: float = 0, dz: float = 0,
                   time_ms: int = 300):
        """
        Shift body position (all legs move opposite).

        Args:
            dx: Forward/back shift in mm (positive = forward)
            dy: Left/right shift in mm (positive = left)
            dz: Up/down shift in mm (positive = up)
            time_ms: Movement time
        """
        positions = {}
        for leg in self.all_legs:
            x, y, z = self.hex.leg_positions[leg]
            # Move legs opposite to shift body
            positions[leg] = (x - dx, y - dy, z - dz)
        self.hex.move_all_legs(positions, time_ms)

    def body_tilt(self, pitch: float = 0, roll: float = 0, time_ms: int = 300):
        """
        Tilt body (pitch and roll).

        Args:
            pitch: Forward/back tilt in degrees (positive = nose down)
            roll: Left/right tilt in degrees (positive = left side down)
            time_ms: Movement time
        """
        # Convert to leg height adjustments
        pitch_rad = math.radians(pitch)
        roll_rad = math.radians(roll)

        positions = {}
        for leg, angle in LEG_ANGLES.items():
            x, y, z = self.hex.leg_positions[leg]

            # Calculate height change based on leg position
            leg_rad = math.radians(angle)
            dz_pitch = 50 * math.cos(leg_rad) * math.sin(pitch_rad)
            dz_roll = 50 * math.sin(leg_rad) * math.sin(roll_rad)

            positions[leg] = (x, y, z + dz_pitch + dz_roll)

        self.hex.move_all_legs(positions, time_ms)

    def wave_body(self, amplitude: float = 20, cycles: int = 2, period: float = 1.0):
        """
        Wave body up and down.

        Args:
            amplitude: Height change in mm
            cycles: Number of wave cycles
            period: Time per cycle in seconds
        """
        steps_per_cycle = 20
        step_time = period / steps_per_cycle

        for _ in range(cycles):
            for i in range(steps_per_cycle):
                phase = 2 * math.pi * i / steps_per_cycle
                dz = amplitude * math.sin(phase)
                self.body_shift(dz=dz, time_ms=int(step_time * 1000))
                time.sleep(step_time)

    # =========================================================================
    # Demo Sequences
    # =========================================================================

    def demo_walk(self):
        """Demo walking sequence."""
        print("Demo: Walking sequence")

        print("  Standing up...")
        self.stand(time_ms=1000)
        time.sleep(1.5)

        print("  Walking forward...")
        self.walk_forward(steps=4)

        print("  Turning left...")
        self.turn_left(angle=90)

        print("  Walking forward...")
        self.walk_forward(steps=2)

        print("  Sitting down...")
        self.sit(time_ms=1000)

        print("Demo complete!")

    def demo_body(self):
        """Demo body movements."""
        print("Demo: Body movements")

        self.stand(time_ms=1000)
        time.sleep(1)

        print("  Shifting forward...")
        self.body_shift(dx=30, time_ms=500)
        time.sleep(0.7)
        self.body_shift(dx=-30, time_ms=500)
        time.sleep(0.7)

        print("  Tilting left/right...")
        self.body_tilt(roll=15, time_ms=500)
        time.sleep(0.7)
        self.body_tilt(roll=-15, time_ms=500)
        time.sleep(0.7)
        self.body_tilt(roll=0, time_ms=500)
        time.sleep(0.7)

        print("  Waving...")
        self.wave_body(amplitude=15, cycles=2, period=0.8)

        self.home()
        print("Demo complete!")


# =============================================================================
# Main (Test)
# =============================================================================

if __name__ == '__main__':
    print("Big Hex Gait Controller Test (Simulation Mode)")
    print("=" * 50)

    with Hexapod(simulation=True) as hex:
        gait = GaitController(hex)

        print("\nStanding up...")
        gait.stand(time_ms=500)
        time.sleep(0.1)

        print("\nWalking forward (2 steps)...")
        gait.walk(direction=0, steps=2)

        print("\nTurning left...")
        gait.rotate(angle=30, steps=2)

        print("\nSitting down...")
        gait.sit(time_ms=500)

    print("\n" + "=" * 50)
    print("Simulation test complete!")
