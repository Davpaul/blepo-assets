"""Draw the belt-path and layout diagrams used in BUILD.md."""
import math, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
import beltkin as K
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cad"))
import geometry as G, parts as P

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "renders")


def belt_points(t, i, bit):
    """Polyline of the belt for corner i: tail side of pulley -> round pulley -> idler -> post."""
    Pc, F, I = t.P[i], t.F[i], np.asarray(bit) + K.IDLER_B[i]
    d = I - Pc; s = K.RP + K.RI
    t1 = math.sqrt(d @ d - s * s); alpha = math.atan2(d[1], d[0]) - math.atan2(s, t1)
    a0, a1 = alpha + math.pi / 2, t.pinch[i]
    while a1 < a0: a1 += 2 * math.pi
    arc_p = [Pc + K.RP * np.array([math.cos(a), math.sin(a)]) for a in np.linspace(a1, a0, 30)]
    e = F - I; t2 = math.sqrt(e @ e - K.RI ** 2); av = math.atan2(e[1], e[0]) + math.atan2(K.RI, t2)
    b0, b1 = alpha - math.pi / 2, av - math.pi / 2
    while b1 < b0: b1 += 2 * math.pi
    arc_i = [I + K.RI * np.array([math.cos(a), math.sin(a)]) for a in np.linspace(b0, b1, 30)]
    tail_dir = np.array([-math.sin(t.pinch[i]), math.cos(t.pinch[i])])
    tail = [arc_p[0] + tail_dir * 55, arc_p[0]]
    return np.array(tail + arc_p + arc_i + [F])


def corner_diagram():
    t = K.Table.rectangle(2440, 1220)
    fig, ax = plt.subplots(figsize=(9, 7.5), dpi=120)
    ax.add_patch(Rectangle((0, 0), 200, 200, fc="#e9d8b4", ec="#b59a62"))
    ax.text(70, 95, "sheet", color="#8a7340", fontsize=13)
    ax.add_patch(Polygon([(-62, -54), (14, -54), (14, -30), (45, -6), (45, 0), (80, 0), (80, 18), (18, 80), (0, 80), (0, 45), (-6, 45), (-62, 2)],
                         fc="#9cc3ea", ec="#3b78b5", alpha=.7))
    px, py = G.P_LOCAL; fx, fy = G.F_LOCAL; kx, ky = G.K_LOCAL
    ax.add_patch(Circle((px, py), 9, fc="#c9c9c9", ec="k")); ax.add_patch(Circle((px, py), K.RP, fc="#8a8a8a", ec="k"))
    ax.add_patch(Circle((kx, ky), 8, fc="#d9d9d9", ec="k")); ax.add_patch(Circle((fx, fy), 5, fc="#e06a5a", ec="k"))
    c, (ux, uy), ang = P._tail_frame(); n = np.array([-uy, ux]); u = np.array([ux, uy])
    for v in (3.2, -3.2):
        a, b = np.array(c) + n * v - u * 9, np.array(c) + n * v + u * 9
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#e8902a", lw=7, solid_capstyle="round")
    bit = (150, 105)
    pts = belt_points(t, 0, bit)
    ax.plot(pts[:, 0], pts[:, 1], color="#111", lw=2.2)
    I = np.array(bit) + K.IDLER_B[0]
    ax.add_patch(Circle(I, 9, fc="none", ec="#555", ls="--")); ax.add_patch(Circle(I, 6, fc="#d9d9d9", ec="k"))
    ann = dict(arrowprops=dict(arrowstyle="->", color="#333"), fontsize=10.5)
    ax.annotate("drive pulley on the motor\n(belt teeth face the pulley)", (px - 6, py - 4), (-150, -62), **ann)
    ax.annotate("pinch bearing\nholds the belt on the teeth", (kx + 3, ky - 6), (-20, -92), **ann)
    ax.annotate("tail guide\nslack belt leaves here\nand drops into a bucket", (c[0] + 8, c[1] - 6), (60, -60), **ann)
    ax.annotate("belt-end post\n(loop zip-tied round the sleeve)", (fx - 3, fy + 4), (-155, 40), **ann)
    ax.annotate("idler on the sled\n(smooth back of the belt\nagainst the idler)", (I[0] + 6, I[1] + 6), (140, 150), **ann)
    ax.text(75, 15, "run 1", fontsize=10, color="#111", rotation=27)
    ax.text(40, 62, "run 2", fontsize=10, color="#111", rotation=27)
    ax.set_xlim(-165, 215); ax.set_ylim(-110, 215); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Belt path at the south-west corner, seen from above\n(the other three corners are the same, turned a quarter turn each)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "belt_path.png")); plt.close(fig)


def layout_diagram():
    t = K.Table.rectangle(2440, 1220)
    fig, ax = plt.subplots(figsize=(11, 6), dpi=120)
    ax.add_patch(Rectangle((0, 0), 2440, 1220, fc="#e9d8b4", ec="#b59a62"))
    bit = (820, 470)
    for i, name in enumerate(("SW (X driver)", "SE (Y driver)", "NE (E0 driver)", "NW (E1 driver)")):
        pts = belt_points(t, i, bit)
        ax.plot(pts[1:, 0], pts[1:, 1], color="#111", lw=1.2)
        ax.add_patch(Rectangle(t.P[i] - 45, 90, 90, fc="#9cc3ea", ec="#3b78b5"))
        off = (0, -120) if i < 2 else (0, 90)
        ax.text(t.P[i][0] + off[0], t.P[i][1] + off[1], name, ha="center", fontsize=10)
    ax.add_patch(Rectangle((bit[0] - 110, bit[1] - 110), 220, 220, fc="#f4b266", ec="#a8641a", alpha=.85))
    ax.add_patch(Circle(bit, 32, fc="#c0392b", ec="k"))
    ax.text(bit[0], bit[1] + 150, "sled", ha="center", fontsize=10)
    ax.annotate("", (700, -150), (0, -150), arrowprops=dict(arrowstyle="->")); ax.text(350, -210, "+X", ha="center")
    ax.annotate("", (-150, 500), (-150, 0), arrowprops=dict(arrowstyle="->")); ax.text(-230, 250, "+Y", va="center")
    ax.text(1220, -330, "SOUTH: you stand here", ha="center", fontsize=11)
    ax.plot([t.F[0][0], t.F[2][0]], [t.F[0][1], t.F[2][1]], ls=":", color="#777"); ax.plot([t.F[1][0], t.F[3][0]], [t.F[1][1], t.F[3][1]], ls=":", color="#777")
    ax.text(1220, 640, "centre mark\n(strings between diagonal posts cross here)", ha="center", fontsize=9, color="#555")
    ax.set_xlim(-330, 2770); ax.set_ylim(-380, 1420); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Layout seen from above")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "layout.png")); plt.close(fig)


if __name__ == "__main__":
    corner_diagram(); layout_diagram(); print("ok")
