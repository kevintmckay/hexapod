# Big Hex Sensor Array

Simple but complete sensor setup for autonomous walking.

## Overview

| Sensor | Purpose | Qty | Price | Total |
|--------|---------|-----|-------|-------|
| MPU6050 | IMU (balance/tilt) | 1 | $3 | $3 |
| VL53L0X | ToF distance (obstacles) | 3 | $5 | $15 |
| Limit switch | Foot contact | 6 | $0.50 | $3 |
| INA219 | Power monitor | 1 | $4 | $4 |
| **Total** | | **11** | | **~$25** |

## Sensor Details

### 1. MPU6050 - Balance/Orientation

```
Type:       6-axis IMU (3-axis gyro + 3-axis accel)
Interface:  I2C (0x68)
Voltage:    3.3V
Size:       20 x 16mm
Price:      ~$3
```

**Capabilities:**
- Pitch, roll, yaw detection
- Angular velocity (gyro): ±250 to ±2000°/s
- Acceleration: ±2g to ±16g
- Built-in DMP for sensor fusion

**Use cases:**
- Detect slopes and adjust gait
- Fall detection and recovery
- Level body on uneven terrain
- Smooth motion filtering

### 2. VL53L0X - Distance Sensing (×3)

```
Type:       Time-of-Flight laser ranging
Interface:  I2C (0x29, configurable)
Range:      30mm - 2000mm
Accuracy:   ±3%
Voltage:    2.8-5V
Size:       13 x 18mm
Price:      ~$5 each
```

**Placement:**
```
            FRONT
              │
     VL53L0X  │  VL53L0X
      (L)     │    (R)
        \     │     /
         \    │    /
          ┌───┴───┐
          │VL53L0X│  (center, angled 30° down)
          │ BODY  │
          └───────┘
```

**Use cases:**
- Obstacle detection (walls, objects)
- Drop-off/cliff detection (stairs, edges)
- Distance to objects for navigation
- Front-facing coverage ~120°

**I2C Address Setup:**
Each VL53L0X defaults to 0x29. To use multiple:
1. Hold XSHUT low on all but one
2. Set new address via software
3. Release next XSHUT, repeat

```
Sensor    XSHUT Pin    Address
------    ---------    -------
Center    GPIO 17      0x29
Left      GPIO 27      0x30
Right     GPIO 22      0x31
```

### 3. Foot Contact Switches (×6)

```
Type:       Micro limit switch (lever arm)
Interface:  Digital GPIO (pulled up)
Voltage:    3.3V logic
Size:       20 x 10mm
Price:      ~$0.50 each
```

**Wiring:**
```
3.3V ─────┐
          │
     ┌────┴────┐
     │  Switch │
     └────┬────┘
          │
GPIO ─────┼───── 10kΩ ───── GND
     (INPUT_PULLUP)
```

**GPIO Assignment:**
```
Foot    GPIO Pin
----    --------
L1      GPIO 5
L2      GPIO 6
L3      GPIO 13
R1      GPIO 19
R2      GPIO 26
R3      GPIO 12
```

**Use cases:**
- Detect ground contact during step
- Adaptive gait timing
- Terrain irregularity sensing
- Step confirmation before weight transfer

**Alternative: Use LX-16A Load Feedback**
The LX-16A servos report load/torque. A spike in tibia servo load indicates ground contact - can supplement or replace physical switches.

### 4. INA219 - Power Monitor

```
Type:       Current/voltage/power sensor
Interface:  I2C (0x40)
Voltage:    3-5.5V
Current:    Up to 3.2A (±0.8mA resolution)
Size:       25 x 25mm
Price:      ~$4
```

**Wiring:**
```
Battery + ──► INA219 VIN+ ──► INA219 VIN- ──► Load (BEC)
```

**Use cases:**
- Battery voltage monitoring (low battery warning)
- Current draw measurement
- Power consumption logging
- Stall detection (current spike)

## Wiring Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Pi Zero 2W GPIO                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   3.3V (Pin 1)  ───┬──► MPU6050 VCC                             │
│                    ├──► VL53L0X VCC (×3)                        │
│                    ├──► INA219 VCC                              │
│                    └──► Pull-up resistors                       │
│                                                                 │
│   GND (Pin 6)   ───┬──► All sensor GND                          │
│                    └──► Switch common                           │
│                                                                 │
│   SDA (GPIO 2)  ───────► I2C Data bus ──┬── MPU6050             │
│                                         ├── VL53L0X (×3)        │
│                                         └── INA219              │
│                                                                 │
│   SCL (GPIO 3)  ───────► I2C Clock bus ─┴── (all I2C devices)   │
│                                                                 │
│   GPIO 17 ─────────────► VL53L0X Center XSHUT                   │
│   GPIO 27 ─────────────► VL53L0X Left XSHUT                     │
│   GPIO 22 ─────────────► VL53L0X Right XSHUT                    │
│                                                                 │
│   GPIO 5  ─────────────► Foot Switch L1                         │
│   GPIO 6  ─────────────► Foot Switch L2                         │
│   GPIO 13 ─────────────► Foot Switch L3                         │
│   GPIO 19 ─────────────► Foot Switch R1                         │
│   GPIO 26 ─────────────► Foot Switch R2                         │
│   GPIO 12 ─────────────► Foot Switch R3                         │
│                                                                 │
│   TX (GPIO 14) ────────► LX-16A Serial Bus (servos)             │
│   RX (GPIO 15) ◄─────── LX-16A Serial Bus                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## I2C Address Map

```
Address    Device
-------    ------
0x29       VL53L0X Center (default)
0x30       VL53L0X Left (configured)
0x31       VL53L0X Right (configured)
0x44       INA219 (A0 jumper soldered - see note below)
0x68       MPU6050
```

**IMPORTANT - INA219 Address Conflict:**
The INA219 defaults to address 0x40, which conflicts with PCA9685 #1 (servo driver).
To avoid this conflict, solder the A0 jumper on the INA219 board to change its address to 0x44.

INA219 address options:
- 0x40: A0=GND, A1=GND (default - conflicts with PCA9685!)
- 0x41: A0=VS+, A1=GND (conflicts with PCA9685 #2)
- 0x44: A0=GND, A1=VS+ (recommended)
- 0x45: A0=VS+, A1=VS+

When initializing the INA219 in Python:
```python
ina = adafruit_ina219.INA219(i2c, addr=0x44)
```

## Software Libraries

### Python (Raspberry Pi)

```bash
# Install libraries
pip install adafruit-circuitpython-mpu6050
pip install adafruit-circuitpython-vl53l0x
pip install adafruit-circuitpython-ina219
pip install RPi.GPIO
```

### Basic Usage

```python
import board
import busio
import adafruit_mpu6050
import adafruit_vl53l0x
import adafruit_ina219
import RPi.GPIO as GPIO

# I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# IMU
mpu = adafruit_mpu6050.MPU6050(i2c)
print(f"Accel: {mpu.acceleration}")
print(f"Gyro: {mpu.gyro}")

# Distance sensor
vl53 = adafruit_vl53l0x.VL53L0X(i2c)
print(f"Distance: {vl53.range}mm")

# Power monitor
ina = adafruit_ina219.INA219(i2c)
print(f"Voltage: {ina.bus_voltage}V")
print(f"Current: {ina.current}mA")

# Foot switches
GPIO.setmode(GPIO.BCM)
FOOT_PINS = [5, 6, 13, 19, 26, 12]
for pin in FOOT_PINS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def foot_contact(leg):
    return not GPIO.input(FOOT_PINS[leg])
```

## Sensor Fusion Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    SENSOR FUSION                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   MPU6050 ──► Body tilt ──► Adjust leg heights              │
│                         └──► Detect falling ──► Recovery    │
│                                                             │
│   VL53L0X ──► Obstacle ahead ──► Stop/turn                  │
│          └──► Drop detected ──► Don't step there            │
│                                                             │
│   Foot SW ──► Ground contact ──► Transfer weight            │
│          └──► No contact ──► Extend leg further             │
│                                                             │
│   INA219 ──► Low voltage ──► Return to base / warn user     │
│          └──► High current ──► Reduce speed / check stall   │
│                                                             │
│   LX-16A ──► Servo load ──► Supplement foot contact         │
│   (built-in) Position ──► Verify movement completed         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Parts List (with links)

| Part | Link | Price |
|------|------|-------|
| MPU6050 | [Amazon](https://www.amazon.com/HiLetgo-MPU-6050-Accelerometer-Gyroscope-Converter/dp/B00LP25V1A) | $3 |
| VL53L0X (3-pack) | [Amazon](https://www.amazon.com/HiLetgo-VL53L0X-Distance-Measurement-Breakout/dp/B071DW8M8V) | $12 |
| Micro Limit Switch (10-pack) | [Amazon](https://www.amazon.com/Cylewet-Switch-Action-Arduino-CYT1073/dp/B07DQKZBQV) | $6 |
| INA219 | [Amazon](https://www.amazon.com/HiLetgo-INA219-Bi-direction-Current-Breakout/dp/B01DUVKZC4) | $4 |

## Optional Upgrades

| Sensor | Purpose | Price | Notes |
|--------|---------|-------|-------|
| BNO055 | 9-axis IMU + fusion | $25 | Better than MPU6050, built-in AHRS |
| VL53L1X | Longer range ToF | $12 | 4m range vs 2m |
| FSR402 | Analog foot pressure | $5 ea | Measure force, not just contact |
| BME280 | Environment | $5 | Temp, humidity, pressure |
| Pi Camera v2 | Vision | $25 | Object detection, SLAM |
| RPLidar A1 | 360° mapping | $100 | Full room mapping |
