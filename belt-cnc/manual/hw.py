"""Simple 3D models of the bought hardware, for the manual's pictures only."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cad"))
from csg import box, cyl, cyl_x, cyl_y, prism, hexprism, union, rounded_box, hull
import geometry as G


def hex_bolt(d, length, af, head_h, head_down=True):
    """Head at z=0..head_h, shaft above it (head_down) or shaft below (head on top)."""
    if head_down:
        return union(hexprism(0, 0, 0, head_h, af), cyl(0, 0, head_h, head_h + length, d / 2, seg=24))
    return union(hexprism(0, 0, 0, head_h, af), cyl(0, 0, -length, 0, d / 2, seg=24))


def cap_screw(d, length, head_d, head_h, pointing_down=True):
    """Head on top (z 0..head_h), shaft going down; or flipped."""
    s = union(cyl(0, 0, 0, head_h, head_d / 2, seg=24), cyl(0, 0, -length, 0, d / 2, seg=20)) - hexprism(0, 0, head_h - 1.5, head_h + 1, d * 0.85)
    return s if pointing_down else s.rotate((180, 0, 0))


def csk_bolt(d, length, head_d, head_h):
    """Countersunk head at the bottom (z=0), shaft up."""
    return union(cyl(0, 0, 0, head_h, head_d / 2, d / 2, seg=32), cyl(0, 0, head_h, length, d / 2, seg=24))


def nut(af, h, nyloc=False):
    n = hexprism(0, 0, 0, h, af) - cyl(0, 0, -1, h + 1, af * 0.3, seg=20)
    if nyloc:
        n = union(n, cyl(0, 0, h, h + 1.5, af * 0.46, seg=24) - cyl(0, 0, h - 1, h + 2, af * 0.3, seg=20))
    return n


def washer(od, hole, t=1.0):
    return cyl(0, 0, 0, t, od / 2, seg=32) - cyl(0, 0, -1, t + 1, hole / 2, seg=24)


def bearing(od, hole, w):
    return cyl(0, 0, 0, w, od / 2, seg=48) - cyl(0, 0, -1, w + 1, hole / 2, seg=32) - (cyl(0, 0, w - 0.4, w + 1, od / 2 - 1.2, seg=48) - cyl(0, 0, w - 1, w + 2, hole / 2 + 1.3, seg=32))


def pulley():
    """20-tooth GT2 pulley, hub down, bottom at z=0."""
    teeth = union(*[box(5.6, 6.3, -0.5, 0.5, 8.5, 15.5).rotate((0, 0, 18 * i)) for i in range(20)])
    return union(cyl(0, 0, 0, 7.5, 8, seg=40), cyl(0, 0, 7.5, 8.5, 9, seg=40), cyl(0, 0, 8.5, 15.5, 5.7, seg=40), teeth,
                 cyl(0, 0, 15.5, 16.5, 9, seg=40)) - cyl(0, 0, -1, 18, 2.5, seg=24) - cyl_x(3, 9, 0, 3.75, 1.5, seg=12)


def idler():
    return union(cyl(0, 0, 0, 1, 9, seg=40), cyl(0, 0, 1, 8, 6, seg=40), cyl(0, 0, 8, 9, 9, seg=40)) - cyl(0, 0, -1, 10, 2.5, seg=24)


def nema17(length=40, shaft=22):
    """Mounting face at z=0, body below, shaft up."""
    body = prism([(-21.15, -17), (-17, -21.15), (17, -21.15), (21.15, -17), (21.15, 17), (17, 21.15), (-17, 21.15), (-21.15, 17)], -length, 0)
    holes = union(*[cyl(sx * 15.5, sy * 15.5, -5, 1, 1.4, seg=12) for sx in (-1, 1) for sy in (-1, 1)])
    return union(body, cyl(0, 0, 0, 2, 11, seg=40), cyl(0, 0, 0, shaft, 2.5, seg=24) - box(2.0, 4, -3, 3, shaft - 15, shaft + 1)) - holes


def n20():
    """Gearbox face at z=0, body below, D shaft up."""
    return union(box(-6, 6, -5, 5, -9, 0), cyl(0, 0, -34, -9, 5.9, seg=24) ^ box(-6, 6, -5, 5, -34, -9),
                 cyl(0, 0, 0, 10, 1.5, seg=16) - box(1.0, 3, -3, 3, 1, 11))


def lm8uu():
    return cyl(0, 0, 0, 24, 7.5, seg=40) - cyl(0, 0, -1, 25, 4, seg=24)


def rod(length=150):
    return cyl(0, 0, 0, length, 4, seg=24)


def lead_screw(length=115):
    return union(cyl(0, 0, 0, length, 3.4, seg=20), *[cyl(0, 0, z, z + 1, 4, seg=20) for z in range(1, int(length) - 1, 3)])


def t8_nut():
    """Flange on top (z -3.5..0), body hanging below."""
    n = union(cyl(0, 0, -3.5, 0, 11, seg=40), cyl(0, 0, -15, 0, 5.1, seg=32)) - cyl(0, 0, -16, 1, 3.4, seg=20)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        n -= cyl(8 * math.cos(a), 8 * math.sin(a), -4, 1, 1.75, seg=12)
    return n


def coupler():
    return cyl(0, 0, 0, 25, 9.5, seg=40) - cyl(0, 0, -1, 26, 2.5, seg=20) - box(-0.5, 0.5, 0, 10, 2, 23)


def microswitch():
    """Body 20 x 6.4 x 10, lever below. Mounting face is +y."""
    return union(box(-10, 10, -6.4, 0, -5, 5), box(-9, 9, -5, -1.4, -8, -5).rotate((0, 6, 0)), box(-8, -6.8, -4, -2.4, 5, 8),
                 box(-0.6, 0.6, -4, -2.4, 5, 8), box(6.8, 8, -4, -2.4, 5, 8))


def router(clamp_z=0.0):
    """65 mm trim router: body from clamp_z up, collet and bit below."""
    return union(cyl(0, 0, clamp_z - 6, clamp_z + 120, 32.5, seg=64), cyl(0, 0, clamp_z + 120, clamp_z + 185, 36, seg=64),
                 cyl(0, 0, clamp_z - 12, clamp_z - 6, 20, seg=40), cyl(0, 0, clamp_z - 30, clamp_z - 12, 10, seg=6), cyl(0, 0, clamp_z - 52, clamp_z - 30, 3.17, seg=16))


def breakout():
    """RJ45 breakout board, 36 x 30, lying flat: board z 0..1.6, socket and terminals on top."""
    b = union(rounded_box(-18, 18, -15, 15, 0, 1.6, 2), box(-8, 8, -15, 1, 1.6, 15), box(-16, 16, 5, 13, 1.6, 9))
    b -= box(-5.8, 5.8, -16, -4, 4, 12.5)
    for i in range(8):
        b -= cyl(-13.7 + i * 3.9, 9, 6, 10, 1.2, seg=10)
    return b


def wing_nut():
    return union(cyl(0, 0, 0, 6, 5.5, seg=24), hull(box(4, 6, -1.2, 1.2, 1, 5), box(11, 13, -1.2, 1.2, 7, 12)),
                 hull(box(-6, -4, -1.2, 1.2, 1, 5), box(-13, -11, -1.2, 1.2, 7, 12))) - cyl(0, 0, -1, 7, 3, seg=16)


def t_nut():
    """Flange at the bottom (z -1.5..0), barrel up into the board."""
    return union(cyl(0, 0, -1.5, 0, 9.5, seg=32), cyl(0, 0, 0, 9, 3.9, seg=24)) - cyl(0, 0, -2, 10, 3, seg=16)


def ribbon(points, z0, z1, t=1.4):
    """A belt drawn as a thin wall following a path seen from above."""
    left, right = [], []
    n = len(points)
    for i, (x, y) in enumerate(points):
        ax, ay = points[max(i - 1, 0)]; bx, by = points[min(i + 1, n - 1)]
        dx, dy = bx - ax, by - ay
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln * t / 2, dx / ln * t / 2
        left.append((x + nx, y + ny)); right.append((x - nx, y - ny))
    return prism(left + right[::-1], z0, z1)


def pen():
    return union(cyl(0, 0, 0, 120, 5, seg=24), cyl(0, 0, -14, 0, 5, 1.2, seg=24))


def laser_module():
    return union(box(-16.5, 16.5, -16.5, 16.5, 0, 90), cyl(0, 0, -8, 0, 7, seg=24))
