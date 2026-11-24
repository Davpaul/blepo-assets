# OpenSCAD parts

| File | What it is |
|---|---|
| `hold_down_knob.scad` | Lobed knob with an M6 nut pressed inside: holds each corner unit down on its studs |
| `z_bushing.scad` | Printed replacement for an LM8UU linear bearing |
| `pinch_roller.scad` | Printed replacement for the 625 pinch bearing |
| `belt_clip.scad` | Clamp for the folded loop at each belt end |
| `plate_printed_extras.scad` | All of the above laid out on one 300 x 300mm bed: 12 knobs, 4 of each of the rest |

Open any file in OpenSCAD, press F6 to render, then File > Export > STL. The sizes that matter are named at the top of each file.

Ready-sliced G-code for the plate, for the Artillery Sidewinder X1 on Klipper with PETG, is in `../print/gcode/`.

The rest of the machine's parts are modelled in Python in `../cad/` (they came first, and the assembly checks run on them). The knob exists in both, and the two match.
