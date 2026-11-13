"""
Twist animatronic core - parametric part library (CadQuery).

All dimensions in mm. Change the parameters in the PARAMETERS block and run
build.py to regenerate every STL.

Local "cage" frame used by every servo-holding part:
    origin  = centre of the servo's bottom face
    +z      = output shaft direction
    +x      = long axis of the servo body, the shaft sits at x = +SX
    y       = thin axis of the servo body
"""
import math
import cadquery as cq
from cadquery import Workplane as WP

# ----------------------------------------------------------------- PARAMETERS
# Standard-size servo (DS3218 / DS3235 / MG996R class). Measure yours.
SL, SW = 40.5, 20.2        # body length, width
S_CASE = 38.0              # bottom of case to top of case
EAR_Z = 27.5               # bottom of case to underside of mounting ears
EAR_T = 2.6                # ear thickness
EAR_SPAN = 54.5            # tip to tip across ears
EAR_HX, EAR_HY = 49.5 / 2, 5.0   # ear hole half-spacings
SX = 10.25                 # shaft offset from body centre along x
HORN_Z = 46.0              # bottom of case to outer face of 25T disc horn

CL = 0.3                   # clearance around servo body
TW = 4.6                   # general wall thickness
CAGE_HX, CAGE_HY = 28.0, 15.0
CAV_HX, CAV_HY = SL / 2 + CL, SW / 2 + CL
BACK0, BACK1 = -9.0, -1.0  # cage back plate (carries the idle pivot nut)
ARM_T = 5.0                # yoke arm thickness
IDLE1 = BACK0 - 1.0        # 1 mm washer between cage and idle arm
IDLE0 = IDLE1 - ARM_T
HORN1 = HORN_Z + ARM_T
YC = (IDLE0 + HORN1) / 2   # centre of a yoke along the shaft axis (=18)
HUB_R = 13.0

H_ROLL = 26.0              # roll yoke: axis to underside of web
H_PITCH = 27.0             # pitch yoke (+-30 deg)
H_TILT = 42.0              # tall pitch yoke for arm units (+-50 deg)
PITCH_UP = H_ROLL + CAGE_HY            # roll axis to pitch axis (41)
WEB4 = 6.0                 # pitch yoke top plate thickness
MNT_X, MNT_Z = 7.0, 24.0   # M4 mounting pattern on top of a pitch yoke

JAW_FWD = 65.0             # pitch axis to jaw axis
JAW_UP = 19.0              # jaw axis height in pitch-yoke frame (see head_frame)

TOOTH_N = 24
TOOTH_SEP = 1.4            # distance between tooth base planes when seated
BOSS_R = 18.0
BOSS_T = 12.0

GEAR_M, GEAR_Z = 1.5, 36   # arm piston rack and pinion
GEAR_T = 10.0
RACK_LEN = 180.0
GUIDE_LEN = 40.0
RACK_BODY = 12.0
BACKLASH = 0.15

PLY = 12.0                 # plywood deck thickness
LAZY_SUSAN_T = 8.5         # lazy susan bearing thickness


# -------------------------------------------------------------------- helpers
def box(x0, x1, y0, y1, z0, z1):
    return WP().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cylz(r, z0, z1, x=0.0, y=0.0):
    return WP().circle(r).extrude(z1 - z0).translate((x, y, z0))


def to_axis(obj, axis, at=(0, 0, 0)):
    """Re-orient an object built along +z so that +z points along `axis`."""
    rot = {
        'z': None,
        '-z': ((1, 0, 0), 180),
        'x': ((0, 1, 0), 90),
        '-x': ((0, 1, 0), -90),
        'y': ((1, 0, 0), -90),
        '-y': ((1, 0, 0), 90),
    }[axis]
    if rot:
        obj = obj.rotate((0, 0, 0), rot[0], rot[1])
    return obj.translate(at)


def cyl(axis, r, a0, a1, at):
    """Cylinder along axis from a0 to a1, `at` = point on the axis (the axis coord is ignored)."""
    p = list(at)
    i = 'xyz'.index(axis)
    p[i] = 0
    return to_axis(cylz(r, a0, a1), axis, tuple(p))


def hexz(af, z0, z1):
    return WP().polygon(6, af / math.cos(math.radians(30))).extrude(z1 - z0).translate((0, 0, z0))


def horn_cut(depth, cb=0.0, cbw=6.2, rot=0.0):
    """Slotted pattern for a 25T disc horn: 4 radial M3 slots (PCD 12-19) + centre access hole."""
    s = cylz(4.5, -0.1, depth + 0.1)
    for a in range(4):
        sl = WP().center(7.75, 0).slot2D(6.9, 3.4).extrude(depth + 0.2).translate((0, 0, -0.1))
        if cb:
            sl = sl.union(WP().center(7.75, 0).slot2D(6.9 + cbw - 3.4, cbw)
                          .extrude(cb + 0.1).translate((0, 0, depth - cb)))
        s = s.union(sl.rotate((0, 0, 0), (0, 0, 1), 90 * a + rot))
    return s


def teeth(r_in=8.0, r_out=BOSS_R, h=1.3):
    """Ring of radial locking teeth rising from z=0. Identical faces mesh every 15 deg."""
    out = None
    t7, t1 = math.tan(math.radians(7.0)), math.tan(math.radians(0.9))

    def wire(r):
        pts = [(r, -r * t7, -0.3), (r, -r * t7, 0), (r, -r * t1, h), (r, r * t1, h),
               (r, r * t7, 0), (r, r * t7, -0.3)]
        return cq.Wire.makePolygon([cq.Vector(*p) for p in pts], close=True)

    tooth = cq.Solid.makeLoft([wire(r_in), wire(r_out)], True)
    for i in range(TOOTH_N):
        t = WP().add(tooth).rotate((0, 0, 0), (0, 0, 1), 3.75 + i * 360 / TOOTH_N)
        out = t if out is None else out.union(t)
    return out


_TEETH = None


def _teeth():
    global _TEETH
    if _TEETH is None:
        _TEETH = teeth()
    return _TEETH


def tooth_boss(captive=True, t=BOSS_T):
    """Toothed mounting boss. Tooth base plane at z=0, body below. M6 through the middle."""
    return cylz(BOSS_R, -t, 0).union(_teeth())


def tooth_boss_cut(captive=True, t=BOSS_T):
    """Negative volume for tooth_boss: bolt hole and nut trap (slot opens toward +x)."""
    c = cylz(3.25, -t - 0.1, 2)
    if captive:
        c = c.union(hexz(10.4, -10.4, -5.0)).union(box(0, BOSS_R + 1, -5.2, 5.2, -10.4, -5.0))
    else:
        c = c.union(hexz(10.4, -t - 0.1, -t + 4.0))
    return c


# ------------------------------------------------------------ servo and cage
def servo():
    """Dummy servo for visualisation and collision checks."""
    s = box(-SL / 2, SL / 2, -SW / 2, SW / 2, 0, S_CASE)
    s = s.union(box(-EAR_SPAN / 2, EAR_SPAN / 2, -SW / 2, SW / 2, EAR_Z, EAR_Z + EAR_T))
    s = s.union(cylz(6.5, S_CASE, S_CASE + 3, SX, 0))
    s = s.union(cylz(10.5, S_CASE + 3, HORN_Z - 0.05, SX, 0))
    return s


def cage(back=(BACK0, BACK1), pivot=True):
    c = box(-CAGE_HX, CAGE_HX, -CAGE_HY, CAGE_HY, back[0], EAR_Z)
    c = c.cut(box(-CAV_HX, CAV_HX, -CAV_HY, CAV_HY, back[1], EAR_Z + 1))
    c = c.cut(box(-CAGE_HX - 1, CAGE_HX + 1, -CAV_HY, CAV_HY, back[1], EAR_Z - TW))
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = c.cut(cylz(2.2, EAR_Z - TW - 1, EAR_Z + 1, sx * EAR_HX, sy * EAR_HY))
    if pivot:
        c = c.cut(cylz(2.65, back[0] - 1, back[1] + 1, SX, 0))
        c = c.cut(hexz(8.3, back[1] - 5.2, back[1] + 0.1).translate((SX, 0, 0)))
    return c


def yoke(h, web_t, web_x=(-15.0, 15.0), web_z=None, horn_rot=0.0):
    """U-yoke that swings around a cage. Web sits on the +y side, `h` above the shaft axis."""
    z0, z1 = web_z if web_z else (IDLE0, HORN1)
    y = box(SX + web_x[0], SX + web_x[1], h, h + web_t, min(z0, IDLE0), max(z1, HORN1))
    for a0, a1 in ((IDLE0, IDLE1), (HORN_Z, HORN1)):
        y = y.union(cylz(HUB_R, a0, a1, SX, 0)).union(box(SX - HUB_R, SX + HUB_R, 0, h + 0.1, a0, a1))
    y = y.cut(horn_cut(ARM_T, rot=horn_rot).translate((SX, 0, HORN_Z)))
    y = y.cut(cylz(2.65, IDLE0 - 1, IDLE1 + 1, SX, 0))
    return y


# ------------------------------------------------------------ generic joints
def bracket_L():
    """G2: plate that bolts to a disc horn (or screws to the deck) + cage for the next servo."""
    c = cage()
    c = c.union(box(-40, 40, -16, -CAV_HY, BACK0, EAR_Z))
    c = c.cut(to_axis(horn_cut(16 - CAV_HY, cb=2.0), 'y', (SX, -16, YC)))
    for x in (-34, 34):
        for z in (-2, 20.5):
            c = c.cut(cyl('y', 2.3, -17, -9, (x, 0, z)))
    # corner relief: lets the yoke above swing a full +-28 deg
    c = c.cut(WP('XY').polyline([(-CAGE_HX - 1, CAGE_HY - 9), (-CAGE_HX - 1, CAGE_HY + 1),
                                 (-CAGE_HX + 9, CAGE_HY + 1)]).close().extrude(60).translate((0, 0, -15)))
    return c


# placement of the pitch servo cage (B) inside the roll yoke frame (A)
def b_in_a(obj):
    return obj.rotate((0, 0, 0), (0, 1, 0), -90).translate((SX + YC, PITCH_UP, YC - SX))


def roll_yoke():
    """G3: swings around a bracket_L cage, carries the pitch servo cage on top."""
    zb0, zb1 = YC - SX - CAGE_HX, YC - SX + CAGE_HX
    y = yoke(H_ROLL, TW, web_x=(-HUB_R, 27.0), web_z=(zb0, zb1))
    y = y.union(b_in_a(cage()))
    return y


def pitch_yoke(h=H_PITCH):
    """G4: swings around a cage, flat top with 4 captive M4 nuts for whatever goes on top."""
    y = yoke(h, WEB4)
    for dx in (-MNT_X, MNT_X):
        for dz in (-MNT_Z, MNT_Z):
            y = y.cut(cyl('y', 2.2, h - 1, h + WEB4 + 1, (SX + dx, 0, YC + dz)))
            y = y.cut(to_axis(hexz(7.2, 0, 3.4), 'y', (SX + dx, h - 0.01, YC + dz)))
    return y


def mount_holes(y0, y1, r=2.2):
    out = None
    for dx in (-MNT_X, MNT_X):
        for dz in (-MNT_Z, MNT_Z):
            c = cyl('y', r, y0, y1, (SX + dx, 0, YC + dz))
            out = c if out is None else out.union(c)
    return out


# ---------------------------------------------------------------------- head
TOP4 = H_PITCH + WEB4      # top of pitch yoke in its cage frame (33)
PLATE_T = 6.0


JAW_FLOOR = -11.0          # underside of the jaw yoke in the jaw cage frame


def c_in_b(obj):
    """Jaw servo cage frame (C) placed in the pitch cage frame (B)."""
    return obj.translate((JAW_FWD, JAW_UP, 0))


def head_frame():
    """Bolts on the neck pitch yoke. Holds the jaw servo and the fixed (upper) paddle."""
    p = box(SX - 15, SX + JAW_FWD + CAGE_HX - SX + 0.01, TOP4, TOP4 + PLATE_T, IDLE0, HORN1)
    p = p.union(box(SX + JAW_FWD + 17, SX + JAW_FWD + 60, TOP4, TOP4 + PLATE_T, YC - 24, YC + 24))
    p = p.union(c_in_b(cage()))
    p = p.cut(mount_holes(TOP4 - 1, TOP4 + 12))
    for dx in (40, 52):
        p = p.cut(cyl('y', 2.2, TOP4 - 1, TOP4 + 12, (SX + JAW_FWD + dx, 0, YC)))
    return p


def jaw_yoke():
    """Swings around the jaw servo cage, carries the moving (lower) paddle. Built in frame C."""
    y = yoke(25.0, 5.0, web_x=(0.0, 14.0), horn_rot=45)
    y = y.rotate((SX, 0, 0), (SX, 0, 1), -90)          # web now faces +x (forward)
    # relief so the arms clear the head plate when over-closed a few degrees
    wedge = (WP('XY').polyline([(SX + 8, 13.5), (SX + 31, 13.5), (SX + 31, 0)]).close()
             .extrude(80).translate((0, 0, -20)))
    y = y.cut(wedge)
    y = y.union(box(SX + 29.9, SX + 62, JAW_FLOOR, JAW_FLOOR + TW, YC - 22, YC + 22))
    y = y.cut(box(SX - 20, SX + 70, -20, JAW_FLOOR, IDLE0 - 1, HORN1 + 1))      # flat base for printing
    for dx in (40, 52):
        y = y.cut(cyl('y', 2.2, -13, -4, (SX + dx, 0, YC)))
    return y


def paddle():
    """Mouth paddle (print two). Flat: x = length, y = width, 3 mm thick."""
    p = box(0, 87, -28, 28, 0, 3).union(cylz(28, 0, 3, 87, 0))
    p = p.cut(WP().center(34, 0).slot2D(56, 4.4).extrude(5).translate((0, 0, -1)))
    for y in (-19, 19):
        p = p.cut(WP().center(88, y).slot2D(22, 3.2).extrude(5).translate((0, 0, -1)))
    return p


# ----------------------------------------------------------- bases and clamps
def servo_base():
    """Cage with a toothed boss on its side. Pan servo of each arm unit."""
    c = cage()
    c = c.union(to_axis(tooth_boss(), 'y', (0, CAGE_HY + BOSS_T, (BACK0 + EAR_Z) / 2)))
    c = c.cut(to_axis(tooth_boss_cut(True), 'y', (0, CAGE_HY + BOSS_T, (BACK0 + EAR_Z) / 2)))
    return c


def ring_ro(d):
    return d / 2 + 6.2


def boss_c(d):
    return ring_ro(d) + 14.0


def knuckle(d):
    """Pipe clamp with a toothed face. Two of them make an adjustable elbow or cross clamp."""
    ro, c = ring_ro(d), boss_c(d)
    zt = ro + 0.25
    hw = BOSS_R
    k = cyl('x', ro, -hw, hw, (0, 0, 0))
    blk = (WP('XY').polyline([(-hw, 0), (hw, 0), (hw, c + hw - 10), (hw - 10, c + hw),
                              (-hw + 10, c + hw), (-hw, c + hw - 10)]).close()
           .extrude(18).translate((0, 0, zt - 18)))
    k = k.union(blk)
    k = k.union(_teeth().translate((0, c, zt)))
    k = k.union(box(-12, 12, -ro - 14, -ro + 4, -8, 8))
    k = k.cut(cyl('x', d / 2 + 0.2, -hw - 1, hw + 1, (0, 0, 0)))
    k = k.cut(box(-hw - 1, hw + 1, -ro - 15, -(d / 2 - 2), -1, 1))
    k = k.cut(cylz(2.7, -9, 9, 0, -ro - 7))
    k = k.cut(cylz(3.25, zt - 19, zt + 3, 0, c))
    k = k.cut(cylz(1.5, -ro - 1, -d / 2 + 1, 0, 0))
    return k


NECK_DROP = -33.0          # neck_base: height of the clamp bolt in the cage frame


def neck_base(d):
    """Cage for the neck yaw servo with a drop leg, so the entry pipe sits on the centre line."""
    ro = ring_ro(d)
    yb0 = ro + 0.25 + TOOTH_SEP          # tooth base plane of this part
    zb = NECK_DROP
    c = cage()
    c = c.union(box(SX - 18, SX + 18, CAGE_HY - 0.1, yb0 + BOSS_T, BACK0, EAR_Z))
    c = c.union(box(SX - 18, SX + 18, yb0 + 4, yb0 + BOSS_T, zb, BACK0 + 0.1))
    c = c.union(to_axis(tooth_boss(), '-y', (SX, yb0, zb)))
    c = c.cut(to_axis(tooth_boss_cut(False), '-y', (SX, yb0, zb)))
    return c


def carriage(d):
    """Bolts on the lean pitch yoke and clamps the boom pipe. Built in the pitch cage frame (B)."""
    ro = ring_ro(d)
    yb = TOP4 + 7 + d / 2
    k = box(SX - 15, SX + 15, TOP4, TOP4 + 6, IDLE0, HORN1)
    k = k.union(box(SX - 30, SX + 30, TOP4, yb, YC - ro, YC + ro))
    k = k.union(cyl('x', ro, SX - 30, SX + 30, (0, yb, YC)))
    k = k.union(box(SX - 30, SX + 30, yb + d / 2 - 2, yb + ro + 14, YC - 8, YC + 8))
    k = k.cut(cyl('x', d / 2 + 0.2, SX - 31, SX + 31, (0, yb, YC)))
    k = k.cut(box(SX - 31, SX + 31, yb + d / 2 - 2, yb + ro + 15, YC - 1, YC + 1))
    for dx in (-18, 18):
        k = k.cut(cyl('z', 2.7, YC - 9, YC + 9, (SX + dx, yb + ro + 7, 0)))
    k = k.cut(mount_holes(TOP4 - 1, TOP4 + 7))
    k = k.cut(mount_holes(TOP4 + 6, yb + ro, r=4.2))     # screw head relief
    k = k.cut(cyl('z', 1.5, YC - ro - 1, YC - d / 2 + 1, (SX, yb, 0)))
    return k


def carriage_axis_y(d):
    return TOP4 + 7 + d / 2


FLANGE_T = 6.0
TB_BACK = (-13.0, -1.0)


def tripod_base():
    """Under the fixed deck: holds the body-yaw servo and a captive 1/4-20 nut for the tripod."""
    c = cage(back=TB_BACK, pivot=False)
    ft = EAR_Z + FLANGE_T
    c = c.union(box(-CAGE_HX, CAGE_HX, CAV_HY + 0.2, CAGE_HY, EAR_Z - 0.1, ft))
    c = c.union(box(-CAGE_HX, CAGE_HX, -CAGE_HY, -CAV_HY - 0.2, EAR_Z - 0.1, ft))
    fl = box(SX - 55, SX + 55, -55, 55, EAR_Z, ft).cut(box(-29, 29, -CAV_HY - 0.2, CAV_HY + 0.2, 0, 50))
    c = c.union(fl)
    for x in (-22, 17):
        for s in (-1, 1):
            g = (WP('YZ').polyline([(CAGE_HY - 0.1, EAR_Z + 0.1), (45, EAR_Z + 0.1), (CAGE_HY - 0.1, -8)])
                 .close().extrude(5).translate((x, 0, 0)))
            if s < 0:
                g = g.mirror('XZ')
            c = c.union(g)
    for sx in (-45, 45):
        for sy in (-45, 45):
            c = c.cut(cylz(2.3, EAR_Z - 1, ft + 1, SX + sx, sy))
    c = c.cut(cylz(3.4, TB_BACK[0] - 1, 0, SX, 0))
    c = c.cut(hexz(11.5, TB_BACK[1] - 5.8, TB_BACK[1] + 0.1).translate((SX, 0, 0)))
    return c


def yaw_hub_t():
    return (EAR_Z + FLANGE_T + PLY + LAZY_SUSAN_T) - HORN_Z


def yaw_hub():
    """Disc between the yaw servo horn and the underside of the turntable deck."""
    t = yaw_hub_t()
    h = cylz(25, 0, t).cut(horn_cut(t, cb=3.2, cbw=6.0))
    for i in range(4):
        a = math.radians(45 + 90 * i)
        h = h.cut(cylz(1.3, -1, t + 1, 19 * math.cos(a), 19 * math.sin(a)))
    return h


# ------------------------------------------------------------------ arm unit
ST_DX = 14.25              # stage: xD = u + ST_DX (u measured along the tilt axis from yoke centre)
RACK_P = SX + GEAR_M * GEAR_Z / 2 + BACKLASH          # rack pitch line (xD)
RACK_TIP = RACK_P - GEAR_M
RACK_ROOT = RACK_P + 1.25 * GEAR_M
RACK_BACK = RACK_ROOT + RACK_BODY
GUIDE_X1 = RACK_BACK + 0.3 + 3.8
GROOVE_X = RACK_ROOT + 7.0
SHELF_X1 = GUIDE_X1


def slide_stage():
    """Bolts on a tilt yoke. Holds the piston servo; the rack guide bolts to its shelf. Frame D."""
    xe = 33 + ST_DX
    s = cage(pivot=False)
    s = s.union(box(-CAGE_HX, xe, -CAGE_HY, CAGE_HY, BACK0, BACK1))
    for sy in (-1, 1):
        s = s.union(box(CAGE_HX - 0.1, xe, min(sy * CAV_HY, sy * CAGE_HY), max(sy * CAV_HY, sy * CAGE_HY),
                        BACK1 - 0.1, EAR_Z))
    s = s.union(box(CAGE_HX - 0.1, SHELF_X1, -22, 22, EAR_Z - TW, EAR_Z))
    for u in (-MNT_Z, MNT_Z):
        for v in (-MNT_X, MNT_X):
            s = s.cut(cylz(2.2, BACK0 - 1, BACK1 + 1, u + ST_DX, v))
            s = s.cut(cylz(3.9, BACK1 - 4.4, BACK1 + 0.1, u + ST_DX, v))
    for v in (-MNT_X, MNT_X):
        s = s.cut(cylz(3.25, EAR_Z - TW - 1, EAR_Z + 1, MNT_Z + ST_DX, v))
    for v in (-12, 12):
        s = s.cut(cylz(2.2, EAR_Z - TW - 1, EAR_Z + 1, RACK_ROOT + 9, v))
    return s


G_FLOOR = HORN_Z - 0.3


def rack_guide():
    """C-channel that carries the rack past the pinion. Bolts to the stage shelf. Frame D."""
    hl = GUIDE_LEN / 2
    g = box(RACK_ROOT + 2, GUIDE_X1, -hl, hl, EAR_Z, G_FLOOR)                       # pedestal
    g = g.union(box(RACK_ROOT + 1, GUIDE_X1, -hl, hl, G_FLOOR - 3, G_FLOOR))        # floor
    g = g.union(box(RACK_BACK + 0.3, GUIDE_X1, -hl, hl, G_FLOOR, HORN_Z + GEAR_T + 3.3))   # back wall
    g = g.union(box(RACK_ROOT + 4.5, GUIDE_X1, -hl, hl, HORN_Z + GEAR_T + 0.3, HORN_Z + GEAR_T + 3.3))
    g = g.union(box(GROOVE_X - 1.0, GROOVE_X + 1.0, -hl, hl, G_FLOOR - 0.1, G_FLOOR + 1.2))
    g = g.union(box(GROOVE_X - 1.0, GROOVE_X + 1.0, -hl, hl, HORN_Z + GEAR_T - 0.9, HORN_Z + GEAR_T + 0.4))
    for v in (-12, 12):
        g = g.cut(cylz(2.2, EAR_Z - 1, EAR_Z + 12, RACK_ROOT + 9, v))
        g = g.cut(box(RACK_ROOT + 9 - 3.65, GUIDE_X1 + 1, v - 3.65, v + 3.65, EAR_Z + 5, EAR_Z + 8.6))
    return g


PAD_Y0 = RACK_LEN / 2 - 28
PAD_X1 = RACK_ROOT + 25
ROD_X = RACK_ROOT + 12.5


def rack():
    """Toothed bar with the rod clamp pad on its front end. Frame D, mid position."""
    p = math.pi * GEAR_M
    ta = math.tan(math.radians(20))
    ht = p / 4 - 0.05
    pts = [(RACK_BACK, -RACK_LEN / 2), (RACK_ROOT, -RACK_LEN / 2)]
    n = int(RACK_LEN / p)
    y0 = -n * p / 2 + p / 2
    for i in range(n):
        yc = y0 + i * p
        pts += [(RACK_ROOT, yc - ht - 1.25 * GEAR_M * ta), (RACK_TIP, yc - ht + GEAR_M * ta),
                (RACK_TIP, yc + ht - GEAR_M * ta), (RACK_ROOT, yc + ht + 1.25 * GEAR_M * ta)]
    pts += [(RACK_ROOT, RACK_LEN / 2), (RACK_BACK, RACK_LEN / 2)]
    r = WP('XY').polyline(pts).close().extrude(GEAR_T).translate((0, 0, HORN_Z))
    for z in (HORN_Z - 0.1, HORN_Z + GEAR_T - 1.5):
        r = r.cut(box(GROOVE_X - 1.3, GROOVE_X + 1.3, -RACK_LEN / 2 - 1, PAD_Y0, z, z + 1.6))
    r = r.union(box(RACK_ROOT, PAD_X1, PAD_Y0, RACK_LEN / 2, HORN_Z, HORN_Z + GEAR_T))
    zt = HORN_Z + GEAR_T
    vee = (WP('XZ').polyline([(ROD_X - 4, zt + 0.1), (ROD_X, zt - 3.9), (ROD_X + 4, zt + 0.1)]).close()
           .extrude(-40).translate((0, PAD_Y0 - 5, 0)))
    r = r.cut(vee)
    for x in (ROD_X - 8.5, ROD_X + 8.5):
        r = r.cut(cylz(1.7, HORN_Z - 1, zt + 1, x, PAD_Y0 + 14))
        r = r.cut(hexz(5.8, HORN_Z - 0.1, HORN_Z + 2.6).translate((x, PAD_Y0 + 14, 0)))
    r = r.cut(cylz(1.7, HORN_Z - 1, zt + 1, GROOVE_X + 4, -RACK_LEN / 2 + 4))
    return r


def rod_cap():
    """Clamp cap for the arm rod (2-8 mm). Frame D."""
    zt = HORN_Z + GEAR_T
    c = box(ROD_X - 12.5, ROD_X + 12.5, PAD_Y0 + 4, PAD_Y0 + 24, zt + 0.6, zt + 5.6)
    vee = (WP('XZ').polyline([(ROD_X - 3, zt + 0.5), (ROD_X, zt + 3.5), (ROD_X + 3, zt + 0.5)]).close()
           .extrude(-40).translate((0, PAD_Y0 - 5, 0)))
    c = c.cut(vee)
    for x in (ROD_X - 8.5, ROD_X + 8.5):
        c = c.cut(cylz(1.7, zt, zt + 7, x, PAD_Y0 + 14))
    return c


def pinion():
    """Involute spur gear, bolts to a disc horn. Built at the origin, z = 0..GEAR_T."""
    m, z = GEAR_M, GEAR_Z
    r, rb = m * z / 2, m * z / 2 * math.cos(math.radians(20))
    ra, rf = r + m, r - 1.25 * m
    inv = math.tan(math.radians(20)) - math.radians(20)
    half = math.pi / (2 * z) - 0.04 / r + inv            # half tooth angle at the base circle
    tmax = math.sqrt((ra / rb) ** 2 - 1)
    pts = []
    for i in range(z):
        c = 2 * math.pi * i / z
        flank = []
        for k in range(7):
            t = tmax * k / 6
            rr = rb * math.sqrt(1 + t * t)
            flank.append((rr, t - math.atan(t)))
        left = [(rf, -half)] + [(rr, -half + a) for rr, a in flank]
        right = [(rr, half - a) for rr, a in reversed(flank)] + [(rf, half)]
        for rr, a in left + right:
            pts.append((rr * math.cos(c + a), rr * math.sin(c + a)))
    g = WP('XY').polyline(pts).close().extrude(GEAR_T)
    return g.cut(horn_cut(GEAR_T))


# ----------------------------------------------------------------- accessories
def speaker_mount(size=62.0):
    """Flat cradle with a toothed boss. Takes any 40-57 mm speaker: screw it through the diagonal
    slots (hole patterns 28-54 mm square) or strap a round one on with cable ties through the edge slots."""
    cy = BOSS_R + size / 2 - 4
    s = tooth_boss()
    s = s.union(box(-size / 2, size / 2, cy - size / 2, cy + size / 2, -BOSS_T, -BOSS_T + 4))
    s = s.union(box(-12, 12, 0, cy, -BOSS_T, -BOSS_T + 4))
    s = s.cut(cylz(17, -BOSS_T - 1, 1, 0, cy))
    for i in range(4):
        a = 45 + 90 * i
        sl = WP().center(29, 0).slot2D(21.4, 3.4).extrude(8).translate((0, 0, -BOSS_T - 1))
        s = s.cut(sl.rotate((0, 0, 0), (0, 0, 1), a).translate((0, cy, 0)))
        tie = WP().center(size / 2 - 4, 0).slot2D(12, 3, 90).extrude(8).translate((0, 0, -BOSS_T - 1))
        s = s.cut(tie.rotate((0, 0, 0), (0, 0, 1), 90 * i + 90).translate((0, cy, 0))) if i != 2 else s
    s = s.cut(tooth_boss_cut(True).rotate((0, 0, 0), (0, 0, 1), -90))
    return s


def accessory_mount():
    """Toothed boss with a slotted plate and a 1/4 inch hole: camera, mic, phone clamp, lights."""
    s = tooth_boss()
    s = s.union(box(-22, 22, 0, 90, -BOSS_T, -BOSS_T + 4))
    s = s.cut(cylz(3.4, -BOSS_T - 1, 1, 0, 72))
    for x in (-14, 14):
        s = s.cut(WP().center(x, 55).slot2D(50, 3.4, 90).extrude(8).translate((0, 0, -BOSS_T - 1)))
    s = s.cut(WP().center(0, 40).slot2D(26, 3.4, 90).extrude(8).translate((0, 0, -BOSS_T - 1)))
    s = s.cut(tooth_boss_cut(True).rotate((0, 0, 0), (0, 0, 1), -90))
    return s


def pipe_saddle(d):
    """Clamp ring with a flat foot and two screw holes: fixes plywood or anything flat to a pipe."""
    ro = ring_ro(d)
    k = cyl('x', ro, -13, 13, (0, 0, 0))
    k = k.union(box(-13, 13, -ro - 16, ro + 16, -ro - 2, -ro + 4))
    k = k.union(box(-9, 9, -8, 8, ro - 4, ro + 14))
    k = k.cut(cyl('x', d / 2 + 0.2, -14, 14, (0, 0, 0)))
    k = k.cut(box(-14, 14, -1, 1, d / 2 - 2, ro + 15))
    k = k.cut(cyl('y', 2.7, -9, 9, (0, 0, ro + 7)))
    for y in (-ro - 9, ro + 9):
        k = k.cut(cylz(2.3, -ro - 3, -ro + 5, 0, y))
    return k
