"""All printed parts for the belt CNC, as functions returning solids.

Each part is modelled in the position it has on the machine ("assembly frame").
PRINT_ORIENT at the bottom says how each one is turned for printing.
"""
import math
from csg import (box, cyl, cyl_x, cyl_y, prism, rounded_box, rounded_rect_pts, hexprism, union, hull)
import geometry as G

T = G.PLATE_T
HEX_POCKET = 3.8          # depth of the pocket that traps an M5 hex head


# =============================================================================
# CORNER DRIVE UNIT  (bracket-local frame: sheet corner at origin, sheet in +x +y,
#                     sheet top at z = 0)
# =============================================================================
def corner_bracket():
    px, py = G.P_LOCAL
    fx, fy = G.F_LOCAL
    kx, ky = G.K_LOCAL
    ft, fd, tp = G.FENCE_T, G.FENCE_DEPTH, G.TOP_PLATE

    # plate that hangs outside the corner and carries the motor
    # (webs run along both fences so the outrigger is not hanging off the corner alone)
    outrigger = prism([(-62, -54), (14, -54), (14, -30), (45, -6), (45, 0), (0, 0), (0, 45), (-6, 45), (-62, 2)], 0, T)
    # triangle that sits on top of the sheet
    top = prism([(0, 0), (tp, 0), (tp, 18), (18, tp), (0, tp)], 0, T)
    # fence: two walls that register against the two edges of the corner
    fence = union(box(-ft, 0, -ft, tp, -fd, T), box(-ft, tp, -ft, 0, -fd, T))
    rx, ry = G.REEL_LOCAL
    reel_plate = prism(rounded_rect_pts(-10, rx + 17, ry - 17, -30, 5), 0, T)      # carries the reel motor
    plug_tab = box(-8, 28, ry - 21, ry - 17, -34, T)                              # panel for the GX16 socket
    body = union(outrigger, top, fence, reel_plate, plug_tab)

    cuts = []
    # motor: centre boss hole, four M3 with counterbores so the heads sit flush
    cuts.append(cyl(px, py, -1, T + 1, 11.15))
    h = G.NEMA17["hole_pitch"] / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(cyl(px + sx * h, py + sy * h, -1, T + 1, G.CLEAR_M3 / 2))
            cuts.append(cyl(px + sx * h, py + sy * h, T - 3.2, T + 1, 3.2))
    # F post (belt end) and K post (pinch bearing): M5 hex bolts pushed up from below
    for (x, y) in ((fx, fy), (kx, ky)):
        cuts.append(cyl(x, y, -1, T + 1, G.CLEAR_M5 / 2))
        cuts.append(hexprism(x, y, -1, HEX_POCKET, G.HEX_M5_AF))
    # M6 bolts (wing nuts into T-nuts in the board), or wood screws with washers
    for (x, y) in ((24, 24), (62, 9), (9, 62)):
        cuts.append(cyl(x, y, -1, T + 1, 3.25))
    # reel motor (N20): gearbox face sits in a pocket under the plate, shaft comes up through
    n = G.N20
    cuts.append(box(rx - n["w"] / 2 - 0.2, rx + n["w"] / 2 + 0.2, ry - n["d"] / 2 - 0.2, ry + n["d"] / 2 + 0.2, -1, G.N20_POCKET))
    cuts.append(cyl(rx, ry, -1, T + 1, 2.6))
    for sx in (-1, 1):
        cuts.append(cyl(rx + sx * 13, ry, -1, T + 1, G.PILOT_M3 / 2))
    cuts.append(cyl_y(ry - 22, ry - 16, 10, -18, 8.1))                            # 16 mm socket hole
    return body - union(*cuts)


def n20_cup():
    """Holds the reel motor up against the underside of the bracket."""
    n = G.N20
    depth = n["body_len"] - G.N20_POCKET
    cup = union(box(-n["w"] / 2 - 2.5, n["w"] / 2 + 2.5, -n["d"] / 2 - 2.5, n["d"] / 2 + 2.5, -depth - 2, 0),
                rounded_box(-17, 17, -6, 6, -3, 0, 3))
    cup -= box(-n["w"] / 2 - 0.2, n["w"] / 2 + 0.2, -n["d"] / 2 - 0.2, n["d"] / 2 + 0.2, -depth, 1)
    cup -= box(-3, 3, -n["d"] / 2 - 3, n["d"] / 2 + 3, -depth - 3, -depth + 6)      # wire slot
    for sx in (-1, 1):
        cup -= cyl(sx * 13, 0, -4, 1, G.CLEAR_M3 / 2)
    return cup.translate((G.REEL_LOCAL[0], G.REEL_LOCAL[1], 0))


REEL_Z0 = 12.5      # underside of the reel's lower flange above the sheet surface


def reel_body():
    """Top flange, hub and drive boss in one piece. The hub has a slot for the belt end."""
    c = G.REEL_CHANNEL
    hub_z0, hub_z1 = REEL_Z0 + 2, REEL_Z0 + 2 + c
    body = union(cyl(0, 0, hub_z1, hub_z1 + 2, G.REEL_FLANGE_R), cyl(0, 0, hub_z0, hub_z1, G.REEL_HUB_R),
                 cyl(0, 0, T + 0.5, hub_z0, 6))
    n = G.N20
    d_bore = cyl(0, 0, 0, hub_z0, n["shaft_d"] / 2 + 0.1, seg=32) ^ box(-3, n["shaft_flat"] - n["shaft_d"] / 2 + 0.05, -3, 3, 0, hub_z0)
    body -= d_bore
    body -= union(box(7, 16, -1.1, 1.1, hub_z0, hub_z1 + 3), cyl(7, 0, hub_z0, hub_z1 + 3, 3.2, seg=32))   # belt-end slot
    for k in range(3):
        a = math.radians(90 + 120 * k)
        body -= cyl(10.5 * math.cos(a), 10.5 * math.sin(a), hub_z0 - 1, hub_z0 + 6, G.PILOT_M3 / 2, seg=24)
    return body.translate((G.REEL_LOCAL[0], G.REEL_LOCAL[1], 0))


def reel_flange():
    """Lower flange, screwed to the hub with three M3 screws."""
    f = cyl(0, 0, REEL_Z0, REEL_Z0 + 2, G.REEL_FLANGE_R) - cyl(0, 0, REEL_Z0 - 1, REEL_Z0 + 3, 6.4)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        f -= cyl(10.5 * math.cos(a), 10.5 * math.sin(a), REEL_Z0 - 1, REEL_Z0 + 3, G.CLEAR_M3 / 2, seg=24)
    return f.translate((G.REEL_LOCAL[0], G.REEL_LOCAL[1], 0))


def f_spacer():      # fixed riser under the belt-end sleeve
    return cyl(0, 0, 0, 8, 6) - cyl(0, 0, -1, 9, G.CLEAR_M5 / 2)


def f_sleeve():      # the zip-tied belt loop turns on this
    return cyl(0, 0, 0, 7.6, 5) - cyl(0, 0, -1, 9, 2.85)


def k_spacer():      # lifts the 625 pinch bearing to belt height; lip touches the inner race only
    return union(cyl(0, 0, 0, 9, 5), cyl(0, 0, 9, 9.5, 3.7)) - cyl(0, 0, -1, 11, G.CLEAR_M5 / 2)


def riser_shim():    # goes under a bracket when the workpiece sits on top of the base board
    tp = G.TOP_PLATE
    s = prism([(0, 0), (tp, 0), (tp, 18), (18, tp), (0, tp)], 0, 6)
    for (x, y) in ((24, 24), (62, 9), (9, 62)):
        s -= cyl(x, y, -1, 7, 3.25)
    return s


def measuring_cap():
    """Drops on the M5 thread sticking out of an F post. The flat face is on the axis."""
    c = cyl(0, 0, 0, 14, 10) - cyl(0, 0, -1, 9, 2.8)
    return c - box(0, 11, -11, 11, 10, 15)


# =============================================================================
# SLED  (sled frame: bit axis at x=y=0, sheet surface at z = 0)
# =============================================================================
def sled_base():
    s, o = G.SLED_SIZE / 2, G.IDLER_OFFSET
    outline = rounded_rect_pts(-s, s, -s, s, 20)
    inset = rounded_rect_pts(-s + 1, s - 1, -s + 1, s - 1, 19)
    # 1 mm chamfer round the underside so it rides over small steps
    plate = union(hull(prism(inset, 0, 0.02), prism(outline, 1, 1.02)), prism(outline, 1, T))
    adds, cuts = [], []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * o, sy * o
            adds.append(cyl(x, y, T, G.BELT_Z - G.IDLER_H / 2, 7))            # idler riser
            cuts.append(cyl(x, y, -1, 30, G.CLEAR_M5 / 2))
            cuts.append(cyl(x, y, -0.01, 3.0, 5.4, 2.4))                       # M5 countersink
        adds.append(cyl(sx * G.ROD_X, 0, T, 22, 11))                           # rod socket
        cuts.append(cyl(sx * G.ROD_X, 0, 2, 30, G.ROD_D / 2 + 0.1))
        cuts.append(cyl_x(sx * G.ROD_X, sx * (G.ROD_X + 13), 0, 15, G.PILOT_M3 / 2)
                    if sx > 0 else cyl_x(-(G.ROD_X + 13), -G.ROD_X, 0, 15, G.PILOT_M3 / 2))
        cuts.append(cyl(sx * 24, -96, -1, T + 1, G.PILOT_M3 / 2))             # dust shoe screws
    cuts.append(cyl(0, 0, -1, T + 1, G.BIT_HOLE_D / 2))
    return union(plate, *adds) - union(*cuts)


def z_carriage():
    """Clamp ring for a 65 mm body, riding on two rods, lifted by the lead screw.
    Modelled with its underside at z = 0."""
    H = G.CARRIAGE_H
    ro, ri = 41.5, G.ROUTER_D / 2 + 0.2
    rx, sy = G.ROD_X, G.SCREW_Y
    adds = [cyl(0, 0, 0, H, ro)]
    for sx in (-1, 1):
        adds.append(cyl(sx * rx, 0, 0, H, 11.5))                               # bearing housing
        adds.append(box(min(sx * 38, sx * 50), max(sx * 38, sx * 50), -9, 9, 0, H))
        adds.append(box(min(sx * 1.5, sx * 11.5), max(sx * 1.5, sx * 11.5), -58, -38, 0, H))  # clamp ear
        # gusset between ring and nut tab
        adds.append(_yz_wedge(12 if sx > 0 else -15, 3))
    adds.append(hull(box(-15, 15, 36, sy, 0, 8), cyl(0, sy, 0, 8, 15)))        # lead-screw nut tab
    body = union(*adds)

    cuts = [cyl(0, 0, -1, H + 1, ri), box(-1.5, 1.5, -60, -30, -1, H + 1)]
    for sx in (-1, 1):
        cuts.append(cyl(sx * rx, 0, 1, H + 1, G.LM8UU["D"] / 2 + 0.1))         # two LM8UU stacked
        cuts.append(cyl(sx * rx, 0, -1, 2, 5))
        for z in (12, 38):                                                      # bearing pinch screws
            cuts.append(cyl_x(sx * rx, sx * (rx + 13), 0, z, G.PILOT_M3 / 2) if sx > 0
                        else cyl_x(-(rx + 13), -rx, 0, z, G.PILOT_M3 / 2))
    for z in (12.5, 37.5):                                                      # clamp bolts
        cuts.append(cyl_x(-13, 13, -50, z, G.CLEAR_M5 / 2))
        cuts.append(hexprism(0, 0, 0, 4.5, G.HEX_M5_AF, 30).rotate((0, 90, 0)).translate((-12, -50, z)))
    t = G.T8_NUT
    cuts.append(cyl(0, sy, -1, 9, t["body_d"] / 2 + 0.3))
    for i in range(4):
        a = math.radians(45 + 90 * i)
        cuts.append(cyl(t["hole_pcd"] / 2 * math.cos(a), sy + t["hole_pcd"] / 2 * math.sin(a), -1, 9, 1.75))
    return body - union(*cuts)


def _yz_wedge(x0, thick):
    """Triangular rib in the y-z plane, from the ring wall down to the nut tab."""
    pts = [(38.0, 8.0), (38.0, 30.0), (60.0, 8.0)]            # (y, z)
    w = prism(pts, 0, thick)                                   # extruded along +z, profile in x-y
    # map profile x->y, y->z, extrusion z->x
    return w.transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])


def z_bridge():
    """Ties the rod tops together and carries the Z motor. Underside at z = 0."""
    Tb = G.BRIDGE_T
    rx, sy = G.ROD_X, G.SCREW_Y
    body = union(box(rx - 11, rx + 11, -11, 90, 0, Tb), box(-rx - 11, -rx + 11, -11, 90, 0, Tb),
                 box(-rx - 11, rx + 11, 42, 90, 0, Tb),
                 box(-rx - 11, -rx + 11, 12, 15, -22, 0))                       # limit-switch tab
    cuts = [box(-22, 22, 41, 86, -1, Tb - 5)]                                   # coupler pocket
    cuts.append(cyl(0, sy, -1, Tb + 1, 11.3))
    h = G.NEMA17["hole_pitch"] / 2
    for sx in (-1, 1):
        for s2 in (-1, 1):
            cuts.append(cyl(sx * h, sy + s2 * h, -1, Tb + 1, G.CLEAR_M3 / 2))
        cuts.append(cyl(sx * rx, 0, -1, Tb - 2, G.ROD_D / 2 + 0.1))
        cuts.append(cyl_x(sx * rx, sx * (rx + 13), 0, 6, G.PILOT_M3 / 2) if sx > 0
                    else cyl_x(-(rx + 13), -rx, 0, 6, G.PILOT_M3 / 2))
    for x in (-rx - 4.75, -rx + 4.75):                                          # microswitch, 9.5 mm pitch
        cuts.append(cyl_y(11, 16, x, -14, 1.05, seg=24))
    return body - union(*cuts)


def dust_shoe():
    """Low duct under the carriage, rising to a vertical hose spigot at the front.
    Sits on the sled base: its underside is at z = T in the sled frame."""
    outer = union(box(-19, 19, -62, 24, 0, 21), box(-19, 19, -108, -62, 0, 40),
                  cyl(0, -85, 40, 70, 16.75, 16.0),
                  box(19, 30, -101, -91, 0, 3), box(-30, -19, -101, -91, 0, 3))
    inner = union(box(-17, 17, -64, 22, -1, 19), box(-17, 17, -106, -62, -1, 38),
                  cyl(0, -85, 30, 71, 13.5), cyl(0, 0, 10, 22, 16))
    part = outer - inner
    for sx in (-1, 1):
        part -= cyl(sx * 24, -96, -1, 4, G.CLEAR_M3 / 2)
    return part.translate((0, 0, T))


# =============================================================================
# TOOL CADDIES  (clamp in the carriage ring in place of the router)
# =============================================================================
LIP_Z = 55.0      # underside of the seating lip; 50 mm of ring plus 5 mm below it


def _caddy_blank(total_h):
    r = G.ROUTER_D / 2 - 0.1
    return union(cyl(0, 0, 0, total_h, r), cyl(0, 0, LIP_Z, LIP_Z + 3, 36))


def pen_caddy_body():
    b = _caddy_blank(LIP_Z + 3) - box(-17.3, 17.3, -15.3, 15.3, -1, 60)
    for sx in (-1, 1):                                    # pegs for an optional rubber band
        b += cyl(sx * 29, 0, LIP_Z + 3, LIP_Z + 9, 2.2, seg=24)
    return b


def pen_slider():
    """Floats up and down in the body. Two thumb screws press the pen into a V."""
    L = 95.0
    s = box(-17, 17, -15, 15, 0, L)
    s -= cyl(-3, 0, -1, L + 1, 10.3)
    s -= prism([(-14.8, 0), (-3, 11.8), (-3, -11.8)], -1, L + 1)      # V seat
    for z in (65, 85):
        s -= cyl_x(5, 18, 0, z, G.PILOT_M5 / 2)
    return s


def thumb_knob():
    k = cyl(0, 0, 0, 8, 11, seg=12) - cyl(0, 0, -1, 9, G.CLEAR_M5 / 2)
    return k - hexprism(0, 0, 4, 9, G.HEX_M5_AF)


def laser_caddy():
    """Square pocket for a 33 to 40 mm diode module, clamped by two thumb screws
    above the carriage ring. Slide the module up or down to set focus."""
    H = 80.0
    c = _caddy_blank(H) - box(-20.75, 20.75, -20.75, 20.75, -1, H + 1)
    for y in (-10, 10):
        c -= cyl_x(18, 34, y, 69, G.PILOT_M5 / 2)
    return c


def laser_shim():
    return box(0, 41, 0, 70, 0, 4.2)


# =============================================================================
# ELECTRONICS
# =============================================================================
def electronics_tray():
    w, d, h, t = 150.0, 110.0, 40.0, 2.5
    tray = rounded_box(-t, w + t, -t, d + t, 0, h, 4) - rounded_box(0, w, 0, d, t, h + 1, 2)
    for (x, y) in ((4, 4), (w - 4, 4), (4, d - 4), (w - 4, d - 4)):
        tray += cyl(x, y, t, h, 4, seg=24) - cyl(x, y, h - 12, h + 1, G.PILOT_M3 / 2, seg=24)
    for x in (25, 55, 85, 115):                           # cable notches, one long side
        tray -= box(x - 6, x + 6, -t - 1, 1, h - 14, h + 1)
    tray -= box(w - 1, w + t + 1, 40, 70, h - 16, h + 1)   # USB / power notch
    return tray


def electronics_lid():
    w, d, t = 150.0, 110.0, 2.5
    lid = rounded_box(-t, w + t, -t, d + t, 0, 2.5, 4)
    for (x, y) in ((4, 4), (w - 4, 4), (4, d - 4), (w - 4, d - 4)):
        lid -= cyl(x, y, -1, 4, G.CLEAR_M3 / 2, seg=24)
    for i in range(8):                                     # vent slots
        lid -= box(30 + i * 12, 34 + i * 12, 25, 85, -1, 4)
    return lid


# =============================================================================
# name -> (function, quantity, print transform, note)
# print transform: list of ("rot", (rx,ry,rz)) applied to the assembly-frame solid
# =============================================================================
PARTS = {
    "corner_bracket":   (corner_bracket,   4, (180, 0, 0), "top face down on the bed, fence walls pointing up"),
    "reel_body":        (reel_body,        4, (180, 0, 0), "big flange down on the bed"),
    "reel_flange":      (reel_flange,      4, (0, 0, 0),   "flat"),
    "n20_cup":          (n20_cup,          4, (180, 0, 0), "open end down"),
    "f_spacer":         (f_spacer,         4, (0, 0, 0),   ""),
    "f_sleeve":         (f_sleeve,         4, (0, 0, 0),   ""),
    "k_spacer":         (k_spacer,         4, (0, 0, 0),   "lip up"),
    "riser_shim":       (riser_shim,       0, (0, 0, 0),   "optional, print as needed"),
    "measuring_cap":    (measuring_cap,    2, (0, 0, 0),   ""),
    "sled_base":        (sled_base,        1, (0, 0, 0),   "underside on the bed"),
    "z_carriage":       (z_carriage,       1, (0, 0, 0),   "ring axis vertical"),
    "z_bridge":         (z_bridge,         1, (180, 0, 0), "top face down on the bed"),
    "dust_shoe":        (dust_shoe,        1, (0, 0, 0),   "upright, bridges 34 mm"),
    "pen_caddy_body":   (pen_caddy_body,   1, (0, 0, 0),   ""),
    "pen_slider":       (pen_slider,       1, (0, 0, 0),   "upright"),
    "thumb_knob":       (thumb_knob,       4, (0, 0, 0),   "hex pocket up"),
    "laser_caddy":      (laser_caddy,      1, (0, 0, 0),   ""),
    "laser_shim":       (laser_shim,       0, (0, 0, 0),   "optional, for modules under 40 mm"),
    "electronics_tray": (electronics_tray, 1, (0, 0, 0),   ""),
    "electronics_lid":  (electronics_lid,  1, (0, 0, 0),   ""),
}
