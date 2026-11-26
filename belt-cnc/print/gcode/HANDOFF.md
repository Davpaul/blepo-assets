# G-code handoff: for the chat or person controlling the printer

Printer: Artillery Sidewinder X1 on Klipper, 300 x 300mm bed, 0.4mm nozzle. Material: plain PETG, 1.75mm.
All G-code here is sliced already (PrusaSlicer, Klipper flavour, relative extrusion). The start code is inline, so no `PRINT_START` macro is needed.

## Files

| File | Contents | Time | PETG |
|---|---|---|---|
| `00_test_kit_x1_petg_klipper.gcode` | One corner bracket, one reel set, spare post parts (the one-corner test) | 9h 19m | 160g |
| `00b_test_kit_plus_twist_x1_petg_klipper.gcode` | The same, plus the Twist rig hardware (tripod mount, 2 couplers, 6 cable stops, 2 jaw springs) on one bed. Layout in `00b_test_kit_plus_twist_layout.png` | 12h 58m | 208g |
| `10_printed_extras_x1_petg_klipper.gcode` | 12 hold-down knobs, 4 Z bushings, 4 pinch rollers, 4 belt clips | 7h 17m | 129g |

Times are the slicer's estimates. Klipper usually runs a little faster.

## Settings in the 00 and 00b files

0.2mm layers, 5 walls, 5 top / 4 bottom layers, 35% cubic infill, any area under 200mm² printed solid, no supports.
Nozzle 240°C first layer then 235°C, bed 80°C, fan off for 3 layers then 30 to 50%.
Speeds: outer wall 45, inner wall 70, infill 80 mm/s. Acceleration 1000. Brim 5mm, skirt 3 loops.
Start code: `M140 S80`, `M104 S150`, `G28`, `M190 S80`, `M109 S240`, then a purge line at X5, Y10 to Y200.
Elephant-foot compensation 0.15mm.

## Things to check before and during the print

- **Purge line clearance (00 and 00b).** The purge line is at X 5 to 5.4mm. The skirt starts at about X 6.8mm, so there is only about 1mm to spare. The parts are positioned for this. Do not shift them left, or re-slice rather than move the G-code.
- **First layer.** The corner bracket is 142 x 176mm, flat and large. Watch the first layer. If a corner lifts, stop: a warped bracket will not seat on the pulley properly, and the pinch gap on it must be right. Clean the bed with washing-up liquid first. A thin wipe of glue stick works as a release layer on PEI.
- **Filament.** Dry PETG. Stringy or crackling prints mean damp filament.
- **Check the bed temperature and Z offset** are your usual ones for PETG. The file does not set a Z offset.

## What is not tested

None of this has been printed or built yet. The bracket's belt pinch gap is the tightest fit in the machine: after printing, test it with a scrap of belt before printing the other three brackets (see `../../TEST_KIT.md`).

## Sources

The belt CNC parts come from `belt-cnc/cad` and `belt-cnc/scad`. The Twist rig parts in `00b` are the user's own, supplied separately, with their settings changed as listed above.
