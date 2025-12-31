# Big Hex Hardware List

## Servos

| Part | Qty | Specs | Price | Link |
|------|-----|-------|-------|------|
| LX-16A Serial Bus Servo | 18 | 17kg-cm, 7.4V, metal gear | ~$15 ea | [Amazon](https://www.amazon.com/LewanSoul-Real-Time-Feedback-Position-Temperature/dp/B073WR3SK9) |

### LX-16A Specifications
```
Torque:       17 kg-cm (6V) / 19.5 kg-cm (7.4V)
Speed:        0.18 sec/60° (adjustable via software)
Voltage:      6V - 7.4V DC
Angle:        0-240° (configurable)
Resolution:   0.24°
Size:         45 x 25 x 36mm (verified)
Weight:       52-57g
Gears:        Full metal
Bearings:     Dual ball bearing
Protocol:     TTL Serial (half-duplex, 115200 baud default)
Feedback:     Position, temperature, voltage, load
```

## Controller

| Part | Qty | Notes | Price |
|------|-----|-------|-------|
| Raspberry Pi Zero 2W | 1 | Main controller, UART for servos | $15 |
| LX-16A Debug Board | 1 | Optional - for servo configuration | $10 |

### Alternative Controllers
- Raspberry Pi 4 (more power, WiFi)
- ESP32 (cheaper, MicroPython)
- Arduino Mega + TTL level shifter

## Power

| Part | Qty | Specs | Price |
|------|-----|-------|-------|
| 2S LiPo Battery | 1 | 7.4V, 3000-5000mAh, 25C+ | $25-40 |
| Buck Converter | 1 | Input 7.4V, Output 6V 10A | $10 |
| Power switch | 1 | 10A rated | $3 |
| XT60 connectors | 2 | Battery connection | $5 |

### Power Budget
```
18 servos × 1A peak = 18A peak (worst case, all stalled)
18 servos × 0.3A avg = 5.4A typical draw
3000mAh battery = ~30 min runtime (estimate)
5000mAh battery = ~50 min runtime (estimate)
```

## Frame (3D Printed)

### Option A: Segmented Body (standard printers ~220mm bed)
| Part | Qty | Material | Est. Print Time |
|------|-----|----------|-----------------|
| Body plate segment (top) | 6 | PETG | 1.5h each |
| Body plate segment (bottom) | 6 | PETG | 1.5h each |
| Coxa bracket | 6 | PETG | 45min each |
| Femur link (80mm) | 6 | PETG | 40min each |
| Tibia link (120mm) | 6 | PETG | 30min each |
| Foot tip | 6 | TPU | 10min each |
| Standoff (45mm) | 12 | PETG | 5min each |
| **Total** | | | **~25h** |

### Option B: Full Body (large printers ~300mm+ bed)
| Part | Qty | Material | Est. Print Time |
|------|-----|----------|-----------------|
| Body plate (top) | 1 | PETG | 4h |
| Body plate (bottom) | 1 | PETG | 4h |
| Coxa bracket | 6 | PETG | 45min each |
| Femur link (80mm) | 6 | PETG | 40min each |
| Tibia link (120mm) | 6 | PETG | 30min each |
| Foot tip | 6 | TPU | 10min each |
| Standoff (45mm) | 12 | PETG | 5min each |
| **Total** | | | **~20h** |

### Print Settings
- Material: PETG (stronger than PLA)
- Layer height: 0.2mm
- Infill: 40% (structural parts)
- Walls: 4
- Supports: Yes (for servo pockets)
- Body segments: bolt together with M3x12 screws

## Hardware

| Part | Qty | Notes |
|------|-----|-------|
| M3 x 8mm screws | 50 | Servo mounting |
| M3 x 12mm screws | 30 | Frame assembly |
| M3 nuts | 50 | |
| M3 lock nuts | 20 | Joints |
| M3 washers | 50 | |
| Servo horn screws | 18 | Included with servos |
| Standoffs (3D printed) | 12 | Body plate spacing (45mm) |
| Zip ties | 50 | Cable management |
| Heat shrink | - | Wire connections |

## Wiring

| Part | Qty | Notes |
|------|-----|-------|
| 18AWG silicone wire (red) | 2m | Power distribution |
| 18AWG silicone wire (black) | 2m | Ground |
| 22AWG servo wire | 3m | Signal extension |
| JST-XH connectors | 20 | Servo connections |
| Dupont connectors | 20 | Pi connections |

## Tools Needed

- Soldering iron + solder
- Wire strippers
- Crimping tool (for JST/Dupont)
- Hex drivers (M2, M2.5, M3)
- 3D printer (or printing service)
- Multimeter

## Total Cost Estimate

| Category | Cost |
|----------|------|
| Servos (18x LX-16A) | $270 |
| Controller | $15 |
| Power system | $40 |
| 3D printing | $20 |
| Hardware | $15 |
| Wiring | $10 |
| **Total** | **~$370** |
