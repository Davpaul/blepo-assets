# Printing the parts in OrcaSlicer

Everything here is set up for your Artillery Sidewinder X1 on Klipper, with plain PETG.

## 1. Import the presets (once)

In OrcaSlicer: **File > Import > Import Configs...** and pick all five files in `orca/`:

| File | What it is |
|---|---|
| `machine_artillery_x1_klipper.json` | Your printer (the same one you sent me) |
| `filament_generic_petg_x1.json` | Your PETG settings (the same one you sent me) |
| `process_belt_cnc_strong.json` | Parts that carry the machine's loads: 0.2mm layers, 5 walls, 5 top / 4 bottom, 35% gyroid |
| `process_belt_cnc_standard.json` | Medium parts: 0.28mm layers, 4 walls, 4 top / 4 bottom, 25% gyroid |
| `process_belt_cnc_light.json` | Lightly loaded parts: 0.28mm layers, 3 walls, 4 top / 3 bottom, 15% gyroid |

All three use your speeds (45 outer, 70 inner, 80 infill, 1000 accel), supports off, auto brim. All three also print any small area solid (`minimum_sparse_infill_area` 200mm²), so pegs, bosses and small parts come out solid automatically.

## 2. Print the plates

Open each `.3mf` in `plates/`, choose the preset its name says, slice, print. Every part is already turned the right way up and laid out on a 300 x 300 bed. Each part stays a separate object, so you can delete or move one.

| Plate | Preset | Parts | Time | PETG |
|---|---|---|---|---|
| `00_test_kit` | strong (G-code ready) | the **minimum test**: 1 corner bracket, 1 reel set, spare post spacers. See `../TEST_KIT.md` | 9h 20m | 160g |
| `01_strong_corner_brackets_a` | strong | 2 corner brackets | 12h 50m | 181g |
| `02_strong_corner_brackets_b` | strong | 2 corner brackets | 12h 50m | 181g |
| `03_strong_carriage_bridge` | strong | Z carriage, Z bridge | 16h 30m | 229g |
| `04_standard_sled_base` | standard | sled base, plus all the post spacers, sleeves and measuring caps (with a spare of each) | 11h 55m | 234g |
| `05_light_reels` | light | 4 reel bodies | 4h 45m | 111g |
| `06_light_flanges_cups` | light | 4 reel flanges, 4 motor cups | 5h 05m | 118g |
| `07_standard_tools` | standard | dust shoe, pen holder and slider, laser holder, 4 knobs, 2 laser shims | 15h 50m | 308g |
| `08_light_tray` | light | electronics tray | 7h 50m | 180g |
| `09_light_lid` | light | electronics lid | 3h 45m | 82g |
| `10_printed_extras` | light (G-code ready) | 12 hold-down knobs, 4 Z bushings, 4 pinch rollers, 4 belt-end clips | 7h 15m | 129g |
| **Total (plates 01 to 10, without the test kit)** | | | **about 98 hours** | **about 1.75kg** |

That is about 43 hours and 240g less than the first settings I gave you, from matching each part's settings to the load it carries (see "Why these settings" below).

Times come from slicing each plate with your machine's settings in PrusaSlicer (which shares its slicing engine with OrcaSlicer). Expect OrcaSlicer's own estimate to land within about 15% of these. Klipper usually prints a little faster than either estimate.

**Filament:** buy 2kg if you are confident, 3kg to allow for a failed print or two.

## Suggested order

0. **Plate 00, the test kit, first.** It is one corner unit on a bench for about £50 and nine hours of printing: see `../TEST_KIT.md`. Do the rest once it works.

1. **Plate 01** first, then build one corner unit and do the pinch-gap check (manual, section 3). If the gap is wrong, fix it before printing plate 02.
2. **Plate 04** next: it has the small post parts every corner needs.
3. Then 05 and 06 (reels), 03 (Z axis), 02, 08, 09.
4. **Plate 07** last. The laser holder, pen holder and shims on it are optional: delete what you don't want before slicing to save time. The dust shoe alone takes about 4 hours.

## Why these settings

The aim is strength where the loads are, and no plastic or time wasted where they are not.

- **Walls do most of the work.** A print's strength comes mainly from its solid outer walls, not its infill. So the parts that carry the belt pull and the router (corner brackets, Z carriage, Z bridge) get 5 walls, a 2mm solid skin, while parts that only hold something in place get 3 or 4.
- **Infill was the main waste.** On parts this size, going from 50% to 35% infill on the strong parts changes their strength very little but saves hours. Lightly loaded parts like the reels, tray and knobs only need 15%.
- **Small areas print solid anyway.** Any region under 200mm² (the bushings, rollers, clips, spacers, pegs and bosses) prints solid whatever the infill setting, because that is where a sparse fill would be weakest.
- **Thicker layers where precision doesn't matter.** 0.28mm layers print about a quarter faster than 0.2mm. They are used everywhere except the strong plates. Those keep 0.2mm, because thinner layers bond together better, and the corner fences and router carriage are pushed in the direction that tries to peel layers apart.
- **Gyroid infill** is equally strong in every direction and has no weak planes. (The ready-made G-code for plate 10 uses cubic infill instead: just as strong, and it keeps the file small enough to upload.)
- **Orientation is already chosen** so the main loads run along the layers, not across them.
- **PETG at 235 to 240°C** bonds its layers well. If a part ever cracks along a layer line, raise the nozzle by 5°C and lower the fan.

**Biggest remaining saving:** plate 07 holds the pen and laser holders, which are optional. Delete what you don't need before slicing.

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

Settings used: the light preset (0.28mm layers, 3 walls, 4 top / 3 bottom, 15% cubic infill), with any area under 200mm² printed solid, so the bushings, rollers and clips come out fully solid and only the knobs use sparse infill. 235°C (240°C first layer), bed 80°C, your speeds and acceleration. About 7h 15m and 129g.

The OpenSCAD source for all four parts, and for this plate (`plate_printed_extras.scad`), is in `../scad/`. Every size that matters is a named number at the top of each file, so you can adjust a fit (the bushing bore, say) and re-export. `gcode/x1_petg_klipper_prusaslicer.ini` holds the exact settings used, if you want to re-slice in PrusaSlicer; in OrcaSlicer, use the light preset.

**Test before trusting:** the printed bushings and rollers are worth trying on your first corner unit and carriage before you leave the metal bearings out altogether. If the bushings bind, open the bore up a little in `z_bushing.scad` (`bore_d`).
