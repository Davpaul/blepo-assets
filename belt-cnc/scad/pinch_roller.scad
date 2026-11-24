// Printed pinch roller: replaces the 625 ball bearing on each corner unit's pinch post.
// It spins on the M5 bolt and only presses the belt onto the drive pulley.
// Same size as a 625 (16mm across, 5mm thick), so nothing else changes.
// Tighten the nyloc nut above it only until the roller still spins freely.
// Print flat. Use 100% infill for these: they are small and should be solid.

od     = 16;
width  = 5;
bore_d = 5.45;   // M5 bolt plus running clearance
hub_d  = 9;      // slightly raised hub, so only the centre touches the spacer and nut
hub_h  = 0.3;

$fn = 90;

module pinch_roller() {
    difference() {
        union() {
            translate([0, 0, hub_h]) cylinder(h = width - 2 * hub_h, d = od);
            cylinder(h = width, d = hub_d);
        }
        translate([0, 0, -1]) cylinder(h = width + 2, d = bore_d);
    }
}

pinch_roller();
