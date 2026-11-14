"""Where on the table can the machine hold the router?

For every bit position this works out the belt tension the motors must supply
to resist a sideways force (cutting force plus sled friction) in the worst
direction, and compares it with what a direct-drive NEMA17 can pull.

    python3 simulate.py                         # full 2440 x 1220 sheet, drives on the sheet corners
    python3 simulate.py --width 1200 --height 600
    python3 simulate.py --wing 200              # drives moved 200 mm out past the long edges
    python3 simulate.py --wing 200 --wing-x 150 # ...and 150 mm past the short edges
    python3 simulate.py --png reach.png
"""
import argparse, math
import numpy as np
import beltkin as K


def table_for(width, height, wing_y, wing_x):
    """Corner units normally sit on the sheet's own corners. A wing is a strip of
    scrap screwed under a corner so the unit sits further out: wing_y past the
    long (X) edges, wing_x past the short edges. The sheet stays at 0..width, 0..height."""
    return K.Table([(-wing_x, -wing_y), (width + wing_x, -wing_y),
                    (width + wing_x, height + wing_y), (-wing_x, height + wing_y)])


def reach_map(t, width, height, f_ext, t_min, step=20):
    xs = np.arange(step / 2, width, step)
    ys = np.arange(step / 2, height, step)
    Z = np.full((len(ys), len(xs)), np.nan)
    for a, y in enumerate(ys):
        for b, x in enumerate(xs):
            try:
                w = K.worst_tension(t, (x, y), f_ext, t_min, n_dir=12)
            except ValueError:
                w = None
            if w is not None:
                Z[a, b] = w
    return xs, ys, Z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=float, default=2440)
    ap.add_argument("--height", type=float, default=1220)
    ap.add_argument("--wing", type=float, default=0, help="drives this far out past the long edges, mm")
    ap.add_argument("--wing-x", type=float, default=0, help="drives this far out past the short edges, mm")
    ap.add_argument("--force", type=float, default=15, help="sideways load on the sled, N (cut + friction)")
    ap.add_argument("--limit", type=float, default=35, help="belt tension a motor can hold, N")
    ap.add_argument("--tmin", type=float, default=3, help="slackest a belt is allowed to get, N")
    ap.add_argument("--png")
    a = ap.parse_args()
    t = table_for(a.width, a.height, a.wing, a.wing_x)
    xs, ys, Z = reach_map(t, a.width, a.height, a.force, a.tmin)
    ok = Z <= a.limit
    print(f"sheet {a.width:.0f} x {a.height:.0f}, wings {a.wing:.0f} / {a.wing_x:.0f}, load {a.force:.0f} N, motor limit {a.limit:.0f} N")
    print(f"usable share of the sheet: {100 * ok.mean():.0f}%")
    mid_x, mid_y = len(xs) // 2, len(ys) // 2
    def margin(vals, coords):
        good = np.where(vals)[0]
        return coords[good[0]] if len(good) else float('nan')
    print(f"margin at the middle of a long edge : {margin(ok[:, mid_x], ys):.0f} mm")
    print(f"margin at the middle of a short edge: {margin(ok[mid_y, :], xs):.0f} mm")
    step = max(1, len(xs) // 60)
    print("map (# usable, . too weak):")
    for row in ok[::-2]:
        print("  " + "".join("#" if v else "." for v in row[::step]))
    if a.png:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(11, 5.5), dpi=110)
        im = ax.pcolormesh(xs, ys, np.clip(Z, 0, 2 * a.limit), cmap="RdYlGn_r", vmin=0, vmax=2 * a.limit, shading="nearest")
        ax.contour(xs, ys, Z, levels=[a.limit], colors="k", linewidths=1.5)
        ax.set_aspect("equal"); ax.set_xlabel("X mm"); ax.set_ylabel("Y mm")
        ax.set_title(f"Belt tension needed to hold {a.force:.0f} N (black line = motor limit {a.limit:.0f} N)")
        fig.colorbar(im, label="N per belt run"); fig.tight_layout(); fig.savefig(a.png)


if __name__ == "__main__":
    main()
