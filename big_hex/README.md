# Big Hex - Large Hexapod Robot

![Big Hex Render](big-hex.png)

A larger hexapod build using LX-16A serial bus servos for improved torque, feedback, and simplified wiring.

## Why LX-16A Servos?

| Feature | SG90 (small hex) | LX-16A (big hex) |
|---------|------------------|------------------|
| Torque | 1.8 kg-cm | 17 kg-cm |
| Control | PWM | Serial Bus |
| Feedback | None | Position, Temp |
| Wiring | 18 separate cables | Daisy-chain per leg |
| Resolution | ~1° | 0.24° |
| Price | ~$2 | ~$15 |

## Specifications

| Spec | Value |
|------|-------|
| Legs | 6 |
| DOF per leg | 3 (coxa, femur, tibia) |
| Total servos | 18x LX-16A |
| Body size | ~350mm across |
| Leg reach | ~250mm from body center |
| Target weight | ~2.4kg |
| Payload capacity | ~500g |
| Torque margin | 55% |

## Servo Details

**LewanSoul/Hiwonder LX-16A**
- Torque: 17 kg-cm (6V) / 19.5 kg-cm (7.4V)
- Speed: 0.18s/60° (adjustable)
- Voltage: 6-7.4V
- Size: 40 x 20 x 40.5mm
- Weight: 57g
- Gear: Full metal
- Protocol: TTL Serial (half-duplex)
- Daisy-chain: Yes (up to 253 servos)
- Feedback: Position, temperature, voltage, load

## Cost Estimate

| Part | Qty | Unit Price | Total |
|------|-----|------------|-------|
| LX-16A servo | 18 | $15 | $270 |
| Servo controller board | 1 | $15 | $15 |
| 2S LiPo 7.4V 3000mAh | 1 | $25 | $25 |
| Raspberry Pi Zero 2W | 1 | $15 | $15 |
| Buck converter 6V 10A | 1 | $10 | $10 |
| 3D printed frame | - | ~$20 filament | $20 |
| Hardware (M3 screws, etc) | - | $15 | $15 |
| **Total** | | | **~$370** |

## Wiring Advantage

### PWM Servos (old way)
```
Pi --> PCA9685 #1 --> 12 separate servo cables
  `--> PCA9685 #2 --> 6 separate servo cables
```
- 18 individual 3-wire cables
- Cable management nightmare
- No feedback

### Serial Bus (LX-16A)
```
Pi (UART) --> L1_coxa --> L1_femur --> L1_tibia
          `-> L2_coxa --> L2_femur --> L2_tibia
          `-> L3_coxa --> L3_femur --> L3_tibia
          `-> R1_coxa --> R1_femur --> R1_tibia
          `-> R2_coxa --> R2_femur --> R2_tibia
          `-> R3_coxa --> R3_femur --> R3_tibia
```
- 6 daisy-chains (one per leg)
- Clean wiring through leg segments
- Full feedback on every servo

## Leg Dimensions

| Segment | Length | Notes |
|---------|--------|-------|
| Coxa | 50mm | Hip rotation |
| Femur | 80mm | Upper leg (optimized for torque) |
| Tibia | 120mm | Lower leg (optimized for torque) |
| **Total reach** | **~250mm** | From body center |

## Links

- [LX-16A on Amazon](https://www.amazon.com/LewanSoul-Real-Time-Feedback-Position-Temperature/dp/B073WR3SK9)
- [Hiwonder LX-16A](https://www.hiwonder.com/products/lx-16a)
- [Arduino Library](https://github.com/madhephaestus/lx16a-servo)
- [Python Library](https://github.com/maximkulkin/lewansoul-lx16a)
- [User Manual PDF](https://cdn.robotshop.com/rbm/a5e9ab51-86bc-497b-adac-003de3088fb7/9/92896585-5e83-4c7c-a663-650b81e5978b/67e9729b_lx-16a-serial-bus-servo-user-manual.pdf)
