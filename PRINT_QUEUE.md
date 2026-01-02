# Print Queue

Track print jobs across all robot projects.

## Queue Status

| # | Project | Part | Material | Profile | Time | Status |
|---|---------|------|----------|---------|------|--------|
| 1 | hexapod | coxa_bracket (test) | PLA | Light | 20m | READY |
| 2 | hexapod | femur_link (test) | PLA | Light | 30m | QUEUED |
| 3 | hexapod | tibia_link (test) | PLA | Light | 15m | QUEUED |
| 4 | hexapod | foot_tip (test) | TPU | Flexible | 15m | QUEUED |
| - | - | - | - | - | - | - |

## Completed Prints

| Date | Project | Part | Material | Time | Notes |
|------|---------|------|----------|------|-------|
| - | - | - | - | - | - |

## Print Settings Profiles

### PLA Light (leg parts - optimized for weight)
```
Layer: 0.2mm
Infill: 15%
Walls: 2
Speed: 60mm/s
Temp: 210/60
```

### PLA Standard (body plates, brackets)
```
Layer: 0.2mm
Infill: 20%
Walls: 3
Speed: 60mm/s
Temp: 210/60
```

### PETG Structural (load-bearing)
```
Layer: 0.2mm
Infill: 40%
Walls: 4
Speed: 45mm/s
Temp: 240/80
```

### TPU Flexible (wheels, feet)
```
Layer: 0.2mm
Infill: 20%
Walls: 3
Speed: 25mm/s
Temp: 230/50
```

## Estimated Total Print Time by Project

| Project | Parts | PLA | PETG | TPU | Total |
|---------|-------|-----|------|-----|-------|
| Hexapod | 25 | 12h | 5h | 2h | ~20h |
| Sawppy | 50+ | 40h | 60h | 10h | ~110h |
| Stair-Climber | 40 | 30h | 40h | 8h | ~80h |
| ExoMy | 30 | 25h | 25h | 5h | ~55h |
| **Total** | | | | | **~265h** |

## Failed Prints Log

| Date | Part | Reason | Fix |
|------|------|--------|-----|
| - | - | - | - |
