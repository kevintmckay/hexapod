# Hexapod Robot Project

## Overview

3DOF hexapod walker using existing servo inventory and 3D printed frame.

## Specifications

| Spec | Value |
|------|-------|
| Legs | 6 |
| DOF per leg | 3 (coxa, femur, tibia) |
| Total servos | 18 |
| Gait types | Tripod, wave, ripple |
| Target size | ~250mm body, ~150mm leg reach |

## Parts Allocation

### From Inventory

| Part | Qty | Use | Notes |
|------|-----|-----|-------|
| Hitec HS-82MG | 6 | Coxa (hip) joints | Metal gear, higher torque for rotation |
| Tower Pro SG90 | 12 | Femur + tibia joints | Lighter load, adequate torque |
| PCA9685 | 2 | PWM control | 16ch each = 32ch total (18 needed) |
| SpeedyBee F405 or Arduino | 1 | Main controller | Or use Pi Zero/Pi Pico |
| 3S Li-Ion (Titan) | 1 | Power | 11.1V, 3.5Ah - good runtime |
| FTDI adapter | 1 | Programming/debug | |

### To Purchase

| Part | Est. Cost | Notes |
|------|-----------|-------|
| Pi Pico or Pi Zero 2W | $5-15 | Recommended controller |
| Buck converter 5V/5A | $5-10 | Servo power (BEC) |
| Servo wire extensions | $5 | 15-20cm leads |
| M2/M2.5 hardware kit | $10 | Servo mounting screws |
| **Total** | ~$25-40 | |

### To 3D Print

| Part | Qty | Material | Notes |
|------|-----|----------|-------|
| Body plate (top) | 1 | PLA/PETG | Hex shape, ~200mm across |
| Body plate (bottom) | 1 | PLA/PETG | Electronics mount |
| Coxa bracket | 6 | PLA/PETG | Hip rotation mount |
| Femur link | 6 | PLA/PETG | Upper leg, ~60mm |
| Tibia link | 6 | PLA/PETG | Lower leg, ~80mm |
| Foot tip | 6 | TPU | Rubber for grip (optional) |
| Servo horn adapters | 18 | PLA | If needed for fit |

## Leg Geometry

```
        [BODY]
           |
      +---------+
      |  COXA   |  <- HS-82MG (horizontal rotation)
      +---------+
           |
      +---------+
      |  FEMUR  |  <- SG90 (vertical lift)
      +---------+
           |
      +---------+
      |  TIBIA  |  <- SG90 (vertical extend)
      +---------+
           |
         [FOOT]
```

## Wiring Plan

### Power Distribution

```
3S Li-Ion (11.1V)
    |
    +---> Buck Converter ---> 5V rail
              |
              +---> PCA9685 #1 V+ (servos 0-11)
              +---> PCA9685 #2 V+ (servos 12-17)
              +---> Controller (Pi Pico 5V or VSYS)
```

### I2C Bus

```
Controller (Pi Pico / Pi Zero)
    |
    +-- SDA (GPIO 0) ----+---- PCA9685 #1 (0x40)
    |                    |
    +-- SCL (GPIO 1) ----+---- PCA9685 #2 (0x41) <- solder A0 jumper
```

### Servo Channel Mapping

| PCA9685 | Ch | Leg | Joint |
|---------|-----|-----|-------|
| #1 | 0 | L1 | Coxa |
| #1 | 1 | L1 | Femur |
| #1 | 2 | L1 | Tibia |
| #1 | 3 | L2 | Coxa |
| #1 | 4 | L2 | Femur |
| #1 | 5 | L2 | Tibia |
| #1 | 6 | L3 | Coxa |
| #1 | 7 | L3 | Femur |
| #1 | 8 | L3 | Tibia |
| #1 | 9 | R1 | Coxa |
| #1 | 10 | R1 | Femur |
| #1 | 11 | R1 | Tibia |
| #2 | 0 | R2 | Coxa |
| #2 | 1 | R2 | Femur |
| #2 | 2 | R2 | Tibia |
| #2 | 3 | R3 | Coxa |
| #2 | 4 | R3 | Femur |
| #2 | 5 | R3 | Tibia |

### Leg Numbering (top view)

```
     FRONT
  L1       R1
    \     /
     \   /
  L2--[B]--R2
     /   \
    /     \
  L3       R3
     REAR
```

## Software Architecture

### Option A: Pi Pico (MicroPython)

```
main.py
├── hexapod.py      # Leg kinematics, gait engine
├── servo.py        # PCA9685 wrapper
├── gait.py         # Tripod, wave, ripple patterns
└── remote.py       # Bluetooth/serial control
```

### Option B: Pi Zero 2W (Python + ROS2)

```
hex_ws/src/
├── hex_control/        # Servo control node
├── hex_kinematics/     # IK solver
├── hex_gait/           # Gait generator
└── hex_teleop/         # Joystick/keyboard control
```

### Inverse Kinematics

Each leg needs IK to convert (x, y, z) foot position to servo angles:

```python
def leg_ik(x, y, z, coxa_len, femur_len, tibia_len):
    """
    x: forward/back from coxa
    y: left/right from coxa
    z: up/down from coxa
    Returns: (coxa_angle, femur_angle, tibia_angle) in degrees
    """
    # Coxa angle (top-down rotation)
    coxa_angle = atan2(y, x)

    # Distance in XY plane
    xy_dist = sqrt(x**2 + y**2) - coxa_len

    # Distance to foot
    foot_dist = sqrt(xy_dist**2 + z**2)

    # Femur and tibia angles (2-link planar IK)
    # Law of cosines
    cos_tibia = (femur_len**2 + tibia_len**2 - foot_dist**2) / (2 * femur_len * tibia_len)
    tibia_angle = acos(clamp(cos_tibia, -1, 1))

    cos_femur = (femur_len**2 + foot_dist**2 - tibia_len**2) / (2 * femur_len * foot_dist)
    femur_angle = atan2(z, xy_dist) + acos(clamp(cos_femur, -1, 1))

    return degrees(coxa_angle), degrees(femur_angle), degrees(tibia_angle)
```

## Build Phases

### Phase 1: Design and Print
- [ ] Design body plates in CAD (Fusion 360 / OpenSCAD)
- [ ] Design leg segments with servo pockets
- [ ] Print test leg (1x) to verify fit
- [ ] Print remaining parts

### Phase 2: Electronics
- [ ] Test PCA9685 with single servo
- [ ] Set second PCA9685 to address 0x41
- [ ] Wire power distribution
- [ ] Test all 18 servos individually

### Phase 3: Assembly
- [ ] Mount servos in printed brackets
- [ ] Assemble one leg completely
- [ ] Verify range of motion
- [ ] Assemble remaining legs
- [ ] Mount electronics in body

### Phase 4: Software
- [ ] Servo calibration (center positions)
- [ ] Single leg IK test
- [ ] Standing pose (all legs)
- [ ] Basic tripod gait
- [ ] Remote control integration

### Phase 5: Refinement
- [ ] Tune gait parameters
- [ ] Add wave/ripple gaits
- [ ] Battery monitoring
- [ ] Optional: IMU for balance

## Reference Dimensions

Based on SG90/HS-82MG servo sizes:

| Servo | Size (mm) | Weight | Torque |
|-------|-----------|--------|--------|
| SG90 | 23 x 12 x 29 | 9g | 1.8 kg-cm |
| HS-82MG | 30 x 12 x 30 | 19g | 3.4 kg-cm |

Suggested link lengths:
- Coxa: 25mm (short, just clears body)
- Femur: 50-60mm
- Tibia: 70-80mm
- Total reach: ~150mm from body center

## Resources

- Inverse Kinematics: https://oscarliang.com/inverse-kinematics-implementation-hexapod-robots/
- PCA9685 library: adafruit-circuitpython-pca9685
- Gait patterns: https://www.robotshop.com/community/blog/show/hexapod-robot-gait-simulation

---

*Created: 2025-12-28*
