"""Tiny solid-modelling helpers on top of manifold3d."""
import math
import struct
import numpy as np
from manifold3d import Manifold, CrossSection

SEG = 96


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def cyl(x, y, z0, z1, r, r_top=None, seg=SEG):
    """Vertical cylinder (or cone if r_top given)."""
    return Manifold.cylinder(z1 - z0, r, r if r_top is None else r_top, seg).translate((x, y, z0))


def cyl_x(x0, x1, y, z, r, seg=48):
    return Manifold.cylinder(x1 - x0, r, r, seg).rotate((0, 90, 0)).translate((x0, y, z))


def cyl_y(y0, y1, x, z, r, seg=48):
    return Manifold.cylinder(y1 - y0, r, r, seg).rotate((-90, 0, 0)).translate((x, y0, z))


def prism(points, z0, z1):
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]))
    if area < 0:                       # manifold wants counter-clockwise outlines
        points = points[::-1]
    return Manifold.extrude(CrossSection([points]), z1 - z0).translate((0, 0, z0))


def rounded_rect_pts(x0, x1, y0, y1, r, n=12):
    pts = []
    for cx, cy, a0 in ((x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def rounded_box(x0, x1, y0, y1, z0, z1, r):
    return prism(rounded_rect_pts(x0, x1, y0, y1, r), z0, z1)


def hexprism(x, y, z0, z1, af, rot_deg=0):
    R = af / math.sqrt(3)
    pts = [(x + R * math.cos(math.radians(rot_deg + 60 * i)), y + R * math.sin(math.radians(rot_deg + 60 * i)))
           for i in range(6)]
    return prism(pts, z0, z1)


def union(*parts):
    return Manifold.batch_boolean(list(parts), __import__("manifold3d").OpType.Add)


def hull(*parts):
    return Manifold.batch_hull(list(parts))


def mesh_arrays(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float64)
    f = np.asarray(mesh.tri_verts).astype(np.int64)
    return v, f


def write_stl(m, path):
    v, f = mesh_arrays(m)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1)
    ln[ln == 0] = 1
    n = n / ln[:, None]
    with open(path, "wb") as fh:
        fh.write(b"belt-cnc".ljust(80, b" "))
        fh.write(struct.pack("<I", len(f)))
        rec = np.zeros(len(f), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        rec["n"] = n
        rec["v"] = tri
        fh.write(rec.tobytes())


def info(m):
    bb = m.bounding_box()
    return dict(size=(bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]), volume_cm3=m.volume() / 1000.0,
                genus=m.genus(), parts=len(m.decompose()))
