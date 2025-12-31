#!/usr/bin/env python3
"""
Big Hex - Servo Calibration Tool

Interactive CLI tool for:
- Scanning for connected servos
- Assigning servo IDs
- Finding center positions
- Setting angle limits
- Testing movements
"""

import json
import os
import sys
import time

from lx16a import LX16A
from hexapod import Hexapod, DEFAULT_SERVO_IDS, LEG_ANGLES


def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header(title: str):
    """Print section header."""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50 + "\n")


def prompt(msg: str, default: str = None) -> str:
    """Prompt for input with optional default."""
    if default:
        result = input(f"{msg} [{default}]: ").strip()
        return result if result else default
    return input(f"{msg}: ").strip()


def prompt_int(msg: str, default: int = None) -> int:
    """Prompt for integer input."""
    while True:
        try:
            result = prompt(msg, str(default) if default else None)
            return int(result)
        except ValueError:
            print("Please enter a valid number.")


def prompt_yn(msg: str, default: bool = True) -> bool:
    """Prompt for yes/no."""
    suffix = "[Y/n]" if default else "[y/N]"
    result = input(f"{msg} {suffix}: ").strip().lower()
    if not result:
        return default
    return result in ('y', 'yes')


class Calibrator:
    """Interactive calibration tool."""

    def __init__(self, port: str = '/dev/serial0', simulation: bool = False):
        self.port = port
        self.simulation = simulation
        self.bus = LX16A(port=port, simulation=simulation)
        self.config_file = 'config.json'
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load existing config or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        return {
            'serial_port': self.port,
            'baud_rate': 115200,
            'geometry': {
                'coxa_length': 50,
                'femur_length': 80,
                'tibia_length': 120,
                'body_radius': 175,
            },
            'servo_ids': DEFAULT_SERVO_IDS,
            'calibration': {},
        }

    def save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"Configuration saved to {self.config_file}")

    def scan_servos(self):
        """Scan for connected servos."""
        print_header("Scanning for Servos")

        if self.simulation:
            print("Simulation mode - no hardware scan available")
            return

        print("Scanning IDs 1-20 (this may take a moment)...")
        found = self.bus.scan(start_id=1, end_id=20)

        if found:
            print(f"\nFound {len(found)} servo(s): {found}")
        else:
            print("\nNo servos found. Check:")
            print("  - Power is connected")
            print("  - Serial cable is connected")
            print("  - Servos are daisy-chained properly")

        return found

    def set_servo_id(self):
        """Change a servo's ID."""
        print_header("Set Servo ID")

        print("WARNING: Only connect ONE servo when changing IDs!")
        print("The servo will respond to broadcast commands.\n")

        if not prompt_yn("Continue?"):
            return

        # Try to read current ID
        print("\nReading current ID...")
        current_id = self.bus.read_id()

        if current_id:
            print(f"Current servo ID: {current_id}")
        else:
            print("Could not read ID. Using broadcast.")
            current_id = 254  # Broadcast

        new_id = prompt_int("Enter new ID (1-253)", current_id if current_id != 254 else 1)

        if new_id < 1 or new_id > 253:
            print("Invalid ID. Must be 1-253.")
            return

        if prompt_yn(f"Change ID from {current_id} to {new_id}?"):
            self.bus.set_id(current_id, new_id)
            print(f"ID changed to {new_id}")
            print("Power cycle the servo to confirm the change.")

    def test_servo(self):
        """Test a single servo."""
        print_header("Test Single Servo")

        servo_id = prompt_int("Enter servo ID to test", 1)

        print(f"\nTesting servo {servo_id}...")

        # Read current position
        pos = self.bus.read_position(servo_id)
        if pos is not None:
            print(f"Current position: {pos}")
        else:
            print("Could not read position (servo may not be connected)")

        # Read voltage
        voltage = self.bus.read_voltage(servo_id)
        if voltage is not None:
            print(f"Voltage: {voltage:.1f}V")

        # Read temperature
        temp = self.bus.read_temperature(servo_id)
        if temp is not None:
            print(f"Temperature: {temp}°C")

        if prompt_yn("\nMove servo to center (500)?"):
            self.bus.move(servo_id, 500, 1000)
            print("Moving to center...")
            time.sleep(1.5)

        if prompt_yn("Sweep servo (300-700)?"):
            print("Sweeping...")
            self.bus.move(servo_id, 300, 500)
            time.sleep(0.6)
            self.bus.move(servo_id, 700, 500)
            time.sleep(0.6)
            self.bus.move(servo_id, 500, 500)
            time.sleep(0.6)

        if prompt_yn("Unload servo (disable torque)?"):
            self.bus.unload(servo_id)
            print("Servo unloaded - can be moved by hand")

    def test_leg(self):
        """Test all servos in a leg."""
        print_header("Test Leg")

        print("Legs: L1, L2, L3, R1, R2, R3")
        leg = prompt("Enter leg name", "L1").upper()

        if leg not in LEG_ANGLES:
            print(f"Invalid leg: {leg}")
            return

        servo_ids = self.config['servo_ids'].get(leg, DEFAULT_SERVO_IDS[leg])
        print(f"\n{leg} servo IDs:")
        print(f"  Coxa:  {servo_ids['coxa']}")
        print(f"  Femur: {servo_ids['femur']}")
        print(f"  Tibia: {servo_ids['tibia']}")

        if prompt_yn("\nCenter all servos in leg?"):
            for joint, sid in servo_ids.items():
                self.bus.move(sid, 500, 1000)
                print(f"  {joint} ({sid}) -> 500")
            time.sleep(1.5)

        if prompt_yn("Unload all servos in leg?"):
            for joint, sid in servo_ids.items():
                self.bus.unload(sid)
            print("Leg unloaded")

    def calibrate_centers(self):
        """Interactive center position calibration."""
        print_header("Calibrate Center Positions")

        print("This will help find the center position for each servo.")
        print("Move each servo to its mechanical center and record the position.\n")

        for leg in LEG_ANGLES:
            if not prompt_yn(f"Calibrate {leg}?"):
                continue

            servo_ids = self.config['servo_ids'].get(leg, DEFAULT_SERVO_IDS[leg])

            for joint in ['coxa', 'femur', 'tibia']:
                sid = servo_ids[joint]

                print(f"\n  {leg} {joint} (ID {sid}):")

                # Unload servo
                self.bus.unload(sid)
                print("    Servo unloaded - move to center position by hand")

                input("    Press Enter when centered...")

                # Read position
                pos = self.bus.read_position(sid)
                if pos is not None:
                    print(f"    Position: {pos}")

                    # Calculate offset from 500
                    offset = pos - 500

                    # Store calibration
                    if str(sid) not in self.config['calibration']:
                        self.config['calibration'][str(sid)] = {}
                    self.config['calibration'][str(sid)]['center'] = pos
                    self.config['calibration'][str(sid)]['offset'] = -offset
                else:
                    print("    Could not read position")

                # Load servo back
                self.bus.load(sid)

        self.save_config()

    def show_config(self):
        """Display current configuration."""
        print_header("Current Configuration")
        print(json.dumps(self.config, indent=2))

    def main_menu(self):
        """Main menu loop."""
        while True:
            clear_screen()
            print_header("Big Hex Calibration Tool")

            if self.simulation:
                print("*** SIMULATION MODE ***\n")

            print("1. Scan for servos")
            print("2. Set servo ID")
            print("3. Test single servo")
            print("4. Test leg")
            print("5. Calibrate centers")
            print("6. Show configuration")
            print("7. Save configuration")
            print("8. Exit")
            print()

            choice = prompt("Select option", "8")

            try:
                if choice == '1':
                    self.scan_servos()
                elif choice == '2':
                    self.set_servo_id()
                elif choice == '3':
                    self.test_servo()
                elif choice == '4':
                    self.test_leg()
                elif choice == '5':
                    self.calibrate_centers()
                elif choice == '6':
                    self.show_config()
                elif choice == '7':
                    self.save_config()
                elif choice == '8':
                    print("\nGoodbye!")
                    break
                else:
                    print("Invalid option")

                if choice not in ('8',):
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\n\nInterrupted")
                break
            except Exception as e:
                print(f"\nError: {e}")
                input("Press Enter to continue...")

        self.bus.close()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Big Hex Servo Calibration Tool')
    parser.add_argument('--port', '-p', default='/dev/serial0',
                       help='Serial port (default: /dev/serial0)')
    parser.add_argument('--simulation', '-s', action='store_true',
                       help='Run in simulation mode')

    args = parser.parse_args()

    cal = Calibrator(port=args.port, simulation=args.simulation)
    cal.main_menu()


if __name__ == '__main__':
    main()
