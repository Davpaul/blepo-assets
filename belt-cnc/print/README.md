# Printing the parts in OrcaSlicer

Everything here is set up for your Artillery Sidewinder X1 on Klipper, with plain PETG.

## 1. Import the presets (once)

In OrcaSlicer: **File > Import > Import Configs...** and pick all four files in `orca/`:

| File | What it is |
|---|---|
| `machine_artillery_x1_klipper.json` | Your printer (the same one you sent me) |
| `filament_generic_petg_x1.json` | Your PETG settings (the same one you sent me) |
| `process_belt_cnc_strong.json` | For the structural parts: 5 walls, 6 top / 5 bottom layers, 50% gyroid |
| `process_belt_cnc_standard.json` | For everything else: 4 walls, 5 top / 4 bottom layers, 40% gyroid |

Both process presets use your speeds (45 outer, 70 inner, 80 infill, 1000 accel), supports off, auto brim.

## 2. Print the plates

Open each `.3mf` in `plates/`, choose the process preset its name says, slice, print. Every part is already turned the right way up and laid out on a 300 x 300 bed. Each part stays a separate object, so you can delete or move one.

| Plate | Preset | Parts | Time | PETG |
|---|---|---|---|---|
| `01_strong_corner_brackets_a` | strong | 2 corner brackets | 15h 30m | 207g |
| `02_strong_corner_brackets_b` | strong | 2 corner brackets | 15h 30m | 207g |
| `03_strong_carriage_bridge` | strong | Z carriage, Z bridge | 20h 05m | 255g |
| `04_standard_sled_base` | standard | sled base, plus all the post spacers, sleeves and measuring caps (with a spare of each) | 18h 45m | 251g |
| `05_standard_reels` | standard | 4 reel bodies | 7h 10m | 121g |
| `06_standard_flanges_cups` | standard | 4 reel flanges, 4 motor cups | 7h 00m | 123g |
| `07_standard_tools` | standard | dust shoe, pen holder and slider, laser holder, 4 knobs, 2 laser shims | 26h 30m | 344g |
| `08_standard_tray` | standard | electronics tray | 10h 40m | 187g |
| `09_standard_lid` | standard | electronics lid | 5h 05m | 88g |
| `10_printed_extras` | see below | 12 hold-down knobs, 4 Z bushings, 4 pinch rollers, 4 belt-end clips | 15h 10m | 208g |
| **Total** | | | **about 141 hours** | **about 2kg** |

Times come from slicing each plate with your machine's settings in PrusaSlicer (which shares its slicing engine with OrcaSlicer). Expect OrcaSlicer's own estimate to land within about 15% of these. Klipper usually prints a little faster than either estimate.

**Filament:** buy 3kg. The full set needs about 2kg including the printed extras.

## Suggested order

1. **Plate 01** first, then build one corner unit and do the pinch-gap check (manual, section 3). If the gap is wrong, fix it before printing plate 02.
2. **Plate 04** next: it has the small post parts every corner needs.
3. Then 05 and 06 (reels), 03 (Z axis), 02, 08, 09.
4. **Plate 07** last. The laser holder, pen holder and shims on it are optional: delete what you don't want before slicing to save time. The dust shoe alone takes about 4 hours.

## Why these settings make the parts strong

- **Walls do most of the work.** In a 3D print, strength comes mainly from the solid outer walls, not the infill. Five walls on a 0.4mm nozzle is a 2mm solid skin, which is where the bolts, the motor and the router clamp put their load.
- **Gyroid infill** is equally strong in every direction and doesn't form weak planes, so it suits parts pulled from several sides like the corner brackets.
- **Thicker top and bottom** (6 and 5 layers, 1.2 and 1mm) on the strong plates stiffens the flat plates that carry the motor and belt.
- **Orientation is already chosen** so the main loads run along the layers, not across them. The corner brackets print with the big flat face down, which puts the belt pull in the plane of each layer, the strongest direction for a print.
- **PETG at 235 to 240°C** bonds its layers well. If a part ever cracks along a layer line, raise the nozzle by 5°C and lower the fan.

## Tips

- Clean the bed with washing-up liquid and water before the big plates. PETG sticks too well to some PEI sheets: a thin wipe of glue stick acts as a release layer.
- The sled base and the tray are large and flat. Watch the first layer; if a corner starts to lift, stop and add a brim rather than finishing a warped part.
- Print one extra of the small spacers and sleeves while the printer is still in one piece. They are already on plate 04.

## Rebuilding the plates

If you change a part in `cad/`, run `python3 cad/build.py` and then `python3 print/make_plates.py`.

## Plate 10: printed extras, ready-to-print G-code

`gcode/10_printed_extras_x1_petg_klipper.gcode` is sliced already, for your Sidewinder X1 on Klipper with PETG, using your own start and end code. Upload it to Klipper and print. No slicer needed.

| Part | Qty | Replaces |
|---|---|---|
| `hold_down_knob` | 12 | Wing nuts and penny washers. Press an M6 nut into the hex pocket underneath. |
| `z_bushing` | 4 | LM8UU linear bearings in the Z carriage. Same size, press in the same way. Oil the rods lightly. |
| `pinch_roller` | 4 | The 625 bearings on the pinch posts. Same size. Tighten the nut only until it still spins. |
| `belt_clip` | 4 | The zip ties on each belt's end loop. Pinch with an M3 x 12 screw. |

Settings used: 0.2mm layers, 5 walls, 6 top / 5 bottom layers, 50% cubic infill, 235°C (240°C first layer), bed 80°C, your speeds and acceleration. About 15 hours and 208g.

The OpenSCAD source for all four parts, and for this plate (`plate_printed_extras.scad`), is in `../scad/`. Every size that matters is a named number at the top of each file, so you can adjust a fit (the bushing bore, say) and re-export. `gcode/x1_petg_klipper_prusaslicer.ini` holds the exact settings used, if you want to re-slice in PrusaSlicer; in OrcaSlicer, use the strong preset.

**Test before trusting:** the printed bushings and rollers are worth trying on your first corner unit and carriage before you leave the metal bearings out altogether. If the bushings bind, open the bore up a little in `z_bushing.scad` (`bore_d`).
