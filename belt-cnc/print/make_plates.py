"""Lay the printed parts out as build plates for a 300 x 300mm bed (Artillery Sidewinder X1).

    python3 make_plates.py

Writes plates/*.3mf (open in OrcaSlicer: each part stays a separate object) and
plates/*.stl. Plates are split into STRONG and STANDARD so one set of slicer
settings suits everything on a plate.
"""
import os, sys, zipfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cad"))
from csg import mesh_arrays
import parts as P

BED = 300.0
GAP = 8.0

# plate name -> (profile, [(part, copies)])
PLATES = {
    "01_strong_corner_brackets_a": ("strong", [("corner_bracket", 2)]),
    "02_strong_corner_brackets_b": ("strong", [("corner_bracket", 2)]),
    "03_strong_carriage_bridge":   ("strong", [("z_carriage", 1), ("z_bridge", 1)]),
    "04_standard_sled_base":       ("standard", [("sled_base", 1), ("f_spacer", 5), ("f_sleeve", 5), ("k_spacer", 5), ("measuring_cap", 2)]),
    "05_standard_reels":           ("standard", [("reel_body", 4)]),
    "06_standard_flanges_cups":    ("standard", [("reel_flange", 4), ("n20_cup", 4)]),
    "07_standard_tools":           ("standard", [("pen_caddy_body", 1), ("pen_slider", 1), ("thumb_knob", 4), ("dust_shoe", 1), ("laser_caddy", 1), ("laser_shim", 2)]),
    "08_standard_tray":            ("standard", [("electronics_tray", 1)]),
    "09_standard_lid":             ("standard", [("electronics_lid", 1)]),
}


def placed(name):
    fn, qty, rot, note = P.PARTS[name]
    m = fn().rotate(rot)
    v, f = mesh_arrays(m)
    v = v - v.min(0)
    return v, f


def shelf_pack(items):
    """Simple shelf packing, biggest first. items: list of (name, v, f). Returns list of (name, v, f) moved into place."""
    items = sorted(items, key=lambda t: -(t[1][:, 1].max()))
    out, x, y, shelf_h = [], 0.0, 0.0, 0.0
    for name, v, f in items:
        w, d = v[:, 0].max(), v[:, 1].max()
        if w > d and d <= BED and w > BED:                 # never needed, kept for safety
            v = v[:, [1, 0, 2]]; w, d = d, w
        if x + w > BED:
            x, y, shelf_h = 0.0, y + shelf_h + GAP, 0.0
        if y + d > BED:
            raise SystemExit(f"plate overflow at {name}")
        out.append((name, v + np.array([x, y, 0]), f))
        x += w + GAP
        shelf_h = max(shelf_h, d)
    # centre the whole layout on the bed
    allv = np.vstack([v for _, v, _ in out])
    shift = np.array([(BED - allv[:, 0].max()) / 2, (BED - allv[:, 1].max()) / 2, 0])
    return [(n, v + shift, f) for n, v, f in out]


def write_3mf(path, objects):
    verts_xml = []
    res, build = [], []
    for i, (name, v, f) in enumerate(objects, start=1):
        vx = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in v)
        tx = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
        res.append(f'<object id="{i}" name="{name}" type="model"><mesh><vertices>{vx}</vertices><triangles>{tx}</triangles></mesh></object>')
        build.append(f'<item objectid="{i}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources>{"".join(res)}</resources><build>{"".join(build)}</build></model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels); z.writestr("3D/3dmodel.model", model)


def write_stl(path, objects):
    import struct
    tris = np.vstack([v[f] for _, v, f in objects]).astype("<f4")
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]); ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1; n = (n / ln[:, None]).astype("<f4")
    rec = np.zeros(len(tris), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]); rec["n"] = n; rec["v"] = tris
    with open(path, "wb") as fh:
        fh.write(b"belt-cnc plate".ljust(80, b" ")); fh.write(struct.pack("<I", len(tris))); fh.write(rec.tobytes())


def main():
    out = os.path.join(HERE, "plates")
    os.makedirs(out, exist_ok=True)
    cache = {}
    for plate, (profile, items) in PLATES.items():
        objs = []
        for name, qty in items:
            if name not in cache:
                cache[name] = placed(name)
            v, f = cache[name]
            for k in range(qty):
                objs.append((f"{name}_{k + 1}" if qty > 1 else name, v, f))
        laid = shelf_pack(objs)
        write_3mf(os.path.join(out, plate + ".3mf"), laid)
        write_stl(os.path.join(out, plate + ".stl"), laid)
        allv = np.vstack([v for _, v, _ in laid])
        print(f"{plate:32s} {profile:8s} {len(laid):2d} parts  {np.ptp(allv[:, 0]):.0f} x {np.ptp(allv[:, 1]):.0f} x {allv[:, 2].max():.0f} mm")


if __name__ == "__main__":
    main()
