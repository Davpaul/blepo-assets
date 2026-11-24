// Twist animatronic: small printable parts that replace bought hardware.
// Everything is a module with parameters at the top. All dimensions in mm.
// Render one part:   openscad -o out.stl -D 'part="washer_m5"' small_parts.scad
// Parts: washer_m5, knob_m6, standoff_m25, sheath_clip, gt2_pulley_20t
$fn = 96;

part = "plate";     // "plate" prints everything below on one 300 x 300 mm bed

// ---------- tolerances (tune after a test print) ----------
fit        = 0.2;   // extra clearance on printed holes and pockets
nut_m6_af  = 10.0;  // M6 nut across flats
nut_m6_t   = 5.2;   // M6 nut thickness
pipe_d     = 26.7;  // pipe outside diameter for the sheath clips (25.0 for the 25 mm folder)

// ---------- M5 washer: OD 10, ID 5.5, 1.2 mm (6 layers at 0.2) ----------
module washer_m5(od = 10, id = 5.5, t = 1.2) {
  difference() { cylinder(d = od, h = t); translate([0, 0, -1]) cylinder(d = id + fit, h = t + 2); }
}

// ---------- M6 knob: scalloped round grip round a captive plain M6 nut, cross slot on top ----------
// Press a normal M6 nut into the hex pocket from the flat side. The bolt end goes into a blind hole,
// so the top stays closed and carries the cross slot (takes a Phillips or a flat screwdriver).
bolt_room = 9;   // how far the bolt may stick out past the nut before it touches the top
module knob_m6(d = 28, h = 20, lobes = 8) {
  pocket = nut_m6_t + 0.4;
  difference() {
    union() {
      cylinder(d = d - 5, h = h);
      // scalloped grip: lobes round the rim, so a hand has something to push on
      for (i = [0 : lobes - 1]) rotate([0, 0, i * 360 / lobes + 180 / lobes])
        translate([d / 2 - 3.2, 0, 0]) cylinder(d = 6.4, h = h, $fn = 48);
    }
    // scallops between the lobes are the gaps already left by the smaller core
    translate([0, 0, -0.01]) cylinder(d = (nut_m6_af + fit) / cos(30), h = pocket, $fn = 6);   // nut pocket
    translate([0, 0, pocket - 0.1]) cylinder(d = 6.6, h = bolt_room + 0.1, $fn = 48);          // blind bolt hole
    // cross slot, 2.2 wide, 12 long, 3.5 deep
    for (a = [0, 90]) rotate([0, 0, a]) translate([-6, -1.1, h - 3.5]) cube([12, 2.2, 3.6]);
  }
}

// ---------- M2.5 standoff: OD 5.5, hole for a self-tapping M2.5 screw ----------
module standoff_m25(h = 8, od = 5.5, hole = 2.2) {
  difference() { cylinder(d = od, h = h); translate([0, 0, -1]) cylinder(d = hole, h = h + 2, $fn = 32); }
}

// ---------- sheath clip: snaps round the pipe, holds up to 5 PTFE tubes (4 mm OD) on its back ----------
module sheath_clip(d = pipe_d, tube = 4.0, n = 5, w = 10) {
  wall = 2.6; ro = d / 2 + wall; pitch = tube + 1.6;
  bar_w = n * pitch + 2; bar_t = tube + 2.4; by = ro + bar_t / 2 - 1.2;
  difference() {
    union() {
      cylinder(r = ro, h = w);
      translate([-bar_w / 2, ro - 1.2, 0]) cube([bar_w, bar_t, w]);
    }
    translate([0, 0, -1]) cylinder(d = d + fit, h = w + 2);
    // opening on the side opposite the tubes so it snaps on (about 80 percent of the diameter)
    translate([-d * 0.40, -ro - 1, -1]) cube([d * 0.8, ro, w + 2]);
    // tube grooves, open to the top so tubes press in
    for (i = [0 : n - 1]) {
      x = (i - (n - 1) / 2) * pitch;
      translate([x, ro - 1.2 + bar_t - tube / 2 - 0.3, -1]) cylinder(d = tube + 0.25, h = w + 2, $fn = 40);
      translate([x - (tube - 0.7) / 2, ro - 1.2 + bar_t - tube / 2 - 0.3, -1]) cube([tube - 0.7, bar_t, w + 2]);
    }
  }
}

// ---------- GT2 pulley, 20 teeth, 5 mm bore, flanged, with M3 grub screw ----------
// Tooth profile is a close match to GT2 (2 mm pitch): test against your belt before printing more.
module gt2_pulley_20t(bore = 5.0, belt_w = 6.5) {
  teeth = 20; pitch = 2; pd = teeth * pitch / PI;          // pitch diameter 12.73
  od = pd - 0.762;                                          // GT2 outside diameter
  hub_h = 8; fl_t = 1.2; total = hub_h + belt_w + 2 * fl_t;
  difference() {
    union() {
      cylinder(d = 16, h = fl_t);                          // lower flange
      translate([0, 0, fl_t]) cylinder(d = od, h = belt_w);
      translate([0, 0, fl_t + belt_w]) cylinder(d = 16, h = fl_t);
      translate([0, 0, 2 * fl_t + belt_w]) cylinder(d = 10, h = hub_h);
    }
    // tooth grooves
    for (i = [0 : teeth - 1]) rotate([0, 0, i * 360 / teeth])
      translate([od / 2 + 0.05, 0, fl_t - 0.01]) cylinder(d = 1.45, h = belt_w + 0.02, $fn = 24);
    // bore with a D flat for a stepper shaft
    translate([0, 0, -1]) difference() {
      cylinder(d = bore + fit, h = total + 2, $fn = 48);
      translate([bore / 2 - 0.35, -5, -1]) cube([5, 10, total + 4]);
    }
    // M3 grub screw and nut trap in the hub, pointing at the flat
    translate([0, 0, 2 * fl_t + belt_w + hub_h / 2]) rotate([0, 90, 0]) {
      cylinder(d = 2.7, h = 10, $fn = 24);
      translate([0, 0, bore / 2 + 0.3]) hull() { for (z = [0, 4]) translate([-z, 0, 0]) cylinder(d = 6.4 / cos(30), h = 2.6, $fn = 6); }
    }
  }
}

// ---------- layout: one plate, 300 x 300 mm bed (Artillery Sidewinder X1). Everything sits inside 20..280. ----------
module grid(n, step, ox, oy, per) {
  for (i = [0 : n - 1]) translate([ox + (i % per) * step, oy + floor(i / per) * step, 0]) children();
}

if (part == "plate") {
  grid(40, 13, 20, 20, 10) washer_m5();            // 40 M5 washers, 10 x 4
  grid(20, 10, 20, 88, 10) standoff_m25();         // 20 M2.5 standoffs, 10 x 2
  for (i = [0 : 2]) translate([30 + i * 32, 140, 0]) knob_m6();      // 3 knobs
  grid(4, 22, 130, 128, 4) gt2_pulley_20t();       // 4 GT2 pulleys (only needed for the stepper version)
  grid(8, 38, 40, 190, 4) sheath_clip();           // 8 sheath clips, 4 x 2
} else if (part == "washer_m5") washer_m5();
else if (part == "knob_m6") knob_m6();
else if (part == "standoff_m25") standoff_m25();
else if (part == "sheath_clip") sheath_clip();
else if (part == "gt2_pulley_20t") gt2_pulley_20t();
