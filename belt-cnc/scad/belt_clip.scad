// Belt-end clip: holds the folded loop at the end of each belt, in place of zip ties.
// Fold 40mm of belt back on itself with the teeth meshed, push the doubled belt
// through the slot, and tighten an M3 x 12 screw into the side hole. The loop
// left beyond the clip goes over the belt-end post.
// Print flat (slot horizontal).

belt_w   = 6;      // GT2 belt width
pair_t   = 2.3;    // two belts with teeth meshed, plus clearance
length   = 14;
wall     = 2.4;
pilot_d  = 2.8;    // M3 screw cuts its own thread

module belt_clip() {
    w = belt_w + 0.6 + 2 * wall;
    h = pair_t + 2 * wall;
    difference() {
        translate([-w / 2, 0, 0]) cube([w, length, h]);
        // slot for the doubled belt
        translate([-(belt_w + 0.6) / 2, -1, wall]) cube([belt_w + 0.6, length + 2, pair_t]);
        // pinch screw, from the top into the slot
        translate([0, length / 2, -1]) cylinder(h = h + 2, d = pilot_d, $fn = 24);
        // rounded entry so the belt doesn't snag
        translate([0, -0.01, wall + pair_t / 2]) rotate([-90, 0, 0]) scale([1.35, 1, 1]) cylinder(h = 1.2, d1 = belt_w + 1.6, d2 = belt_w + 0.6, $fn = 40);
    }
}

belt_clip();
