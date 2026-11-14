"""Work out how far off the table measurements are, from a set of test dots.

1. Run the G-code from make_test_pattern.py with the SAME --table and --inset.
2. Measure these six distances between the dots, in mm:
       bottom  (south-west dot to south-east dot)      top   (north-west to north-east)
       left    (south-west to north-west)              right (south-east to north-east)
       diag1   (south-west to north-east)              diag2 (north-west to south-east)
3. Run, giving the five post measurements you used for table_config.py first:

    python3 calibrate.py --posts 2500.4 1280.8 2500.4 1280.8 2789.6 \\
                         --table 2440 1220 --inset 300 \\
                         --dots 1840.0 1841.5 620.0 619.0 1942.0 1943.5

It prints corrected post measurements to feed back into table_config.py and a
belt scale correction for steps_per_mm.
"""
import argparse, math
import numpy as np
import beltkin as K
from make_test_pattern import points

PAIRS = [(0, 1), (3, 2), (0, 3), (1, 2), (0, 2), (3, 1)]


def predicted(believed, true_posts, scale, pts):
    """Where the dots really land if the machine believes `believed` but the
    posts are really at `true_posts` and the belts are `scale` times too long."""
    true = K.Table.from_measurements(*true_posts)
    home_b, home_t = believed.centre, true.centre
    zero_b, zero_t = K.lengths(believed, home_b), K.lengths(true, home_t)
    out = []
    for p in pts:
        paid = (K.lengths(believed, p) - zero_b) * scale        # belt the motors actually move
        out.append(K.forward(true, zero_t + paid, guess=np.array(p) - home_b + home_t))
    out = np.array(out)
    return [float(np.linalg.norm(out[a] - out[b])) for a, b in PAIRS]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--posts", nargs=5, type=float, required=True, metavar=("S", "E", "N", "W", "D"))
    ap.add_argument("--table", nargs=2, type=float, default=[2440, 1220])
    ap.add_argument("--inset", type=float, default=300)
    ap.add_argument("--dots", nargs=6, type=float, required=True, metavar=("BOTTOM", "TOP", "LEFT", "RIGHT", "DIAG1", "DIAG2"))
    ap.add_argument("--tape-error", type=float, default=2.0, help="how far out you think each post measurement could be, mm")
    a = ap.parse_args()

    believed = K.Table.from_measurements(*a.posts)
    pts = points(a.table[0], a.table[1], a.inset)
    nominal = [math.dist(pts[i], pts[j]) for i, j in PAIRS]
    meas = np.array(a.dots)
    print("distance   wanted   measured   error")
    for n, w, m in zip(("bottom", "top", "left", "right", "diag1", "diag2"), nominal, meas):
        print(f"  {n:7s} {w:8.1f} {m:9.1f} {m - w:+7.1f}")

    # unknowns: corrections to S E N W D (mm) and belt scale error (parts per thousand).
    # Six numbers from six measurements is fragile, so pull gently towards "no change".
    x = np.zeros(6)
    prior = np.array([a.tape_error] * 5 + [3.0])
    sigma = 0.5                                              # how well a dot spacing can be measured, mm

    def resid(v):
        posts = np.array(a.posts) + v[:5]
        r = (np.array(predicted(believed, posts, 1 + v[5] / 1000.0, pts)) - meas) / sigma
        return np.concatenate([r, v / prior])

    lam = 1e-2
    cost = float(resid(x) @ resid(x))
    for _ in range(40):
        r = resid(x)
        J = np.zeros((len(r), 6))
        for k in range(6):
            d = np.zeros(6); d[k] = 1e-3
            J[:, k] = (resid(x + d) - r) / 1e-3
        step = np.linalg.solve(J.T @ J + lam * np.eye(6), -J.T @ r)
        new = float(resid(x + step) @ resid(x + step))
        if new < cost:
            x, cost, lam = x + step, new, lam / 3
        else:
            lam *= 5
        if np.abs(step).max() < 1e-5:
            break

    left = np.array(predicted(believed, np.array(a.posts) + x[:5], 1 + x[5] / 1000.0, pts)) - meas
    print(f"\nunexplained error after fitting: worst {np.abs(left).max():.2f} mm")
    if np.abs(left).max() > 1.5:
        print("!! The fit is poor. Re-measure the dots, and check no belt went slack while marking.")
    print("\ncorrected post measurements for table_config.py:")
    print("  " + " ".join(f"{v:.1f}" for v in np.array(a.posts) + x[:5]))
    print("  (changes: " + " ".join(f"{n} {v:+.1f}" for n, v in zip("SENWD", x[:5])) + " mm)")
    print(f"\nbelt scale: belts are moving {x[5]:+.2f} parts per thousand too far.")
    print(f"  multiply steps_per_mm on the x, y, a and b axes by {1 / (1 + x[5] / 1000.0):.5f}  (80.000 becomes {80 / (1 + x[5] / 1000.0):.3f})")


if __name__ == "__main__":
    main()
