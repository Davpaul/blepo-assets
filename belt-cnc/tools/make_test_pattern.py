"""Write G-code that marks a rectangle of dots for checking accuracy.

Use the pen caddy (or a V-bit with --depth 0.3). It marks the four corners
and the centre of a rectangle centred on the table. Measure the dots with a
tape and feed the numbers to calibrate.py.

    python3 make_test_pattern.py --table 2440 1220 --inset 300 > dots.gcode
"""
import argparse


def points(width, height, inset):
    x0, x1, y0, y1 = inset, width - inset, inset, height - inset
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), ((x0 + x1) / 2, (y0 + y1) / 2)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", nargs=2, type=float, default=[2440, 1220], metavar=("WIDTH", "HEIGHT"))
    ap.add_argument("--inset", type=float, default=300, help="distance of the dots from the table edges, mm")
    ap.add_argument("--depth", type=float, default=0.0, help="how far below Z0 to go for each mark")
    ap.add_argument("--lift", type=float, default=5.0)
    ap.add_argument("--feed", type=float, default=1200)
    a = ap.parse_args()
    print("; accuracy test dots. Coordinates are machine coordinates (table frame).")
    print("; Set Z0 at the surface first:  G10 L20 P1 Z0")
    print(f"G21 G90\nG0 Z{a.lift:.2f}")
    for (x, y) in points(a.table[0], a.table[1], a.inset):
        print(f"G53 G0 X{x:.2f} Y{y:.2f}\nG1 Z{-a.depth:.2f} F200\nG4 P0.3\nG0 Z{a.lift:.2f}")
    cx, cy = a.table[0] / 2, a.table[1] / 2
    print(f"G53 G0 X{cx:.2f} Y{cy:.2f}\nM2")


if __name__ == "__main__":
    main()
