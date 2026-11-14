"""Build every STL into ../stl and preview images into ../renders.

    python3 build.py            # all parts
    python3 build.py sled_base  # one part
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from csg import write_stl, info, mesh_arrays, cyl, box, union
import parts as P
import geometry as G

HERE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(HERE, "..", "stl")
REN = os.path.join(HERE, "..", "renders")
BED = 300.0


def _tris(m, color, alpha):
    v, f = mesh_arrays(m)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1
    n /= ln[:, None]
    light = np.array([0.35, -0.5, 0.8]); light /= np.linalg.norm(light)
    k = 0.35 + 0.65 * np.clip(n @ light, 0, 1)
    c = np.clip(np.outer(k, np.array(color)), 0, 1)
    return tri, np.c_[c, np.full(len(c), alpha)]


def render(items, path, views=((28, -60), (28, 120), (89, -90)), title=None):
    """One merged collection, so matplotlib depth-sorts faces across all parts."""
    data = [_tris(m, col, a) for (m, col, a) in items]
    tri = np.vstack([d[0] for d in data]); col = np.vstack([d[1] for d in data])
    v = tri.reshape(-1, 3)
    lo, hi = v.min(0), v.max(0)
    c, r = (lo + hi) / 2, (hi - lo).max() / 2 * 1.05
    fig = plt.figure(figsize=(6 * len(views), 6), dpi=110)
    for i, (el, az) in enumerate(views):
        ax = fig.add_subplot(1, len(views), i + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(tri, facecolors=col, edgecolors="none"))
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(el, az); ax.set_axis_off()
    if title:
        fig.suptitle(title)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def main():
    os.makedirs(STL, exist_ok=True); os.makedirs(REN, exist_ok=True)
    only = sys.argv[1:]
    print(f"{'part':18s} {'qty':>3s}  {'print size (mm)':>22s}  {'cm3':>6s}  ok")
    for name, (fn, qty, rot, note) in P.PARTS.items():
        if only and name not in only:
            continue
        m = fn()
        pm = m.rotate(rot)
        bb = pm.bounding_box()
        pm = pm.translate((-bb[0], -bb[1], -bb[2]))
        i = info(pm)
        ok = i["parts"] == 1 and max(i["size"][:2]) <= BED and i["size"][2] <= 400
        write_stl(pm, os.path.join(STL, name + ".stl"))
        render([(pm, (0.25, 0.55, 0.85), 1.0)], os.path.join(REN, name + ".png"), title=f"{name} (as printed)")
        sz = "x".join(f"{s:.0f}" for s in i["size"])
        print(f"{name:18s} {qty:3d}  {sz:>22s}  {i['volume_cm3']:6.1f}  {'yes' if ok else 'CHECK: ' + str(i['parts']) + ' bodies'}")


if __name__ == "__main__":
    main()
