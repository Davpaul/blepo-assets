"""Describe every picture in the manual as a 3D scene, for render.js to draw.

    python3 scenes.py <output folder>

Each scene lists parts (already-fitted ones in grey, the ones being added in
colour), how far each new part is pulled out along its fitting direction (the
"exploded" position), and the labels.
"""
import base64, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cad"))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
sys.path.insert(0, HERE)
from csg import box, cyl, union, mesh_arrays, prism, rounded_box
import parts as P
import geometry as G
import hw as H
import beltkin as K

T = G.PLATE_T
COL = {  # fill, edge
    "old":   ((0.80, 0.83, 0.86), (0.33, 0.36, 0.41)),
    "new":   ((0.36, 0.64, 0.93), (0.07, 0.16, 0.30)),
    "new2":  ((0.98, 0.62, 0.30), (0.35, 0.16, 0.03)),
    "hw":    ((1.00, 0.80, 0.25), (0.35, 0.24, 0.02)),
    "steel": ((0.80, 0.82, 0.85), (0.30, 0.32, 0.36)),
    "dark":  ((0.36, 0.38, 0.43), (0.10, 0.11, 0.13)),
    "wood":  ((0.93, 0.85, 0.68), (0.55, 0.45, 0.28)),
    "belt":  ((0.16, 0.16, 0.18), (0.0, 0.0, 0.0)),
    "green": ((0.30, 0.68, 0.42), (0.05, 0.25, 0.10)),
    "red":   ((0.88, 0.32, 0.28), (0.35, 0.05, 0.03)),
}


class Scene:
    all = []

    def __init__(self, name, view=(-125, 30), size=(1500, 1000), pad=(0.1, 0.1, 0.1, 0.1), focus=None):
        self.d = dict(name=name, view=list(view), width=size[0], height=size[1], pad=list(pad), parts=[], guides=[], labels=[], arrows=[], scale=size[0] / 1500)
        if focus:
            self.d["focus"] = list(focus)
        Scene.all.append(self)

    def add(self, mesh, kind="old", at=(0, 0, 0), explode=None, label=None, lab=(70, -50), alpha=1.0, guide=True):
        v, f = mesh_arrays(mesh)
        fill, edge = COL[kind]
        pos = np.array(at, float) + (np.array(explode, float) if explode is not None else 0)
        self.d["parts"].append(dict(v=base64.b64encode(v.astype("<f4").tobytes()).decode(), f=base64.b64encode(f.astype("<u4").tobytes()).decode(),
                                    color=list(fill), edge=list(edge), pos=[float(x) for x in pos], alpha=alpha))
        centre = (v.min(0) + v.max(0)) / 2
        if explode is not None and guide:
            self.d["guides"].append(dict(a=[float(x) for x in centre + np.array(at, float)], b=[float(x) for x in centre + pos]))
        if label:
            self.label(label, centre + pos, *lab)
        return self

    def label(self, text, at, dx=70, dy=-50, **kw):
        self.d["labels"].append(dict(text=text, at=[float(x) for x in at], dx=dx, dy=dy, **kw))
        return self

    def arrow(self, a, b):
        self.d["arrows"].append(dict(a=[float(x) for x in a], b=[float(x) for x in b]))
        return self

    def write(self, folder):
        json.dump(self.d, open(os.path.join(folder, self.d["name"] + ".json"), "w"))


# ----------------------------------------------------------------------------- shared pieces
PX, PY = G.P_LOCAL; FX, FY = G.F_LOCAL; KX, KY = G.K_LOCAL; RX, RY = G.REEL_LOCAL
M5HEX = dict(d=5, af=8, head_h=3.5)


def f_bolt():  return H.hex_bolt(5, 30, 8, 3.5).translate((FX, FY, 0.3))
def k_bolt():  return H.hex_bolt(5, 25, 8, 3.5).translate((KX, KY, 0.3))
def c_motor(): return H.nema17().translate((PX, PY, 0))
def c_pulley(): return H.pulley().translate((PX, PY, T + 0.5))
def c_bearing(): return H.bearing(16, 5, 5).translate((KX, KY, 15.5))
def c_n20():   return H.n20().translate((RX, RY, G.N20_POCKET))
def c_reel():  return union(P.reel_body(), P.reel_flange())


def motor_screws():
    h = 15.5
    return [H.cap_screw(3, 8, 5.5, 3).translate((PX + sx * h, PY + sy * h, T - 3.2)) for sx in (-1, 1) for sy in (-1, 1)]


def f_stack():
    return [P.f_spacer().translate((FX, FY, T)), P.f_sleeve().translate((FX, FY, T + 8)),
            H.washer(10, 5.3).translate((FX, FY, T + 15.6)), H.nut(8, 5, True).translate((FX, FY, T + 16.6))]


def k_stack():
    return [P.k_spacer().translate((KX, KY, T)), c_bearing(), H.nut(8, 5, True).translate((KX, KY, 20.5))]


def corner_unit(upto=99):
    """List of (mesh, kind) for a corner unit built up to a given stage."""
    items = [(P.corner_bracket(), "old")]
    if upto >= 1: items += [(f_bolt(), "old"), (k_bolt(), "old")]
    if upto >= 2: items += [(c_motor(), "old")] + [(s, "old") for s in motor_screws()]
    if upto >= 3: items += [(m, "old") for m in f_stack()]
    if upto >= 4: items += [(m, "old") for m in k_stack()]
    if upto >= 5: items += [(c_pulley(), "old")]
    if upto >= 7: items += [(c_n20(), "old"), (P.n20_cup(), "old")]
    if upto >= 9: items += [(c_reel(), "old")]
    return items


def corner_solid():
    return union(*[m for m, _ in corner_unit()])


# ----------------------------------------------------------------------------- corner unit steps
def corner_scenes():
    s = Scene("c01_bolts", view=(-118, -30), pad=(0.2, 0.22, 0.08, 0.1))
    s.add(P.corner_bracket(), "new")
    s.add(f_bolt(), "hw", explode=(0, 0, -55), label="M5 x 30 bolt\n(the hole on its own)", lab=(-70, 40))
    s.add(k_bolt(), "hw", explode=(0, 0, -55), label="M5 x 25 bolt\n(beside the motor hole)", lab=(80, 50))
    s.label("underside of the bracket", (-30, -60, 0), -120, -90)

    s = Scene("c02_motor", view=(-125, 22), pad=(0.2, 0.2, 0.12, 0.08))
    for m, k in corner_unit(1): s.add(m, k)
    s.add(c_motor(), "dark", explode=(0, 0, -62), label="stepper motor\nshaft up, lead facing out", lab=(-90, 60))
    for i, sc in enumerate(motor_screws()):
        s.add(sc, "hw", explode=(0, 0, 42), label="4 x M3 x 8" if i == 0 else None, lab=(-90, -60))

    s = Scene("c03_post", view=(-125, 18), pad=(0.22, 0.26, 0.1, 0.06), focus=(FX - 45, FX + 60, FY - 45, FY + 45, -10, 110))
    for m, k in corner_unit(2): s.add(m, k)
    names = ["f_spacer (fat)", "f_sleeve (must spin)", "M5 washer", "M5 nyloc nut"]
    kinds = ["new", "new2", "hw", "hw"]
    for i, m in enumerate(f_stack()):
        s.add(m, kinds[i], explode=(0, 0, 20 + i * 17), label=names[i], lab=(90, -8), guide=(i == 3))

    s = Scene("c04_pinch", view=(-125, 18), pad=(0.22, 0.26, 0.1, 0.06), focus=(KX - 50, KX + 55, KY - 45, KY + 45, -10, 100))
    for m, k in corner_unit(3): s.add(m, k)
    names = ["k_spacer (lip up)", "625 bearing", "M5 nyloc nut, no washer"]
    kinds = ["new", "steel", "hw"]
    for i, m in enumerate(k_stack()):
        s.add(m, kinds[i], explode=(0, 0, 20 + i * 20), label=names[i], lab=(90, -8), guide=(i == 2))

    s = Scene("c05_pulley", view=(-125, 18), pad=(0.22, 0.26, 0.1, 0.06), focus=(PX - 50, PX + 55, PY - 45, PY + 45, -10, 90))
    for m, k in corner_unit(4): s.add(m, k)
    s.add(c_pulley(), "steel", explode=(0, 0, 45), label="20-tooth pulley\ngrub screws at the bottom", lab=(90, -10))
    s.label("gap: one business card", (PX + 8, PY - 4, T + 0.3), 120, 70)

    s = Scene("c06_gap", view=(-90, 90), size=(1500, 900), pad=(0.12, 0.12, 0.1, 0.1), focus=(PX - 30, PX + 45, PY - 32, PY + 20, 0, 30))
    for m, k in corner_unit(4): s.add(m, k)
    s.add(c_pulley(), "steel", alpha=0.35)                       # see-through, so the belt under its top rim shows
    a = math.radians(G.PINCH_ANGLE_DEG)
    r = G.PULLEY_PITCH_R + 0.1
    arc = [(PX + r * math.cos(t), PY + r * math.sin(t)) for t in np.linspace(math.radians(150), a, 24)]
    tail = [(arc[-1][0] - math.sin(a) * d, arc[-1][1] + math.cos(a) * d) for d in (8, 18, 30)]
    lead = [(arc[0][0] + 0.5 * d, arc[0][1] + 0.87 * d) for d in (30, 18, 8)]
    s.add(H.ribbon(lead + arc + tail, 15, 21), "belt")
    s.label("scrap of belt, teeth against the pulley", (arc[4][0], arc[4][1], 21), -60, -120)
    s.label("pinch bearing: belt slides through\nwith light drag, and cannot lift\noff the teeth", (KX + 4, KY - 2, 21), 90, 30)
    s.label("pulley", (PX + 3, PY + 3, 23), 110, -80)

    s = Scene("c07_reelmotor", view=(-60, -24), pad=(0.2, 0.24, 0.08, 0.1))
    for m, k in corner_unit(5): s.add(m, k)
    s.add(c_n20(), "dark", explode=(0, 0, -50), label="N20 motor\nshaft up through the hole", lab=(90, -20))
    s.add(P.n20_cup(), "new", explode=(0, 0, -105), label="n20_cup", lab=(90, 0))
    for i, sx in enumerate((-1, 1)):
        s.add(H.cap_screw(3, 12, 5.6, 2.4, pointing_down=False).translate((RX + sx * 13, RY, -3)), "hw", explode=(0, 0, -150),
              label="2 x M3 x 12" if i == 1 else None, lab=(90, 20))

    s = Scene("c08_reel", view=(-60, -22), size=(1500, 900), pad=(0.2, 0.24, 0.1, 0.12))
    s.add(P.reel_body(), "new", label="reel_body", lab=(110, -60))
    s.add(P.reel_flange(), "new2", explode=(0, 0, -40), label="reel_flange (plain disc)", lab=(110, 10))
    for k in range(3):
        an = math.radians(90 + 120 * k)
        s.add(H.cap_screw(3, 12, 5.6, 2.4, pointing_down=False).translate((RX + 10.5 * math.cos(an), RY + 10.5 * math.sin(an), P.REEL_Z0)), "hw",
              explode=(0, 0, -78), label="3 x M3 x 12" if k == 0 else None, lab=(110, 30))

    s = Scene("c09_reelon", view=(-60, 24), pad=(0.16, 0.2, 0.14, 0.06))
    for m, k in corner_unit(7): s.add(m, k)
    s.add(c_reel(), "new", explode=(0, 0, 60), label="reel: push onto the D-shaped shaft,\nflat to flat", lab=(60, -90))

    s = Scene("c10_breakout", view=(-78, 8), pad=(0.14, 0.24, 0.1, 0.1))
    for m, k in corner_unit(9): s.add(m, k)
    bo = H.breakout().rotate((90, 0, 0)).translate((10, RY - 21, -22))
    s.add(bo, "green", explode=(0, -55, 0), label="network breakout board\non the panel with the grid of holes,\nsocket pointing down", lab=(60, 80))

    s = Scene("c11_done", view=(-125, 28), pad=(0.08, 0.08, 0.08, 0.08))
    for m, k in corner_unit(9):
        kind = "new" if m is not None and k == "old" else k
        s.add(m, "old")
    s.d["parts"][0]["color"], s.d["parts"][0]["edge"] = list(COL["new"][0]), list(COL["new"][1])
    s.add(H.breakout().rotate((90, 0, 0)).translate((10, RY - 21, -22)), "green")
    s.label("drive pulley", (PX, PY, 24), -90, -110); s.label("pinch bearing", (KX, KY, 22), -130, 60)
    s.label("belt-end post", (FX, FY, 28), -110, -70); s.label("reel", (RX + 20, RY, 26), 110, -80)
    s.label("fence: pushes against\nthe corner of the sheet", (40, -6, 0), 120, 60)


# ----------------------------------------------------------------------------- sled steps
O = G.IDLER_OFFSET; RODX = G.ROD_X; SY = G.SCREW_Y; CZ = 45.0


def sled_idlers():   return [H.idler().translate((sx * O, sy * O, 13.5)) for sx in (-1, 1) for sy in (-1, 1)]
def sled_bolts():    return [H.csk_bolt(5, 30, 9.2, 2.8).translate((sx * O, sy * O, 0)) for sx in (-1, 1) for sy in (-1, 1)]
def sled_nuts():     return [H.nut(8, 5, True).translate((sx * O, sy * O, 22.5)) for sx in (-1, 1) for sy in (-1, 1)]
def sled_rods():     return [H.rod().translate((sx * RODX, 0, 2)) for sx in (-1, 1)]
def car_bearings():  return [H.lm8uu().translate((sx * RODX, 0, z)) for sx in (-1, 1) for z in (1, 25)]
def car_nut():       return H.t8_nut().translate((0, SY, 11.5))


def carriage_full(z=CZ):
    return union(P.z_carriage(), *car_bearings(), car_nut()).translate((0, 0, z))


def bridge_motor():  return H.nema17().rotate((180, 0, 0)).translate((0, SY, G.BRIDGE_T))
def bridge_full():
    return union(P.z_bridge(), bridge_motor(), H.coupler().translate((0, SY, -17)), H.lead_screw().translate((0, SY, -120)),
                 H.microswitch().translate((-RODX, 12, -14))).translate((0, 0, G.BRIDGE_Z))


def sled(upto=99, cz=CZ):
    items = [(P.sled_base(), "old")]
    if upto >= 1: items += [(m, "old") for m in sled_bolts() + sled_idlers() + sled_nuts()]
    if upto >= 3: items += [(m, "old") for m in sled_rods()]
    if upto >= 4: items += [(carriage_full(cz), "old")]
    if upto >= 6: items += [(bridge_full(), "old")]
    if upto >= 7: items += [(P.dust_shoe(), "old")]
    if upto >= 8: items += [(H.router(cz + 8), "old")]
    return items


def sled_scenes():
    s = Scene("s01_idlers", view=(-62, 12), size=(1500, 900), pad=(0.12, 0.2, 0.08, 0.08))
    s.add(P.sled_base(), "new")
    for i, m in enumerate(sled_bolts()):
        s.add(m, "hw", explode=(0, 0, -55), label="4 x M5 x 30 countersunk,\nup from underneath" if i == 1 else None, lab=(100, 40))
    for i, m in enumerate(sled_idlers()):
        s.add(m, "steel", explode=(0, 0, 45), label="4 x smooth idler" if i == 3 else None, lab=(110, -10))
    for i, m in enumerate(sled_nuts()):
        s.add(m, "hw", explode=(0, 0, 75), label="4 x M5 nyloc nut" if i == 3 else None, lab=(110, -30), guide=False)
    s.label("front of the sled\n(two small screw holes)", (0, -100, T), -150, 70)

    s = Scene("s02_carriage", view=(-58, 24), pad=(0.16, 0.24, 0.1, 0.08))
    s.add(P.z_carriage(), "new")
    for i, m in enumerate(car_bearings()):
        s.add(m, "steel", explode=(0, 0, 70 + (0 if i % 2 == 0 else 32)), label="4 x LM8UU bearing,\ntwo in each side tube" if i == 3 else None, lab=(100, -30), guide=(i % 2 == 1))
    s.add(car_nut(), "hw", explode=(0, 0, 55), label="brass nut, flange on top", lab=(-110, -70))
    for i in range(4):
        an = math.radians(45 + 90 * i)
        s.add(H.cap_screw(3, 10, 5.5, 3).translate((8 * math.cos(an), SY + 8 * math.sin(an), 11.5)), "hw", explode=(0, 0, 95), guide=False,
              label="4 x M3 x 10 + nuts" if i == 0 else None, lab=(-120, -50))
    s.label("clamp slot = front", (0, -58, 25), -130, 60)
    s.label("M3 x 12 in each side hole\nnips the bearings. Just snug.", (RODX + 11, 0, 25), 90, 70)

    s = Scene("s03_rods", view=(-62, 16), pad=(0.14, 0.22, 0.1, 0.08))
    for m, k in sled(1): s.add(m, k)
    for i, m in enumerate(sled_rods()):
        s.add(m, "steel", explode=(0, 0, 80), label="2 x 8mm rod, pushed right down" if i == 1 else None, lab=(90, -60))
    s.label("M3 x 12 in the side of\neach socket locks the rod", (RODX + 11, 0, 15), 100, 60)

    s = Scene("s04_carriage_on", view=(-62, 16), pad=(0.16, 0.22, 0.08, 0.08))
    for m, k in sled(3): s.add(m, k)
    s.add(carriage_full(CZ), "new", explode=(0, 0, 140), label="carriage: clamp slot to the front,\nbrass nut to the back", lab=(80, -70))

    s = Scene("s05_bridge", view=(-58, 20), pad=(0.2, 0.24, 0.08, 0.08))
    s.add(P.z_bridge(), "new")
    s.add(bridge_motor(), "dark", explode=(0, 0, 55), label="Z motor on top,\nshaft pointing down", lab=(110, -40))
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        s.add(H.cap_screw(3, 8, 5.5, 3, pointing_down=False).translate((sx * 15.5, SY + sy * 15.5, G.BRIDGE_T - 5)), "hw", explode=(0, 0, -45),
              label="4 x M3 x 8,\nfrom underneath" if i == 1 else None, lab=(120, 30), guide=(i < 2))
    s.add(H.coupler().translate((0, SY, -17)), "steel", explode=(0, 0, -75), label="coupler", lab=(-110, 10))
    s.add(H.lead_screw().translate((0, SY, -120)), "steel", explode=(0, 0, -105), label="lead screw, cut to 115mm", lab=(-110, 30))
    s.add(H.microswitch().translate((-RODX, 12, -14)), "red", explode=(0, -45, 0), label="microswitch,\nlever down,\n2 x M2 screws", lab=(-120, 30))

    s = Scene("s06_bridge_on", view=(-62, 14), size=(1500, 1150), pad=(0.16, 0.22, 0.06, 0.06))
    for m, k in sled(4): s.add(m, k)
    s.add(bridge_full(), "new", explode=(0, 0, 85), label="bridge: turn the lead screw by hand\nso it winds into the brass nut\nas the bridge comes down", lab=(70, -80))

    s = Scene("s07_shoe", view=(-62, 18), pad=(0.16, 0.22, 0.08, 0.08))
    for m, k in sled(6): s.add(m, k)
    s.add(P.dust_shoe(), "new", explode=(0, -95, 20), label="dust_shoe slides in from the front\n2 x M3 x 12 through its tabs", lab=(-60, 110))

    s = Scene("s08_router", view=(-62, 14), size=(1500, 1250), pad=(0.2, 0.24, 0.05, 0.05))
    for m, k in sled(7): s.add(m, k)
    s.add(H.router(CZ + 8), "red", explode=(0, 0, 150), label="65mm trim router", lab=(110, -30))
    for i, z in enumerate((12.5, 37.5)):
        s.add(H.hex_bolt(5, 30, 8, 3.5).rotate((0, -90, 0)).translate((15, -50, CZ + z)), "hw", explode=(45, 0, 0),
              label="2 x M5 x 30 clamp bolts" if i == 1 else None, lab=(100, 20))
        s.add(H.nut(8, 4).rotate((0, 90, 0)).translate((-12, -50, CZ + z)), "hw", explode=(-40, 0, 0),
              label="2 x M5 nuts in the\nsix-sided pockets" if i == 0 else None, lab=(-110, 40))

    s = Scene("s09_done", view=(-58, 18), size=(1500, 1250), pad=(0.2, 0.2, 0.05, 0.05))
    for m, k in sled(8): s.add(m, k)
    s.d["parts"][0]["color"], s.d["parts"][0]["edge"] = list(COL["new"][0]), list(COL["new"][1])
    s.add(H.breakout().translate((46, 66, G.BRIDGE_Z + G.BRIDGE_T)), "green", label="breakout board\n(fitted in the wiring section)", lab=(110, -30))
    s.label("Z motor", (0, SY, 194), 110, -60); s.label("carriage", (-RODX, 0, CZ + 30), -130, 0)
    s.label("dust hose here", (0, -85, 76), -130, -30); s.label("idlers: the belts hook round these", (O, -O, 18), 120, 80)


# ----------------------------------------------------------------------------- table, belts, tools
def rot_z(mesh, deg, origin=(0, 0)):
    return mesh.translate((-origin[0], -origin[1], 0)).rotate((0, 0, deg)).translate(origin)


def belt_path(table, i, bit, with_reel=True):
    """Belt centreline for corner i: reel -> round the pulley -> sled idler -> end post."""
    Pc, F, I = table.P[i], table.F[i], np.asarray(bit, float) + K.IDLER_B[i]
    d = I - Pc; s = K.RP + K.RI
    t1 = math.sqrt(d @ d - s * s); alpha = math.atan2(d[1], d[0]) - math.atan2(s, t1)
    a0, a1 = alpha + math.pi / 2, table.pinch[i]
    while a1 < a0: a1 += 2 * math.pi
    arc_p = [Pc + K.RP * np.array([math.cos(a), math.sin(a)]) for a in np.linspace(a1, a0, 28)]
    e = F - I; t2 = math.sqrt(e @ e - K.RI ** 2); av = math.atan2(e[1], e[0]) + math.atan2(K.RI, t2)
    b0, b1 = alpha - math.pi / 2, av - math.pi / 2
    while b1 < b0: b1 += 2 * math.pi
    arc_i = [I + K.RI * np.array([math.cos(a), math.sin(a)]) for a in np.linspace(b0, b1, 28)]
    pts = arc_p + arc_i + [F]
    if with_reel:
        R = table.C[i] + K.rot(table.theta[i]) @ np.array(G.REEL_LOCAL)
        v = R - arc_p[0]; n = np.array([v[1], -v[0]]) / np.linalg.norm(v)
        wound = [R + 36 * np.array([math.cos(a), math.sin(a)]) for a in np.linspace(math.atan2(n[1], n[0]) - 4.6, math.atan2(n[1], n[0]), 40)]
        pts = wound + pts
    return [tuple(p) for p in pts]


def table_scenes():
    stud = lambda x, y: union(H.t_nut().translate((x, y, -18)), H.hex_bolt(6, 40, 10, 4).translate((x, y, -23.5)))
    holes = ((24, 24), (62, 9), (9, 62))
    s = Scene("t01_mount", view=(-125, 26), pad=(0.16, 0.22, 0.1, 0.06))
    board = box(0, 230, 0, 230, -18, 0)
    for (x, y) in holes:
        board -= cyl(x, y, -19, 1, 3.3)
    s.add(board, "wood")
    for i, (x, y) in enumerate(holes):
        s.add(stud(x, y), "hw", explode=(0, 0, -60), label="T-nut hammered in from below,\nM6 x 40 bolt screwed up through it" if i == 1 else None, lab=(110, 70))
    s.add(corner_solid(), "new", explode=(-0, -0, 75), label="corner unit: push both fence walls\nhard against the corner", lab=(-60, -110))
    for i, (x, y) in enumerate(holes):
        s.add(P.hold_down_knob().translate((x, y, T)), "new2", explode=(0, 0, 150), label="hold_down_knob,\nM6 nut pressed in underneath" if i == 1 else None, lab=(110, -30))

    # whole machine
    W, Hh = 2440.0, 1220.0
    table = K.Table.rectangle(W, Hh)
    bit = (980.0, 560.0)
    s = Scene("t02_overview", view=(-70, 38), size=(1700, 1000), pad=(0.07, 0.07, 0.12, 0.08))
    s.add(box(0, W, 0, Hh, -18, 0), "wood")
    unit = corner_solid()
    names = ["SW corner", "SE corner", "NE corner", "NW corner"]
    labs = [(-60, 90), (80, 80), (90, -70), (-80, -80)]
    for i in range(4):
        m = unit.rotate((0, 0, math.degrees(table.theta[i]))).translate((table.C[i][0], table.C[i][1], 0))
        s.add(m, "new", label=names[i], lab=labs[i])
        s.add(H.ribbon(belt_path(table, i, bit, with_reel=False), 14, 22, t=5), "belt")
    sl = union(*[m for m, _ in sled(8)]).translate((bit[0], bit[1], 0))
    s.add(sl, "new2", label="sled with router", lab=(90, -90))
    s.label("SOUTH edge: you stand here", (W / 2, -40, 0), 0, 90, bold=True)
    s.label("+X", (W * 0.82, -40, 0), 30, 60); s.label("+Y", (-40, Hh * 0.75, 0), -90, -10)

    s = Scene("t03_measure", view=(-125, 24), pad=(0.2, 0.24, 0.12, 0.06), focus=(FX - 60, FX + 80, FY - 60, FY + 60, -10, 90))
    for m, k in corner_unit(9): s.add(m, k)
    s.add(P.measuring_cap().translate((FX, FY, T + 23)), "new", explode=(0, 0, 40), label="measuring_cap drops on the\nthread above the nut", lab=(90, -30))
    s.label("hook the tape on this flat face.\nIt sits exactly on the post's centre.", (FX, FY, T + 77), -110, -60)

    # belt path at a corner, from above
    t = K.Table.rectangle(600, 600)
    bitc = (190.0, 150.0)
    s = Scene("b01_path", view=(-90, 90), size=(1500, 1150), pad=(0.1, 0.1, 0.08, 0.08), focus=(-150, 260, -150, 220, 0, 30))
    s.add(box(0, 400, 0, 400, -18, 0), "wood")
    for m, k in corner_unit(9): s.add(m, "old", alpha=1.0)
    s.d["parts"][-1]["alpha"] = 0.45                                # see the belt inside the reel
    path = belt_path(t, 0, bitc)
    s.add(H.ribbon(path, 15, 21, t=1.8), "belt")
    I = np.array(bitc) + K.IDLER_B[0]
    s.add(H.idler().translate((I[0], I[1], 13.5)), "steel")
    s.label("1  loop over the belt-end post", (FX, FY, 22), -40, -110)
    s.label("2  out round the sled idler,\nsmooth side against the idler", (I[0] + 6, I[1] + 6, 22), 60, -90)
    s.label("3  back to the pulley on the\npost side, teeth against it", (PX - 5, PY + 4, 22), -150, 40)
    s.label("4  between pulley\nand pinch bearing", (KX - 4, KY - 6, 22), -90, 100)
    s.label("5  onto the reel", (RX + 30, RY - 20, 26), 80, 70)
    s.label("sheet", (300, 300, 0), 0, 0)

    # belts on the sled, from above
    t = K.Table.rectangle(700, 700)
    c = (350.0, 350.0)
    s = Scene("b02_sled", view=(-90, 90), size=(1500, 1150), pad=(0.1, 0.1, 0.08, 0.08), focus=(c[0] - 170, c[0] + 170, c[1] - 150, c[1] + 150, 0, 30))
    s.add(P.sled_base().translate((c[0], c[1], 0)), "old")
    for m in sled_idlers() + sled_nuts():
        s.add(m.translate((c[0], c[1], 0)), "steel")
    for i in range(4):
        s.add(H.ribbon(belt_path(t, i, c, with_reel=False), 15, 21, t=2.2), "belt")
    s.label("each belt makes a U-turn\nround its own idler", (c[0] + O + 8, c[1] + O + 8, 22), 110, -80)
    s.label("to the SW corner", (c[0] - 150, c[1] - 135, 20), -20, 60); s.label("to the SE corner", (c[0] + 150, c[1] - 135, 20), 20, 60)
    s.label("bit", (c[0], c[1], 6), 60, 50)

    # pen caddy
    ring = P.z_carriage()
    s = Scene("p01_pen", view=(-55, 16), size=(1500, 1300), pad=(0.2, 0.26, 0.04, 0.04))
    s.add(ring, "old")
    s.add(P.pen_caddy_body().translate((0, 0, -5)), "new", explode=(0, 0, 80), label="pen_caddy_body\nclamps in the ring, lip on top", lab=(110, -10))
    s.add(P.pen_slider().translate((0, 0, -32)), "new2", explode=(0, 0, 185), label="pen_slider\nfloats up and down", lab=(110, -30))
    s.add(H.pen().translate((-9, 0, -45)), "dark", explode=(0, 0, 300), label="pen, 6 to 20mm", lab=(100, -40))
    for i, z in enumerate((65, 85)):
        knob = union(H.hex_bolt(5, 40, 8, 3.5).rotate((0, -90, 0)), P.thumb_knob().rotate((0, 90, 0)).translate((-4, 0, 0))).translate((62, 0, -32 + z))
        s.add(knob, "hw", explode=(60, 0, 185), guide=False, label="2 x M5 x 40 with thumb_knob:\npress the pen into the V" if i == 1 else None, lab=(60, -80))

    s = Scene("p02_laser", view=(-55, 16), size=(1500, 1150), pad=(0.2, 0.26, 0.05, 0.05))
    s.add(ring, "old")
    s.add(P.laser_caddy().translate((0, 0, -5)), "new", explode=(0, 0, 80), label="laser_caddy", lab=(110, 0))
    s.add(H.laser_module().translate((-4, 0, -20)), "dark", explode=(0, 0, 200), label="laser module, 33 to 40mm square\nslide up or down to focus", lab=(100, -30))
    for i, y in enumerate((-10, 10)):
        knob = union(H.hex_bolt(5, 40, 8, 3.5).rotate((0, -90, 0)), P.thumb_knob().rotate((0, 90, 0)).translate((-4, 0, 0))).translate((62, y, 64))
        s.add(knob, "hw", explode=(55, 0, 80), guide=False, label="2 x M5 x 40 with thumb_knob" if i == 1 else None, lab=(60, 70))

    # electronics tray
    s = Scene("e01_tray", view=(-70, 32), size=(1500, 950), pad=(0.12, 0.2, 0.12, 0.06))
    s.add(P.electronics_tray(), "new")
    s.add(union(rounded_box(0, 110, 0, 84, 0, 1.6, 3), *[box(8 + i * 19, 22 + i * 19, 50, 70, 1.6, 14) for i in range(5)]).translate((100, 58, 8.5)), "green",
          explode=(0, 0, 55), label="main board on standoffs,\nfive drivers plugged in", lab=(60, -90))
    for i, x in enumerate((30, 70, 110, 150, 190)):
        s.add(H.breakout().rotate((0, 0, 0)).translate((x, 17, 2.5)), "green", explode=(0, 0, 40), guide=(i in (0, 4)),
              label="five breakout boards,\none behind each notch" if i == 0 else None, lab=(-110, -70))
    s.add(P.electronics_lid().translate((0, 0, 40)), "new2", explode=(0, 0, 105), label="lid, 4 x M3 x 12", lab=(110, -30))
    for i, n in enumerate(("X=SW", "Y=SE", "E0=NE", "E1=NW", "Z=SLED")):
        s.label(n, (30 + i * 40, -4, 30), -10 + i * 4, 110 + (i % 2) * 52, size=30)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    corner_scenes(); sled_scenes(); table_scenes()
    for s in Scene.all:
        s.write(out)
    print(len(Scene.all), "scenes written to", out)


if __name__ == "__main__":
    main()
