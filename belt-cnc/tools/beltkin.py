"""Belt geometry for the four-corner belt CNC (reference model, numpy only).

The firmware (firmware/BeltKin.h) is a line-for-line port of metered() and
forward(); tools/gen_test_vectors.py checks the two against each other.

Frames
------
Table frame: origin at the SOUTH-WEST corner of the base sheet, +X along the
south edge towards the south-east corner, +Y towards the north-west corner.
Corners are numbered 0=SW, 1=SE, 2=NE, 3=NW (counter-clockwise).

Each corner unit has a drive pulley P and a belt-end post F. The belt runs
pulley -> idler on the sled -> back to the post, so it is a 2:1 tackle: the
"metered" length is roughly twice the pulley-to-idler distance.
"""
import math
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cad"))
import geometry as G  # noqa: E402

RP = G.PULLEY_PITCH_R
RI = G.IDLER_PITCH_R
P_LOCAL = np.array(G.P_LOCAL)
F_LOCAL = np.array(G.F_LOCAL)
PINCH = math.radians(G.PINCH_ANGLE_DEG)
O = G.IDLER_OFFSET
IDLER_B = np.array([[-O, -O], [O, -O], [O, O], [-O, O]])   # sled idler for corner i, relative to the bit
TWO_PI = 2 * math.pi


def rot(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s], [s, c]])


class Table:
    """Where the four corner units are. Build with Table.from_corners() or
    Table.from_measurements()."""

    def __init__(self, corners):
        self.C = np.asarray(corners, dtype=float)            # sheet corners, 4x2
        self.theta = np.zeros(4)
        for i in range(4):
            nxt, prv = self.C[(i + 1) % 4] - self.C[i], self.C[(i - 1) % 4] - self.C[i]
            bis = nxt / np.linalg.norm(nxt) + prv / np.linalg.norm(prv)
            # a bracket's local +x+y diagonal points along the corner bisector
            self.theta[i] = math.atan2(bis[1], bis[0]) - math.pi / 4
        self.P = np.array([self.C[i] + rot(self.theta[i]) @ P_LOCAL for i in range(4)])
        self.F = np.array([self.C[i] + rot(self.theta[i]) @ F_LOCAL for i in range(4)])
        self.pinch = np.array([PINCH + self.theta[i] for i in range(4)])
        self.centre = self.C.mean(axis=0)

    @classmethod
    def rectangle(cls, width, height):
        return cls([(0, 0), (width, 0), (width, height), (0, height)])

    @classmethod
    def from_config(cls, path):
        """Read the corner geometry back out of a FluidNC config written by table_config.py."""
        import re
        text = open(path).read()
        val = lambda key: float(re.search(rf"^\s*{key}:\s*([-\d.]+)", text, re.M).group(1))
        t = cls.__new__(cls)
        names = ["sw", "se", "ne", "nw"]
        t.P = np.array([[val(n + "_pulley_x"), val(n + "_pulley_y")] for n in names])
        t.F = np.array([[val(n + "_post_x"), val(n + "_post_y")] for n in names])
        t.pinch = np.array([math.radians(val(n + "_pinch_deg")) for n in names])
        t.centre = np.array([val("home_x"), val("home_y")])
        t.theta = t.pinch - PINCH
        t.C = np.array([t.P[i] - rot(t.theta[i]) @ P_LOCAL for i in range(4)])
        return t

    def post_distances(self):
        """(S, E, N, W, D) between the belt-end posts; D is NW post to SE post."""
        F = self.F
        d = lambda a, b: float(np.linalg.norm(F[a] - F[b]))
        return d(0, 1), d(1, 2), d(2, 3), d(3, 0), d(3, 1)

    @classmethod
    def from_measurements(cls, S, E, N, W, D):
        """Solve the sheet shape from the five tape measurements between posts."""
        target = np.array([S, E, N, W, D], dtype=float)
        # start from a rectangle of about the right size
        x = np.array([S - 60.0, 0.0, W - 60.0, S - 60.0, W - 60.0])   # a, b, c, d, e

        def corners(p):
            a, b, c, d, e = p
            return [(0, 0), (a, 0), (d, e), (b, c)]

        def resid(p):
            return np.array(cls(corners(p)).post_distances()) - target

        for _ in range(40):
            r = resid(x)
            J = np.zeros((5, 5))
            for k in range(5):
                dx = np.zeros(5); dx[k] = 1e-4
                J[:, k] = (resid(x + dx) - r) / 1e-4
            step = np.linalg.solve(J, -r)
            x = x + step
            if np.abs(step).max() < 1e-9:
                break
        if np.abs(resid(x)).max() > 1e-3:
            raise ValueError("measurements do not describe a possible table - check them")
        return cls(corners(x))


def metered(table, i, bit, dz=0.0):
    """Belt length between the pinch point of corner i and its end post, mm."""
    P, F, I = table.P[i], table.F[i], np.asarray(bit, float) + IDLER_B[i]
    d = I - P
    dist = math.hypot(d[0], d[1])
    s = RP + RI
    if dist <= s + 1.0:
        raise ValueError("sled idler is on top of the corner pulley")
    t1 = math.sqrt(dist * dist - s * s)
    alpha = math.atan2(d[1], d[0]) - math.atan2(s, t1)        # direction of run 1 (pulley -> idler)
    wrap_p = (table.pinch[i] - (alpha + math.pi / 2)) % TWO_PI
    e = F - I
    t2 = math.sqrt(e[0] * e[0] + e[1] * e[1] - RI * RI)
    ang_v = math.atan2(e[1], e[0]) + math.atan2(RI, t2)       # direction of run 2 (idler -> post)
    wrap_i = (ang_v - alpha) % TWO_PI
    return RP * wrap_p + math.hypot(t1, dz) + RI * wrap_i + math.hypot(t2, dz)


def lengths(table, bit, dz=0.0):
    return np.array([metered(table, i, bit, dz) for i in range(4)])


def run_dirs(table, i, bit):
    """Unit vectors of the two belt runs pulling on the sled idler of corner i."""
    P, F, I = table.P[i], table.F[i], np.asarray(bit, float) + IDLER_B[i]
    d = I - P
    s = RP + RI
    t1 = math.sqrt(d @ d - s * s)
    alpha = math.atan2(d[1], d[0]) - math.atan2(s, t1)
    e = F - I
    t2 = math.sqrt(e @ e - RI * RI)
    ang_v = math.atan2(e[1], e[0]) + math.atan2(RI, t2)
    return np.array([-math.cos(alpha), -math.sin(alpha)]), np.array([math.cos(ang_v), math.sin(ang_v)])


def jacobian(table, bit, dz=0.0, h=1e-3):
    J = np.zeros((4, 2))
    for k in range(2):
        d = np.zeros(2); d[k] = h
        J[:, k] = (lengths(table, np.asarray(bit) + d, dz) - lengths(table, np.asarray(bit) - d, dz)) / (2 * h)
    return J


def forward(table, L, guess=None, dz=0.0, weights=None):
    """Least-squares bit position for four belt lengths (they over-determine it)."""
    x = np.array(table.centre if guess is None else guess, dtype=float)
    w = np.ones(4) if weights is None else np.asarray(weights)
    for _ in range(25):
        r = (lengths(table, x, dz) - L) * w
        J = jacobian(table, x, dz) * w[:, None]
        step = np.linalg.lstsq(J, -r, rcond=None)[0]
        x += step
        if np.abs(step).max() < 1e-7:
            break
    return x


def tensions_for(table, bit, force, t_min=5.0):
    """Smallest belt tensions (N per run, each >= t_min) that balance an external
    force on the sled. Returns None if no set of tensions can."""
    A = np.zeros((2, 4))
    for i in range(4):
        u, v = run_dirs(table, i, bit)
        A[:, i] = u + v                       # both runs carry the same tension
    b = -np.asarray(force, float)
    best = None
    for i in range(4):
        for j in range(i + 1, 4):
            free = [k for k in range(4) if k not in (i, j)]
            rhs = b - A[:, [i, j]] @ np.array([t_min, t_min])
            M = A[:, free]
            if abs(np.linalg.det(M)) < 1e-9:
                continue
            tf = np.linalg.solve(M, rhs)
            if (tf >= t_min - 1e-9).all():
                t = np.full(4, t_min); t[free] = tf
                if best is None or t.max() < best.max():
                    best = t
    return best


def worst_tension(table, bit, f_ext, t_min=5.0, n_dir=16):
    worst = 0.0
    for k in range(n_dir):
        a = TWO_PI * k / n_dir
        t = tensions_for(table, bit, (f_ext * math.cos(a), f_ext * math.sin(a)), t_min)
        if t is None:
            return None
        worst = max(worst, t.max())
    return worst
