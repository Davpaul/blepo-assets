// Hold-down knob for the corner units: replaces a wing nut and penny washer.
// Press an M6 nut into the hex pocket underneath, then screw the knob down onto
// the stud that holds the corner unit to the table. Print flat face down.
// PETG, 4 to 5 walls, 40 to 50% infill, no supports.

height   = 22;     // overall height
core_r   = 13;     // centre of the knob
lobe_r   = 5;      // the six finger lobes
lobe_at  = 13;     // how far out the lobes sit
top_r    = 15.5;   // the sides taper in to this radius at the top
nut_af   = 10.25;  // M6 nut across flats, plus clearance for a press fit
nut_deep = 5.2;    // M6 nut thickness, plus a little
bore_d   = 6.5;    // clearance for the M6 stud
roof     = 3;      // solid top above the stud

$fn = 64;

module hold_down_knob() {
    difference() {
        intersection() {
            union() {
                cylinder(h = height, r = core_r);
                for (i = [0 : 5])
                    rotate([0, 0, 60 * i]) translate([lobe_at, 0, 0]) cylinder(h = height, r = lobe_r, $fn = 40);
            }
            cylinder(h = height, r1 = 22, r2 = top_r);
        }
        // M6 nut pocket, open at the bottom
        translate([0, 0, -1]) cylinder(h = nut_deep + 1, r = nut_af / sqrt(3), $fn = 6);
        // stud clearance, closed at the top
        translate([0, 0, -1]) cylinder(h = height - roof + 1, d = bore_d);
    }
}

hold_down_knob();
