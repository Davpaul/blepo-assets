// Printed Z-axis bushing: a drop-in replacement for an LM8UU linear bearing.
// Same outside size (15mm x 24mm), so it presses into the carriage the same way.
// The bore has three shallow channels so dust has somewhere to go and the
// contact area is smaller. Add a drop of light machine oil.
// Print standing up (axis vertical) so the bore comes out round.

od      = 15;     // outside, same as an LM8UU
length  = 24;
bore_d  = 8.35;   // 8mm rod plus running clearance; PETG holes print a little small
channel = 1.6;    // width of the dust channels
chamfer = 0.8;    // lead-in at each end of the bore

$fn = 72;

module z_bushing() {
    difference() {
        cylinder(h = length, d = od);
        translate([0, 0, -1]) cylinder(h = length + 2, d = bore_d);
        for (i = [0 : 2])
            rotate([0, 0, 120 * i]) translate([bore_d / 2 - 0.2, -channel / 2, -1]) cube([0.9, channel, length + 2]);
        translate([0, 0, -0.01]) cylinder(h = chamfer, d1 = bore_d + 2 * chamfer, d2 = bore_d);
        translate([0, 0, length - chamfer + 0.01]) cylinder(h = chamfer, d1 = bore_d, d2 = bore_d + 2 * chamfer);
    }
}

z_bushing();
