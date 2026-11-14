"""Assembly previews and clash checks. Run: python3 assembly.py"""
import os, math
from csg import box, cyl, union
import parts as P, geometry as G
from build import render, REN

T = G.PLATE_T
GREY, BLUE, ORANGE, GREEN, RED, DARK = (.6, .6, .62), (.25, .55, .85), (.95, .6, .2), (.3, .75, .4), (.85, .3, .3), (.25, .25, .28)


def corner_hw():
    px, py = G.P_LOCAL; fx, fy = G.F_LOCAL; kx, ky = G.K_LOCAL
    motor = box(px - 21.15, px + 21.15, py - 21.15, py + 21.15, -40, 0)
    shaft = cyl(px, py, 0, 22, 2.5)
    pulley = union(cyl(px, py, T + .5, T + 8, 8), cyl(px, py, T + 8, T + 9, 9), cyl(px, py, T + 9, T + 16, 6.1), cyl(px, py, T + 16, T + 17, 9))
    bearing = cyl(kx, ky, 15.5, 20.5, 8)
    sheet = box(0, 160, 0, 160, -18, 0)
    return motor, shaft, pulley, bearing, sheet


def corner_assembly():
    fx, fy = G.F_LOCAL; kx, ky = G.K_LOCAL
    motor, shaft, pulley, bearing, sheet = corner_hw()
    return [(sheet, (.85, .75, .55), 1), (P.corner_bracket(), BLUE, 1), (P.tail_guide(), ORANGE, 1),
            (P.f_spacer().translate((fx, fy, T)), GREEN, 1), (P.f_sleeve().translate((fx, fy, T + 8)), RED, 1),
            (P.k_spacer().translate((kx, ky, T)), GREEN, 1), (bearing, GREY, 1), (motor, DARK, 1), (union(shaft, pulley), GREY, 1)]


def sled_hw(cz):
    o = G.IDLER_OFFSET
    idlers = union(*[union(cyl(sx * o, sy * o, 13.5, 14.5, 9), cyl(sx * o, sy * o, 14.5, 21.5, 6), cyl(sx * o, sy * o, 21.5, 22.5, 9),
                           cyl(sx * o, sy * o, 22.5, 27.5, 4.6)) for sx in (-1, 1) for sy in (-1, 1)])
    rods = union(cyl(G.ROD_X, 0, 2, 152, 4), cyl(-G.ROD_X, 0, 2, 152, 4))
    router = union(cyl(0, 0, cz, cz + 200, 32.5), cyl(0, 0, cz - 24, cz, 11), cyl(0, 0, cz - 48, cz - 24, 3))
    zmotor = box(-21.15, 21.15, G.SCREW_Y - 21.15, G.SCREW_Y + 21.15, 154, 194)
    screw = union(cyl(0, G.SCREW_Y, 24, 136, 4), cyl(0, G.SCREW_Y, 123, 148, 9.5))
    return idlers, rods, router, zmotor, screw


def sled_assembly(cz=G.CARRIAGE_Z_MIN, shoe=True):
    idlers, rods, router, zmotor, screw = sled_hw(cz)
    items = [(P.sled_base(), BLUE, 1), (P.z_carriage().translate((0, 0, cz)), ORANGE, 1),
             (P.z_bridge().translate((0, 0, G.BRIDGE_Z)), GREEN, 1), (rods, GREY, 1), (idlers, GREY, 1),
             (router, RED, 1), (zmotor, DARK, 1), (screw, GREY, 1)]
    if shoe:
        items.append((P.dust_shoe(), (.8, .8, .3), 1))
    return items


def clash(a, b):
    return (a ^ b).volume()


def checks():
    out = []
    base, shoe, bridge = P.sled_base(), P.dust_shoe(), P.z_bridge().translate((0, 0, G.BRIDGE_Z))
    for cz in (G.CARRIAGE_Z_MIN, 69.0):
        car = P.z_carriage().translate((0, 0, cz))
        idlers, rods, router, zmotor, screw = sled_hw(cz)
        for n, a, b in (("carriage/base", car, base), ("carriage/shoe", car, shoe), ("carriage/bridge", car, bridge),
                        ("carriage/idlers", car, idlers), ("router/bridge", router, bridge), ("router/zmotor", router, zmotor),
                        ("carriage/coupler+screw", car, screw), ("router/shoe", router, shoe), ("shoe/idlers", shoe, idlers),
                        ("shoe/base", shoe, base), ("bridge/zmotor", bridge, zmotor)):
            out.append((f"z={cz:.0f} {n}", clash(a, b)))
    motor, shaft, pulley, bearing, sheet = corner_hw()
    br, tg = P.corner_bracket(), P.tail_guide()
    fx, fy = G.F_LOCAL; kx, ky = G.K_LOCAL
    fs, ks = P.f_spacer().translate((fx, fy, T)), P.k_spacer().translate((kx, ky, T))
    for n, a, b in (("bracket/motor", br, motor), ("bracket/sheet", br, sheet), ("bracket/pulley", br, pulley), ("pulley/bearing", pulley, bearing),
                    ("tailguide/pulley", tg, pulley), ("tailguide/bearing", tg, bearing), ("tailguide/bracket", tg, br),
                    ("fspacer/pulley", fs, pulley), ("kspacer/pulley", ks, pulley), ("kspacer/fspacer", ks, fs), ("motor/sheet", motor, sheet)):
        out.append((f"corner {n}", clash(a, b)))
    return out


if __name__ == "__main__":
    render(corner_assembly(), os.path.join(REN, "assembly_corner.png"), views=((35, -125), (35, 55), (89.9, -90)), title="Corner drive unit")
    render(sled_assembly(), os.path.join(REN, "assembly_sled.png"), views=((22, -65), (22, 115), (89.9, -90)), title="Sled, carriage down")
    render(sled_assembly(69, shoe=False)[:5] , os.path.join(REN, "assembly_sled_bare.png"), views=((30, -65), (30, 115), (89.9, -90)), title="Sled without router")
    for n, v in checks():
        print(f"{'CLASH' if v > 0.5 else 'ok   '} {n:34s} {v:8.1f} mm3")
