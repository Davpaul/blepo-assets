"""
Places every part of the Twist animatronic core in its working position for a given pose.
Used for collision checks, renders and the STEP export of the whole rig.

Global frame of the rig: X = puppet's left/right, Y = forward (nose), Z = up.
"""
import math
import cadquery as cq
from cadquery import Location as L, Plane, Vector as V
import parts as P
from parts import SX, YC, HORN_Z

PRINT = (0.95, 0.55, 0.15)
PRINT2 = (0.25, 0.55, 0.85)
SERVO = (0.2, 0.2, 0.22)
PIPE = (0.92, 0.92, 0.9)
WOOD = (0.82, 0.68, 0.45)
METAL = (0.6, 0.62, 0.65)
ELEC = (0.15, 0.5, 0.25)


def frame(origin, xdir, normal):
    return L(Plane(origin=origin, xDir=xdir, normal=normal))


def rot(point, axis, deg):
    p = V(*point)
    return L(p) * L(V(0, 0, 0), V(*axis), deg) * L(-p)


def shaft_rot(deg):
    """Rotation about the servo shaft of a cage frame."""
    return rot((SX, 0, 0), (0, 0, 1), deg)


A_ON_HORN = frame((SX + YC, SX, HORN_Z + 16), (0, -1, 0), (-1, 0, 0))     # bracket_L on a horn
B_IN_A = L(V(SX + YC, P.PITCH_UP, YC - SX)) * L(V(0, 0, 0), V(0, 1, 0), -90)
C_IN_B = L(V(P.JAW_FWD, P.JAW_UP, 0))
FLIP = L(V(0, 0, 0), V(1, 0, 0), 180)

_cache = {}


def part(name, *a):
    key = (name,) + a
    if key not in _cache:
        _cache[key] = getattr(P, name)(*a).val()
    return _cache[key]


def pipe(d, length):
    key = ('pipe', d, round(length, 1))
    if key not in _cache:
        _cache[key] = (cq.Workplane().circle(d / 2).circle(d / 2 - 2.6).extrude(length)
                       .rotate((0, 0, 0), (0, 1, 0), 90).val())      # along +x from origin
    return _cache[key]


def knuckle_mate(d, phi):
    """Frame of the second knuckle of a pair, relative to the first, at joint angle phi."""
    c, zt = P.boss_c(d), P.ring_ro(d) + 0.25
    return rot((0, c, 0), (0, 0, 1), phi) * L(V(0, 2 * c, 2 * zt + P.TOOTH_SEP)) * FLIP


def device_mate(d, phi):
    """Frame of a toothed-boss device (tooth base plane z=0) mated to a knuckle."""
    c, zt = P.boss_c(d), P.ring_ro(d) + 0.25
    return L(V(0, c, zt + P.TOOTH_SEP)) * FLIP * L(V(0, 0, 0), V(0, 0, 1), phi)


DEFAULT_POSE = dict(yaw=0, lean_roll=0, lean_pitch=0, head_yaw=0, head_roll=0, head_pitch=0, jaw=0,
                    pan_l=0, tilt_l=0, ext_l=0, pan_r=0, tilt_r=0, ext_r=0)


def build(d=26.7, pose=None, extras=True):
    """Returns a list of (name, located shape, colour, link id)."""
    q = dict(DEFAULT_POSE)
    q.update(pose or {})
    out = []

    def add(name, shape, loc, col, link):
        out.append((name, shape.moved(loc), col, link))

    sv = part('servo')
    # ---------------------------------------------------------------- base
    zdeck0 = P.EAR_Z + P.FLANGE_T
    zdeck1 = zdeck0 + P.PLY
    zturn0 = zdeck1 + P.LAZY_SUSAN_T
    zturn1 = zturn0 + P.PLY
    TB = L(V(-SX, 0, 0))
    add('tripod_base', part('tripod_base'), TB, PRINT, 'base')
    add('servo_yaw', sv, TB, SERVO, 'base')
    if extras:
        deck = (cq.Workplane().box(170, 170, P.PLY, centered=(True, True, False)).circle(35).cutThruAll()
                .translate((0, 0, zdeck0)).val())
        add('deck_fixed', deck, L(), WOOD, 'base')
        ls = (cq.Workplane().circle(75).circle(52).extrude(P.LAZY_SUSAN_T).translate((0, 0, zdeck1)).val())
        add('lazy_susan', ls, L(), METAL, 'base')
    YAW = L(V(0, 0, 0), V(0, 0, 1), q['yaw'])
    add('yaw_hub', part('yaw_hub'), YAW * L(V(0, 0, HORN_Z)), PRINT2, 'turn')
    if extras:
        deck2 = (cq.Workplane().box(180, 180, P.PLY, centered=(True, True, False))
                 .translate((0, 0, zturn0)).val())
        add('deck_turntable', deck2, YAW, WOOD, 'turn')
    # ---------------------------------------------------------- lean gimbal
    A = YAW * frame((SX, -YC, zturn1 + 16), (-1, 0, 0), (0, 1, 0))
    add('lean_bracket_L', part('bracket_L'), A, PRINT, 'turn')
    add('servo_lean_roll', sv, A, SERVO, 'turn')
    G3 = A * shaft_rot(q['lean_roll'])
    add('lean_roll_yoke', part('roll_yoke'), G3, PRINT2, 'lean_roll')
    B = G3 * B_IN_A
    add('servo_lean_pitch', sv, B, SERVO, 'lean_roll')
    G4 = B * shaft_rot(q['lean_pitch'])
    add('lean_pitch_yoke', part('pitch_yoke'), G4, PRINT, 'body')
    add('carriage', part('carriage', d), G4, PRINT2, 'body')
    # rig frame: X right, Y forward, Z up, origin on the boom axis above the lean centre
    R = G4 * frame((SX, P.carriage_axis_y(d), YC), (0, 0, 1), (0, 1, 0))
    c = P.boss_c(d)
    zsep = 2 * (P.ring_ro(d) + 0.25) + P.TOOTH_SEP
    s5, zk3 = 200.0, 260.0
    yk1 = s5 * math.cos(math.radians(30))
    kn = part('knuckle', d)
    # boom
    add('pipe_boom', pipe(d, yk1 + 20 + 110), R * frame((0, -yk1 - 20, 0), (0, 1, 0), (0, 0, 1)), PIPE, 'body')
    K1 = R * frame((0, -yk1, 0), (0, 1, 0), (1, 0, 0))
    add('knuckle_1', kn, K1, PRINT, 'body')
    K2 = K1 * knuckle_mate(d, 90)
    add('knuckle_2', kn, K2, PRINT2, 'body')
    K3 = R * frame((zsep, -yk1 - c, zk3), (0, 0, 1), (-1, 0, 0))
    add('pipe_mast', pipe(d, zk3 + 20 - (c - 20)), R * frame((zsep, -yk1 - c, c - 20), (0, 0, 1), (0, 1, 0)), PIPE, 'body')
    add('knuckle_3', kn, K3, PRINT, 'body')
    K4 = K3 * knuckle_mate(d, 60)
    add('knuckle_4', kn, K4, PRINT2, 'body')
    add('pipe_entry', pipe(d, s5 + 40), K4 * L(V(-20, 0, 0)), PIPE, 'body')
    I = L()
    k4r = (frame((zsep, -yk1 - c, zk3), (0, 0, 1), (-1, 0, 0)) * knuckle_mate(d, 60))
    p5 = tp(k4r, (s5, 0, 0))
    e5 = vsub(tp(k4r, (1, 0, 0)), tp(k4r, (0, 0, 0)))
    K5 = R * frame(p5, e5, (1, 0, 0))                          # boss faces +X, bolt sits up-back of the pipe
    add('knuckle_5', kn, K5, PRINT, 'body')
    # ----------------------------------------------------------------- neck
    n = vsub(tp(K5, (0, 0, 1)), tp(K5, (0, 0, 0)))            # K5 boss face normal (global)
    up = vsub(tp(R, (0, 0, 1)), tp(R, (0, 0, 0)))
    xd = cross(n, up)
    yb0 = P.ring_ro(d) + 0.25 + P.TOOTH_SEP
    bolt = tp(K5, (0, c, yb0))                                  # bolt axis, on the neck tooth plane
    o = tuple(bolt[i] - SX * xd[i] - yb0 * n[i] - P.NECK_DROP * up[i] for i in range(3))
    N1 = frame(o, xd, up)
    add('neck_base', part('neck_base', d), N1, PRINT2, 'body')
    add('servo_head_yaw', sv, N1, SERVO, 'body')
    An = N1 * shaft_rot(q['head_yaw']) * A_ON_HORN
    add('neck_bracket_L', part('bracket_L'), An, PRINT, 'head_yaw')
    add('servo_head_roll', sv, An, SERVO, 'head_yaw')
    G3n = An * shaft_rot(q['head_roll'])
    add('neck_roll_yoke', part('roll_yoke'), G3n, PRINT2, 'head_roll')
    Bn = G3n * B_IN_A
    add('servo_head_pitch', sv, Bn, SERVO, 'head_roll')
    G4n = Bn * shaft_rot(q['head_pitch'])
    add('neck_pitch_yoke', part('pitch_yoke'), G4n, PRINT, 'head')
    add('head_frame', part('head_frame'), G4n, PRINT2, 'head')
    Cn = G4n * C_IN_B
    add('servo_jaw', sv, Cn, SERVO, 'head')
    add('paddle_upper', part('paddle'), G4n * frame((SX + P.JAW_FWD + 30, P.TOP4, YC), (1, 0, 0), (0, -1, 0)),
        PRINT, 'head')
    J = Cn * shaft_rot(-q['jaw'])
    add('jaw_yoke', part('jaw_yoke'), J, PRINT, 'jaw')
    add('paddle_lower', part('paddle'), J * frame((SX + 30, P.JAW_FLOOR + P.TW, YC), (1, 0, 0), (0, 1, 0)), PRINT2, 'jaw')
    # ------------------------------------------------------------ arm units
    yk6 = -62.0
    K6 = R * frame((0, yk6, 0), (0, 1, 0), (0, 0, 1))
    add('knuckle_6', kn, K6, PRINT, 'body')
    K7 = K6 * knuckle_mate(d, 90)
    add('knuckle_7', kn, K7, PRINT2, 'body')
    wo = 215.0
    add('pipe_outrigger', pipe(d, 2 * wo + 40), R * frame((-wo - 20, yk6 - c, zsep), (1, 0, 0), (0, 0, 1)), PIPE, 'body')
    ang = math.radians(75)                     # arm units aim 75 deg above horizontal at rest
    nrm = (0, math.cos(ang), math.sin(ang))
    for side, sgn in (('r', 1), ('l', -1)):
        K8 = R * frame((sgn * wo, yk6 - c, zsep), (1, 0, 0), nrm)
        add('knuckle_arm_' + side, kn, K8, PRINT, 'body')
        n8 = vsub(tp(K8, (0, 0, 1)), tp(K8, (0, 0, 0)))
        zl = vsub(tp(K8, (0, 1, 0)), tp(K8, (0, 0, 0)))        # pan axis points away from the clamp ring
        yl = tuple(-v for v in n8)
        xl = cross(yl, zl)
        bolt8 = tp(K8, (0, c, P.ring_ro(d) + 0.25 + P.TOOTH_SEP))
        zc = (P.BACK0 + P.EAR_Z) / 2
        o8 = tuple(bolt8[i] - (P.CAGE_HY + P.BOSS_T) * yl[i] - zc * zl[i] for i in range(3))
        SB = frame(o8, xl, zl)
        add('arm_base_' + side, part('servo_base'), SB, PRINT2, 'body')
        add('servo_pan_' + side, sv, SB, SERVO, 'body')
        Am = SB * shaft_rot(q['pan_' + side]) * A_ON_HORN
        add('arm_bracket_L_' + side, part('bracket_L'), Am, PRINT, 'pan_' + side)
        add('servo_tilt_' + side, sv, Am, SERVO, 'pan_' + side)
        T = Am * shaft_rot(q['tilt_' + side])
        add('arm_tilt_yoke_' + side, part('pitch_yoke', P.H_TILT), T, PRINT2, 'tilt_' + side)
        D = T * frame((SX, P.H_TILT + P.WEB4 - P.BACK0, YC - P.ST_DX), (0, 0, 1), (0, 1, 0))
        add('arm_slide_stage_' + side, part('slide_stage'), D, PRINT, 'tilt_' + side)
        add('servo_ext_' + side, sv, D, SERVO, 'tilt_' + side)
        add('arm_rack_guide_' + side, part('rack_guide'), D, PRINT2, 'tilt_' + side)
        add('arm_pinion_' + side, part('pinion'), D * L(V(SX, 0, HORN_Z)), PRINT2, 'tilt_' + side)
        E = D * L(V(0, q['ext_' + side], 0))
        add('arm_rack_' + side, part('rack'), E, PRINT, 'ext_' + side)
        add('arm_rod_cap_' + side, part('rod_cap'), E, PRINT2, 'ext_' + side)
        if extras:
            rod = cq.Workplane().circle(1.5).extrude(330).rotate((0, 0, 0), (1, 0, 0), -90).val()
            add('arm_rod_' + side, rod, E * L(V(P.ROD_X, P.PAD_Y0, HORN_Z + P.GEAR_T - 1.8)), METAL, 'ext_' + side)
    # ------------------------------------------- electronics board on the mast
    sd = part('pipe_saddle', d)
    ro = P.ring_ro(d)
    for k, zz in enumerate((80, 210)):
        add('pipe_saddle_%d' % (k + 1), sd, R * frame((zsep, -yk1 - c, zz), (0, 0, 1), (0, 1, 0)), PRINT2, 'body')
    if extras:
        yb = -yk1 - c - ro - 2
        board = cq.Workplane().box(150, 9, 170, centered=(True, False, False)).translate((zsep, yb - 9, 60)).val()
        add('electronics_board', board, R, WOOD, 'body')
        for nm, (bx, bz), (px, pz) in (('raspberry_pi', (65, 30), (-35, 195)), ('servo_driver_1', (62, 26), (35, 200)),
                                        ('servo_driver_2', (62, 26), (35, 165)), ('buck_converter', (60, 52), (-35, 110)),
                                        ('amp', (20, 20), (35, 110))):
            b = cq.Workplane().box(bx, 12, bz, centered=(True, False, True)).translate((zsep + px, yb - 9 - 16, pz)).val()
            add(nm, b, R, ELEC, 'body')
    # -------------------------------------------------------------- speaker
    K9 = R * frame((zsep, -yk1 - c, 145), (0, 0, 1), (0, 1, 0))
    add('knuckle_speaker', kn, K9, PRINT, 'body')
    add('speaker_mount', part('speaker_mount'), K9 * device_mate(d, 180), PRINT2, 'body')
    return out


def tp(loc, pt):
    return cq.Vertex.makeVertex(*pt).moved(loc).toTuple()


def vsub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def device_neck_unused(d):
    """neck_base cage frame relative to the knuckle on the end of the entry pipe."""
    cc, zt = P.boss_c(d), P.ring_ro(d) + 0.25
    yb0 = zt + P.TOOTH_SEP
    # knuckle boss axis is its local z at (0, cc); neck_base boss axis is its local y at (SX, z=-30)
    # neck local y -> knuckle +z, neck local z (shaft) -> chosen by the tooth step, here 60 deg from knuckle y
    a = math.radians(60)
    zdir = (math.sin(a), math.cos(a), 0)           # neck shaft direction in knuckle frame
    ydir = (0, 0, 1)
    xdir = (ydir[1] * zdir[2] - ydir[2] * zdir[1], ydir[2] * zdir[0] - ydir[0] * zdir[2], 0)
    o = (0 - SX * xdir[0] + 30 * zdir[0], cc - SX * xdir[1] + 30 * zdir[1], 0)
    return frame(o, xdir, zdir)


if __name__ == '__main__':
    items = build()
    print(len(items), 'items')
    for n, s, _, _ in items:
        bb = s.BoundingBox()
        print(f'{n:22s} x[{bb.xmin:7.1f},{bb.xmax:7.1f}] y[{bb.ymin:7.1f},{bb.ymax:7.1f}] z[{bb.zmin:7.1f},{bb.zmax:7.1f}]')
