#!/usr/bin/env python3
"""
Big Hex - Demo Scripts

Test and demonstration code for the hexapod.
"""

import argparse
import time
import sys

from hexapod import Hexapod
from gait import GaitController


def demo_stand_sit(hex: Hexapod):
    """Demo: Stand up and sit down."""
    print("\n=== Demo: Stand/Sit ===\n")

    print("Standing up (80mm)...")
    hex.stand(height=80, time_ms=1000)
    time.sleep(1.5)

    print("Rising higher (100mm)...")
    hex.stand(height=100, time_ms=500)
    time.sleep(1)

    print("Lowering (60mm)...")
    hex.stand(height=60, time_ms=500)
    time.sleep(1)

    print("Sitting down...")
    hex.sit(time_ms=1000)
    time.sleep(1.5)

    print("Done!")


def demo_leg_test(hex: Hexapod):
    """Demo: Test individual leg movement."""
    print("\n=== Demo: Leg Test ===\n")

    print("Standing up...")
    hex.stand(height=80, time_ms=1000)
    time.sleep(1.5)

    legs = ['L1', 'R1', 'L2', 'R2', 'L3', 'R3']

    for leg in legs:
        print(f"Lifting {leg}...")
        x, y, z = hex.leg_positions[leg]
        hex.move_leg(leg, x, y, z + 40, 300)
        time.sleep(0.5)
        hex.move_leg(leg, x, y, z, 300)
        time.sleep(0.5)

    print("Sitting down...")
    hex.sit(time_ms=1000)
    time.sleep(1.5)

    print("Done!")


def demo_walk(hex: Hexapod):
    """Demo: Walking sequence."""
    print("\n=== Demo: Walking ===\n")

    gait = GaitController(hex)

    print("Standing up...")
    gait.stand(time_ms=1000)
    time.sleep(1.5)

    print("Walking forward (4 steps)...")
    gait.walk_forward(steps=4)

    print("Turning left...")
    gait.turn_left(angle=90)

    print("Walking forward (2 steps)...")
    gait.walk_forward(steps=2)

    print("Turning right...")
    gait.turn_right(angle=90)

    print("Walking backward (2 steps)...")
    gait.walk_backward(steps=2)

    print("Sitting down...")
    gait.sit(time_ms=1000)
    time.sleep(1.5)

    print("Done!")


def demo_body_movement(hex: Hexapod):
    """Demo: Body movement without walking."""
    print("\n=== Demo: Body Movement ===\n")

    gait = GaitController(hex)

    print("Standing up...")
    gait.stand(time_ms=1000)
    time.sleep(1.5)

    print("Shifting forward...")
    gait.body_shift(dx=30, time_ms=500)
    time.sleep(0.7)

    print("Shifting back...")
    gait.body_shift(dx=-60, time_ms=500)
    time.sleep(0.7)

    print("Centering...")
    gait.body_shift(dx=30, time_ms=500)
    time.sleep(0.7)

    print("Tilting left...")
    gait.body_tilt(roll=15, time_ms=500)
    time.sleep(0.7)

    print("Tilting right...")
    gait.body_tilt(roll=-30, time_ms=500)
    time.sleep(0.7)

    print("Leveling...")
    gait.body_tilt(roll=15, time_ms=500)
    time.sleep(0.7)

    print("Waving body...")
    gait.wave_body(amplitude=15, cycles=2, period=0.8)

    print("Sitting down...")
    gait.sit(time_ms=1000)
    time.sleep(1.5)

    print("Done!")


def demo_all(hex: Hexapod):
    """Run all demos."""
    print("\n=== Running All Demos ===\n")

    demo_stand_sit(hex)
    time.sleep(1)

    demo_leg_test(hex)
    time.sleep(1)

    demo_body_movement(hex)
    time.sleep(1)

    demo_walk(hex)

    print("\n=== All Demos Complete! ===\n")


def servo_test(hex: Hexapod):
    """Test: Center all servos."""
    print("\n=== Servo Test: Center All ===\n")

    print("Centering all servos...")
    hex.center_all(time_ms=1000)
    time.sleep(1.5)

    print("Reading positions...")
    positions = hex.read_all_positions()

    for leg, joints in positions.items():
        print(f"  {leg}:")
        for joint, pos in joints.items():
            status = "OK" if pos is not None else "NO RESPONSE"
            print(f"    {joint}: {pos} {status}")

    print("\nDone!")


def voltage_check(hex: Hexapod):
    """Check voltage on all servos."""
    print("\n=== Voltage Check ===\n")

    voltages = hex.read_all_voltages()

    if not voltages:
        print("No voltages read (simulation mode or no servos connected)")
        return

    print("Servo voltages:")
    for sid, voltage in sorted(voltages.items()):
        status = "OK" if voltage > 6.0 else "LOW!"
        print(f"  Servo {sid:2d}: {voltage:.1f}V {status}")

    avg = sum(voltages.values()) / len(voltages)
    print(f"\nAverage: {avg:.1f}V")

    if avg < 6.5:
        print("WARNING: Battery may be low!")


def main():
    parser = argparse.ArgumentParser(description='Big Hex Demo Scripts')
    parser.add_argument('demo', nargs='?', default='all',
                       choices=['stand', 'legs', 'walk', 'body', 'all',
                               'servo_test', 'voltage'],
                       help='Demo to run (default: all)')
    parser.add_argument('--port', '-p', default='/dev/serial0',
                       help='Serial port')
    parser.add_argument('--simulation', '-s', action='store_true',
                       help='Run in simulation mode')
    parser.add_argument('--config', '-c', default='config.json',
                       help='Configuration file')

    args = parser.parse_args()

    print("=" * 50)
    print("  Big Hex Demo")
    print("=" * 50)

    if args.simulation:
        print("\n*** SIMULATION MODE ***")

    try:
        with Hexapod(port=args.port, config_file=args.config,
                    simulation=args.simulation) as hex:

            if args.demo == 'stand':
                demo_stand_sit(hex)
            elif args.demo == 'legs':
                demo_leg_test(hex)
            elif args.demo == 'walk':
                demo_walk(hex)
            elif args.demo == 'body':
                demo_body_movement(hex)
            elif args.demo == 'servo_test':
                servo_test(hex)
            elif args.demo == 'voltage':
                voltage_check(hex)
            else:
                demo_all(hex)

    except KeyboardInterrupt:
        print("\n\nDemo interrupted!")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
