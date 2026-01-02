# Print Queue

Track print jobs for hexapod robot.

## JLC3DP Order

Ordering from [JLC3DP](https://jlc3dp.com/) - online 3D printing service.

**Quote page:** https://jlc3dp.com/3d-printing-quote

**STL files:** `hex/cad/stl/`

### Order Details

| Part | File | Qty | Material | Notes |
|------|------|-----|----------|-------|
| Coxa bracket | coxa_bracket.stl | 7 | PLA | +1 spare |
| Femur link | femur_link.stl | 7 | PLA | +1 spare |
| Tibia link | tibia_link.stl | 7 | PLA | +1 spare |
| Foot tip | foot_tip.stl | 7 | TPU | +1 spare |
| Body segment | body_segment.stl | 6 | PLA | |
| **Total** | | **34** | | |

### Print Settings (specify when ordering)

**PLA parts:**
- Technology: FDM
- Infill: 15-20%
- Layer: 0.2mm
- Color: Gray (or any)

**TPU parts (foot_tip):**
- Technology: FDM
- Material: TPU
- Infill: 20%
- Color: Black

### Cost Estimate

| Item | Cost |
|------|------|
| PLA parts (27×) | ~$35 |
| TPU parts (7×) | ~$10 |
| Shipping | ~$10-15 |
| **Total** | **~$55-60** |

### Timeline

| Stage | Time |
|-------|------|
| Build | 2-5 days |
| Shipping | 7-14 days |
| **Total** | **~2-3 weeks** |

### Order Status

- [ ] Upload STL files
- [ ] Select materials and quantities
- [ ] Place order
- [ ] Order shipped
- [ ] Order received
- [ ] Verify fit with servo

---

## Part Quantities (Full Robot)

| Part | Per Leg | Legs | Body | Total | +Spare | Order |
|------|---------|------|------|-------|--------|-------|
| coxa_bracket | 1 | 6 | - | 6 | +1 | 7 |
| femur_link | 1 | 6 | - | 6 | +1 | 7 |
| tibia_link | 1 | 6 | - | 6 | +1 | 7 |
| foot_tip | 1 | 6 | - | 6 | +1 | 7 |
| body_segment | - | - | 6 | 6 | - | 6 |

## Print Settings Reference

### PLA Light (leg parts - optimized for weight)
```
Layer: 0.2mm
Infill: 15%
Walls: 2
Speed: 60mm/s
Temp: 210/60
```

### TPU Flexible (feet)
```
Layer: 0.2mm
Infill: 20%
Walls: 3
Speed: 25mm/s
Temp: 230/50
```
