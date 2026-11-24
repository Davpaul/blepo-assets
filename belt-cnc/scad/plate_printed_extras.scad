// Everything on one 300 x 300mm bed (Artillery Sidewinder X1):
//   12 hold-down knobs, 4 Z bushings, 4 pinch rollers, 4 belt-end clips.
// Export this whole file as one STL, or use the ready G-code next to it.

use <hold_down_knob.scad>
use <z_bushing.scad>
use <pinch_roller.scad>
use <belt_clip.scad>

pitch = 46;                 // spacing of the knob grid
// 12 knobs in a 4 x 3 grid
for (ix = [0 : 3], iy = [0 : 2])
    translate([60 + ix * pitch, 70 + iy * pitch, 0]) hold_down_knob();
// small parts in a row along the front
for (i = [0 : 3]) translate([60 + i * 26, 30, 0]) z_bushing();
for (i = [0 : 3]) translate([164 + i * 24, 30, 0]) pinch_roller();
// clips along the back
for (i = [0 : 3]) translate([70 + i * 26, 210, 0]) belt_clip();
