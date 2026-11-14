"""Turn five tape measurements into the table settings the firmware needs.

Measure between the measuring caps on the four belt-end posts, in mm:

    S  south-west post to south-east post      N  north-west post to north-east post
    W  south-west post to north-west post      E  south-east post to north-east post
    D  north-west post to south-east post (the diagonal)

"South" is the edge you stand at; south-west is the corner on your left.

    python3 table_config.py 2500.4 1280.8 2500.4 1280.8 2789.6             # S E N W D, prints the block
    python3 table_config.py 2500.4 1280.8 2500.4 1280.8 2789.6 --write ../firmware/belt-cnc.yaml
"""
import argparse, math, re
import numpy as np
import beltkin as K

NAMES = ["sw", "se", "ne", "nw"]


def block(t, margin):
    lines = []
    for i, n in enumerate(NAMES):
        lines += [f"{n}_pulley_x: {t.P[i][0]:.3f}", f"{n}_pulley_y: {t.P[i][1]:.3f}",
                  f"{n}_post_x: {t.F[i][0]:.3f}", f"{n}_post_y: {t.F[i][1]:.3f}",
                  f"{n}_pinch_deg: {math.degrees(t.pinch[i]) % 360:.3f}"]
    xs, ys = t.C[:, 0], t.C[:, 1]
    # largest rectangle that is inside all four corners, less a margin
    lo_x, hi_x = max(xs[0], xs[3]) + margin, min(xs[1], xs[2]) - margin
    lo_y, hi_y = max(ys[0], ys[1]) + margin, min(ys[2], ys[3]) - margin
    lines += [f"home_x: {t.centre[0]:.3f}", f"home_y: {t.centre[1]:.3f}",
              f"min_x: {lo_x:.3f}", f"max_x: {hi_x:.3f}", f"min_y: {lo_y:.3f}", f"max_y: {hi_y:.3f}"]
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("S", type=float); ap.add_argument("E", type=float); ap.add_argument("N", type=float)
    ap.add_argument("W", type=float); ap.add_argument("D", type=float)
    ap.add_argument("--margin", type=float, default=40.0, help="keep the bit this far inside the corner units, mm")
    ap.add_argument("--write", metavar="YAML", help="update this FluidNC config file in place")
    a = ap.parse_args()
    t = K.Table.from_measurements(a.S, a.E, a.N, a.W, a.D)

    c = t.C
    print("Table as measured (corner of each bracket, mm):")
    for n, p in zip(NAMES, c):
        print(f"  {n.upper()}: x {p[0]:8.1f}  y {p[1]:8.1f}")
    d_expected = math.hypot(a.S, a.W)
    print(f"  width {np.linalg.norm(c[1]-c[0]):.1f} (south) {np.linalg.norm(c[2]-c[3]):.1f} (north), "
          f"depth {np.linalg.norm(c[3]-c[0]):.1f} (west) {np.linalg.norm(c[2]-c[1]):.1f} (east)")
    ang = math.degrees(math.acos(np.dot(c[1]-c[0], c[3]-c[0]) / np.linalg.norm(c[1]-c[0]) / np.linalg.norm(c[3]-c[0])))
    print(f"  south-west corner angle {ang:.2f} degrees (90 is square; anything from 88 to 92 is fine, the software corrects it)")
    if abs(ang - 90) > 3:
        print("  !! That is a long way out of square. Re-check the diagonal before trusting this.")
    lines = block(t, a.margin)
    print("\nkinematics block:\n  BeltCNC:")
    for ln in lines:
        print("    " + ln)
    print(f"\nSled starts at the table centre: X {t.centre[0]:.1f}  Y {t.centre[1]:.1f}")
    print(f"Longest belt needed: {max(K.lengths(t, (x, y)).max() for x in (c[0][0]+60, c[1][0]-60) for y in (c[0][1]+60, c[3][1]-60)) + 150:.0f} mm per corner")

    if a.write:
        s = open(a.write).read()
        m = re.search(r"(?P<head>[ \t]*# >>> table[^\n]*\n)(?P<body>.*?)(?P<tail>[ \t]*# <<< table)", s, re.S)
        if not m:
            raise SystemExit("could not find the '# >>> table' ... '# <<< table' markers in " + a.write)
        indent = re.match(r"[ \t]*", m.group("head")).group(0)
        s = s[:m.start("body")] + "".join(indent + ln + "\n" for ln in lines) + s[m.start("tail"):]
        s = re.sub(r"(mpos_mm:\s*)[-\d.]+(\s*# =home_x)", lambda k: f"{k.group(1)}{t.centre[0]:.3f}{k.group(2)}", s)
        s = re.sub(r"(mpos_mm:\s*)[-\d.]+(\s*# =home_y)", lambda k: f"{k.group(1)}{t.centre[1]:.3f}{k.group(2)}", s)
        open(a.write, "w").write(s)
        print("updated", a.write)


if __name__ == "__main__":
    main()
