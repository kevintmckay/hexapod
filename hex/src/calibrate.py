#!/usr/bin/env python3
"""
Hexapod Servo Calibration Tool

Interactive tool to find min/max pulse widths for each servo
and save calibration data to a config file.

Usage:
    python calibrate.py [--simulate]
"""

import copy
import json
import os
import sys
from time import sleep

# Get the directory where this script is located for reliable file paths
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Default calibration values
DEFAULT_CALIBRATION = {
    'L1': {
        'coxa':  {'channel': 0,  'min': 500, 'max': 2500, 'center': 1500, 'direction': 1},
        'femur': {'channel': 1,  'min': 500, 'max': 2500, 'center': 1500, 'direction': 1},
        'tibia': {'channel': 2,  'min': 500, 'max': 2500, 'center': 1500, 'direction': 1},
    },
    'L2': {
        'coxa':  {'channel': 3,  'min': 500, 'max': 2500, 'center': 1500, 'direction': 1},
        'femur': {'channel': 4,  'min': 500, 'max': 2500, 'center': 1500, 'direction': 1},
        'tibia': {'channel': 5,  'min': 500, 'max': 2500, 'center': 1500, 'direction': 1},
    },
    'L3': {
        'coxa':  {'channel': 6,  'min': 500, 'max': 2500, 'center': 1500, 'direction': 1},
        'femur': {'channel': 7,  'min': 500, 'max': 2500, 'center': 1500, 'direction': 1},
        'tibia': {'channel': 8,  'min': 500, 'max': 2500, 'center': 1500, 'direction': 1},
    },
    'R1': {
        'coxa':  {'channel': 9,  'min': 500, 'max': 2500, 'center': 1500, 'direction': -1},
        'femur': {'channel': 10, 'min': 500, 'max': 2500, 'center': 1500, 'direction': -1},
        'tibia': {'channel': 11, 'min': 500, 'max': 2500, 'center': 1500, 'direction': -1},
    },
    'R2': {
        'coxa':  {'channel': 16, 'min': 500, 'max': 2500, 'center': 1500, 'direction': -1},
        'femur': {'channel': 17, 'min': 500, 'max': 2500, 'center': 1500, 'direction': -1},
        'tibia': {'channel': 18, 'min': 500, 'max': 2500, 'center': 1500, 'direction': -1},
    },
    'R3': {
        'coxa':  {'channel': 19, 'min': 500, 'max': 2500, 'center': 1500, 'direction': -1},
        'femur': {'channel': 20, 'min': 500, 'max': 2500, 'center': 1500, 'direction': -1},
        'tibia': {'channel': 21, 'min': 500, 'max': 2500, 'center': 1500, 'direction': -1},
    },
}

# Use absolute path based on script location for reliable file access
CONFIG_FILE = os.path.join(_SCRIPT_DIR, 'calibration.json')


class CalibrationTool:
    """Interactive servo calibration."""

    def __init__(self, simulate=False):
        self.simulate = simulate
        self.calibration = self._load_calibration()
        self.pca = [None, None]

        if not simulate:
            self._init_drivers()

    def _init_drivers(self):
        """Initialize PCA9685 drivers."""
        try:
            from pca9685 import PCA9685
            self.pca[0] = PCA9685(address=0x40, freq=50)
            self.pca[1] = PCA9685(address=0x41, freq=50)
            print("PCA9685 drivers initialized (0x40, 0x41)")
        except Exception as e:
            print(f"Warning: Could not init hardware: {e}")
            print("Running in simulation mode")
            self.simulate = True

    def _load_calibration(self):
        """Load calibration from file or use defaults."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    print(f"Loaded calibration from {CONFIG_FILE}")
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load {CONFIG_FILE}: {e}")

        print("Using default calibration values")
        return copy.deepcopy(DEFAULT_CALIBRATION)

    def save_calibration(self):
        """Save calibration to file."""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.calibration, f, indent=2)
        print(f"Calibration saved to {CONFIG_FILE}")

    def set_pulse(self, channel, pulse_us):
        """Set servo pulse width."""
        if self.simulate:
            print(f"  [SIM] Channel {channel}: {pulse_us}us")
            return

        pca_idx = 0 if channel < 16 else 1
        ch = channel if channel < 16 else channel - 16
        self.pca[pca_idx].set_pwm(ch, pulse_us)

    def disable_servo(self, channel):
        """Disable servo (no holding torque)."""
        if self.simulate:
            print(f"  [SIM] Channel {channel}: disabled")
            return

        pca_idx = 0 if channel < 16 else 1
        ch = channel if channel < 16 else channel - 16
        self.pca[pca_idx].set_pwm(ch, 0)

    def disable_all(self):
        """Disable all servos."""
        for leg in self.calibration:
            for joint in self.calibration[leg]:
                ch = self.calibration[leg][joint]['channel']
                self.disable_servo(ch)

    def center_all(self):
        """Move all servos to center position."""
        print("Centering all servos...")
        for leg in self.calibration:
            for joint in self.calibration[leg]:
                ch = self.calibration[leg][joint]['channel']
                center = self.calibration[leg][joint]['center']
                self.set_pulse(ch, center)
        sleep(0.5)

    def calibrate_joint(self, leg, joint):
        """Interactive calibration for single joint."""
        config = self.calibration[leg][joint]
        channel = config['channel']
        current = config['center']

        print(f"\n--- Calibrating {leg} {joint} (channel {channel}) ---")
        print("Commands: +/- adjust by 10us, ++/-- by 50us")
        print("          min/max/center to set positions")
        print("          flip to toggle direction")
        print("          done to finish this joint")
        print(f"Current: min={config['min']} center={config['center']} max={config['max']}")

        self.set_pulse(channel, current)

        while True:
            try:
                cmd = input(f"[{current}us] > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if cmd == 'done' or cmd == 'd':
                break
            elif cmd == '+':
                current = min(2500, current + 10)
            elif cmd == '-':
                current = max(500, current - 10)
            elif cmd == '++':
                current = min(2500, current + 50)
            elif cmd == '--':
                current = max(500, current - 50)
            elif cmd == 'min':
                config['min'] = current
                print(f"  MIN set to {current}us")
            elif cmd == 'max':
                config['max'] = current
                print(f"  MAX set to {current}us")
            elif cmd == 'center' or cmd == 'c':
                config['center'] = current
                print(f"  CENTER set to {current}us")
            elif cmd == 'flip' or cmd == 'f':
                config['direction'] *= -1
                print(f"  Direction: {config['direction']}")
            elif cmd.isdigit():
                current = max(500, min(2500, int(cmd)))
            elif cmd == 'off':
                self.disable_servo(channel)
                print("  Servo disabled")
                continue
            elif cmd == '?':
                print(f"  min={config['min']} center={config['center']} max={config['max']} dir={config['direction']}")
                continue
            else:
                print("  Unknown command. Use +/-/++/--/min/max/center/flip/done/?")
                continue

            self.set_pulse(channel, current)

        self.disable_servo(channel)

    def run_interactive(self):
        """Run interactive calibration for all joints."""
        print("\n" + "=" * 50)
        print("HEXAPOD SERVO CALIBRATION")
        print("=" * 50)

        legs = ['L1', 'L2', 'L3', 'R1', 'R2', 'R3']
        joints = ['coxa', 'femur', 'tibia']

        print("\nLeg layout (top view):")
        print("     FRONT")
        print("  L1       R1")
        print("  L2--[ ]--R2")
        print("  L3       R3")
        print("     REAR")

        print("\nOptions:")
        print("  1-6: Select leg (L1=1, L2=2, L3=3, R1=4, R2=5, R3=6)")
        print("  all: Calibrate all joints in sequence")
        print("  center: Move all servos to center")
        print("  save: Save calibration to file")
        print("  quit: Exit")

        while True:
            try:
                cmd = input("\nSelect [1-6/all/center/save/quit] > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if cmd == 'quit' or cmd == 'q':
                break
            elif cmd == 'save' or cmd == 's':
                self.save_calibration()
            elif cmd == 'center':
                self.center_all()
            elif cmd == 'all':
                for leg in legs:
                    for joint in joints:
                        self.calibrate_joint(leg, joint)
                print("\nAll joints calibrated!")
            elif cmd in ['1', '2', '3', '4', '5', '6']:
                leg = legs[int(cmd) - 1]
                print(f"\nCalibrating {leg}")
                for joint in joints:
                    self.calibrate_joint(leg, joint)
            elif cmd in legs:
                for joint in joints:
                    self.calibrate_joint(cmd.upper(), joint)
            else:
                # Try leg.joint format (e.g., "L1.coxa")
                if '.' in cmd:
                    parts = cmd.upper().split('.')
                    if len(parts) == 2 and parts[0] in legs:
                        leg, joint = parts
                        if joint.lower() in joints:
                            self.calibrate_joint(leg, joint.lower())
                            continue
                print("Unknown command")

        self.disable_all()
        print("\nCalibration complete. Don't forget to 'save'!")


def test_sweep(simulate=False):
    """Test all servos with a sweep pattern."""
    tool = CalibrationTool(simulate=simulate)

    print("Testing servo sweep (all channels)...")

    for pulse in range(1000, 2000, 100):
        print(f"Pulse: {pulse}us")
        for leg in tool.calibration:
            for joint in tool.calibration[leg]:
                ch = tool.calibration[leg][joint]['channel']
                tool.set_pulse(ch, pulse)
        sleep(0.3)

    tool.disable_all()
    print("Sweep complete")


if __name__ == '__main__':
    simulate = '--simulate' in sys.argv or '-s' in sys.argv

    if '--test' in sys.argv:
        test_sweep(simulate)
    else:
        tool = CalibrationTool(simulate=simulate)
        tool.run_interactive()
