# Small printed parts (OpenSCAD)

These replace bought hardware. Source is `small_parts.scad`, with every dimension at the top.

| Part | Qty on the plate | Replaces | Notes |
|---|---|---|---|
| `washer_m5` | 40 | M5 washers | 10 mm OD, 5.5 mm hole, 1.2 mm thick. Fine for pivots and pinch bolts. Use real nylon washers instead for any pivot that wobbles |
| `knob_m6` | 3 | M6 wing nuts | Round scalloped knob, 28 mm across. Press a plain M6 nut into the hex pocket from the flat side. The top has a cross slot for a Phillips or flat screwdriver. The bolt may stick out up to 9 mm past the nut (`bolt_room`), so trim or swap a bolt that is longer |
| `standoff_m25` | 20 | M2.5 standoffs | 8 mm tall. The hole takes a self-tapping M2.5 screw. Change `h` for other heights |
| `sheath_clip` | 8 | Cable ties on the mast | Snaps round the pipe and holds up to five 4 mm PTFE tubes. Set `pipe_d` to 25.0 if you use 25 mm tube |
| `gt2_pulley_20t` | 4 | GT2 pulleys | Only needed for the stepper version. 5 mm bore with a D flat and an M3 grub screw. The tooth shape is close to GT2 but check it against your belt |

Not included, as agreed: speaker mount, lazy susan bearing, servo horns, jaw spring.

## Files

- `stl/` has each part on its own plus `plate.stl` with all of them together.
- `gcode/small_parts_plate_PETG_artillery_x1_klipper.gcode` is the whole plate sliced for an Artillery Sidewinder X1 running Klipper.
- `artillery_x1_PETG.ini` is the PrusaSlicer profile that made it. Load it to re-slice or tweak.

## Printing on the X1

- **Material:** PETG, 0.4 mm nozzle, 0.2 mm layers, 4 walls, 40% gyroid.
- **Temperatures:** 240 C first layer, 235 C after, bed 80 C. The stock X1 hot end tops out at 240 C, so don't raise these.
- **Plate:** one plate, about 9 h and about 69 g. It uses X 5 to 251 mm and Y 26 to 274 mm of the 300 x 300 bed.
- **Bed:** PETG can fuse to the glass bed and chip it. Wipe on a thin layer of glue stick first and let the bed cool before removing the parts.
- **Check before you run it:** the start code homes with G28 and does not level. If you build a bed mesh before each print, uncomment the `;BED_MESH_CALIBRATE` line in the start code, or swap the start code for your own `PRINT_START` macro. The G-code is plain Klipper-compatible G-code for a direct-drive extruder. Set your Z offset on the printer as usual.
- **Test fit first:** the washers and wing nuts are quick to check. Print one `knob_m6` and one `sheath_clip` alone (from `stl/`) before committing to the full plate, because the nut pocket and the pipe fit depend on your printer's tolerances. If the nut is loose or tight, change `fit` at the top of the file.

To regenerate: `openscad -o stl/plate.stl small_parts.scad` then slice with `prusa-slicer --export-gcode --load artillery_x1_PETG.ini stl/plate.stl`.
