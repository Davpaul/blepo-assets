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
    return [(sheet, (.85, .75, .55), 1), (P.corner_bracket(), BLUE, 1), (P.reel_body(), ORANGE, 1), (P.reel_flange(), ORANGE, 1), (P.n20_cup(), GREEN, 1),
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
    br, tg = P.corner_bracket(), union(P.reel_body(), P.reel_flange())
    cup = P.n20_cup()
    n20 = box(G.REEL_LOCAL[0] - 6, G.REEL_LOCAL[0] + 6, G.REEL_LOCAL[1] - 5, G.REEL_LOCAL[1] + 5, G.N20_POCKET - 34, G.N20_POCKET)
    socket = box(-10, 30, G.REEL_LOCAL[1] - 17, G.REEL_LOCAL[1] + 3, -42, -5)   # RJ45 breakout board behind its panel
    fx, fy = G.F_LOCAL; kx, ky = G.K_LOCAL
    fs, ks = P.f_spacer().translate((fx, fy, T)), P.k_spacer().translate((kx, ky, T))
    for n, a, b in (("bracket/motor", br, motor), ("bracket/sheet", br, sheet), ("bracket/pulley", br, pulley), ("pulley/bearing", pulley, bearing),
                    ("reel/pulley", tg, pulley), ("reel/bearing", tg, bearing), ("reel/bracket", tg, br), ("reel/sheet", tg, sheet), ("cup/bracket", cup, br), ("cup/motor", cup, motor), ("n20/bracket", n20, br), ("n20/cup", n20, cup), ("socket/motor", socket, motor), ("socket/cup", socket, cup), ("reel/kspacer", tg, ks), ("reel/fspacer", tg, fs),
                    ("fspacer/pulley", fs, pulley), ("kspacer/pulley", ks, pulley), ("kspacer/fspacer", ks, fs), ("motor/sheet", motor, sheet)):
        out.append((f"corner {n}", clash(a, b)))
    return out


if __name__ == "__main__":
    render(corner_assembly(), os.path.join(REN, "assembly_corner.png"), views=((35, -125), (35, 55), (89.9, -90)), title="Corner drive unit")
    render(sled_assembly(), os.path.join(REN, "assembly_sled.png"), views=((22, -65), (22, 115), (89.9, -90)), title="Sled, carriage down")
    render(sled_assembly(69, shoe=False)[:5] , os.path.join(REN, "assembly_sled_bare.png"), views=((30, -65), (30, 115), (89.9, -90)), title="Sled without router")
    for n, v in checks():
        print(f"{'CLASH' if v > 0.5 else 'ok   '} {n:34s} {v:8.1f} mm3")


def step_renders():
    """One picture per assembly stage, for the PDF guide."""
    fx, fy = G.F_LOCAL; kx, ky = G.K_LOCAL; px, py = G.P_LOCAL
    motor, shaft, pulley, bearing, sheet = corner_hw()
    br = (P.corner_bracket(), BLUE, 1)
    bolts = (union(cyl(fx, fy, 0, 33, 2.5), cyl(kx, ky, 0, 28, 2.5)), RED, 1)
    mot = (union(motor, shaft), DARK, 1)
    posts = [(P.f_spacer().translate((fx, fy, T)), GREEN, 1), (P.f_sleeve().translate((fx, fy, T + 8)), ORANGE, 1),
             (P.k_spacer().translate((kx, ky, T)), GREEN, 1), (bearing, GREY, 1), (pulley, GREY, 1)]
    n20 = box(G.REEL_LOCAL[0] - 6, G.REEL_LOCAL[0] + 6, G.REEL_LOCAL[1] - 5, G.REEL_LOCAL[1] + 5, G.N20_POCKET - 34, G.N20_POCKET)
    reel = [(P.n20_cup(), GREEN, 1), (n20, DARK, 1), (P.reel_body(), ORANGE, 1), (P.reel_flange(), ORANGE, 1)]
    cv = ((32, -120), (-28, -120))
    render([br, bolts], os.path.join(REN, "step_corner_1.png"), views=cv)
    render([br, bolts, mot], os.path.join(REN, "step_corner_2.png"), views=cv)
    render([br, bolts, mot] + posts, os.path.join(REN, "step_corner_3.png"), views=((32, -120), (89.9, -90)))
    render([br, bolts, mot] + posts + reel, os.path.join(REN, "step_corner_4.png"), views=((32, -120), (-28, -120)))

    idlers, rods, router, zmotor, screw = sled_hw(45)
    base = (P.sled_base(), BLUE, 1)
    car = (P.z_carriage().translate((0, 0, 45)), ORANGE, 1)
    bridge = (P.z_bridge().translate((0, 0, G.BRIDGE_Z)), GREEN, 1)
    sv = ((26, -62), (26, 118))
    render([base, (idlers, GREY, 1)], os.path.join(REN, "step_sled_1.png"), views=sv)
    render([base, (idlers, GREY, 1), (rods, GREY, 1), car], os.path.join(REN, "step_sled_2.png"), views=sv)
    render([base, (idlers, GREY, 1), (rods, GREY, 1), car, bridge, (zmotor, DARK, 1), (screw, GREY, 1)], os.path.join(REN, "step_sled_3.png"), views=sv)
    render([base, (idlers, GREY, 1), (rods, GREY, 1), car, bridge, (zmotor, DARK, 1), (screw, GREY, 1), (router, RED, 1), (P.dust_shoe(), (.8, .8, .3), 1)],
           os.path.join(REN, "step_sled_4.png"), views=sv)
    render([(P.pen_caddy_body(), BLUE, 1), (P.pen_slider().translate((0, 0, -25)), ORANGE, 1), (cyl(-6, 0, -60, 90, 5), DARK, 1)],
           os.path.join(REN, "step_pen.png"), views=((24, -60), (24, 30)))
    render([(P.laser_caddy(), BLUE, 1), (box(-16.5, 16.5, -16.5, 16.5, -30, 70).translate((-4, 0, 0)), DARK, 1)],
           os.path.join(REN, "step_laser.png"), views=((24, -60), (60, 30)))
