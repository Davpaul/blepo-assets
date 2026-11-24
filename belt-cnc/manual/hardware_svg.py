"""Life-size drawings of the fasteners and small parts, as SVG measured in millimetres.

Each entry in HW is (label, svg_body, width_mm, height_mm). Printed at 100% they are true size.
"""
import math

STEEL, BRASS, DARK, BLUE, ORANGE = "#c9ccd1", "#d9b85a", "#1f2328", "#4d82d6", "#e8902a"
ST = f'stroke="{DARK}" stroke-width="0.18"'


def rect(x, y, w, h, fill=STEEL, r=0):
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{r}" fill="{fill}" {ST}/>'


def circ(x, y, r, fill=STEEL):
    return f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{fill}" {ST}/>'


def poly(pts, fill=STEEL):
    return f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x, y in pts)}" fill="{fill}" {ST}/>'


def hexa(x, y, af, fill=STEEL):
    R = af / math.sqrt(3)
    return poly([(x + R * math.cos(math.radians(60 * i)), y + R * math.sin(math.radians(60 * i))) for i in range(6)], fill)


def thread(x, y, d, length):
    s = rect(x, y - d / 2, length, d)
    n = max(2, int(length / 1.0))
    for i in range(1, n):
        xx = x + i * length / n
        s += f'<line x1="{xx:.2f}" y1="{y - d / 2:.2f}" x2="{xx - 0.4:.2f}" y2="{y + d / 2:.2f}" stroke="#6b7078" stroke-width="0.1"/>'
    return s


def screw(kind, d, length, head_d, head_h):
    cy = head_d / 2
    if kind == "csk":
        body = thread(head_h, cy, d, length - head_h) + poly([(0, 0), (0, head_d), (head_h, cy + d / 2), (head_h, cy - d / 2)])
        return body, length, head_d
    body = thread(head_h, cy, d, length)
    if kind == "pan":
        body += rect(0, 0, head_h, head_d, r=min(head_h * 0.45, 1.0))
    else:
        body += rect(0, 0, head_h, head_d)
        if kind == "hex":
            for f in (0.25, 0.75):
                body += f'<line x1="0" y1="{head_d * f:.2f}" x2="{head_h}" y2="{head_d * f:.2f}" stroke="{DARK}" stroke-width="0.12"/>'
    return body, length + head_h, head_d


def nut(af, h, nyloc=False):
    w = af * 1.16
    s = hexa(w / 2, af / 2, af) + circ(w / 2, af / 2, af * 0.3, "#fff") + rect(w + 3, 0, h, af)
    if nyloc:
        s += rect(w + 3 + h * 0.68, af * 0.1, h * 0.32, af * 0.8, BLUE)
    return s, w + 3 + h, af


def washer(od, hole):
    return circ(od / 2, od / 2, od / 2) + circ(od / 2, od / 2, hole / 2, "#fff"), od, od


def ring(od, hole, width, fill=STEEL):
    return circ(od / 2, od / 2, od / 2, fill) + circ(od / 2, od / 2, hole / 2, "#fff") + rect(od + 3, 0, width, od, fill), od + 3 + width, od


def pulley():
    cy = 9
    s = rect(0, cy - 8, 7.5, 16) + rect(7.5, cy - 9, 1, 18) + rect(8.5, cy - 6.1, 7, 12.2, "#a9adb3") + rect(15.5, cy - 9, 1, 18)
    for i in range(1, 7):
        y = cy - 6.1 + i * 12.2 / 7
        s += f'<line x1="8.5" y1="{y:.2f}" x2="15.5" y2="{y:.2f}" stroke="{DARK}" stroke-width="0.1"/>'
    return s + circ(3.5, cy, 1.4, DARK), 16.5, 18


def idler():
    cy = 9
    return (rect(0, cy - 9, 1, 18) + rect(1, cy - 6, 7, 12) + rect(8, cy - 9, 1, 18) + circ(21, cy, 9) + circ(21, cy, 6, "#e6e7ea") + circ(21, cy, 2.5, "#fff")), 30, 18


def n20():
    return rect(0, 4.5, 10, 3) + rect(10, 0, 9, 12, BRASS) + rect(19, 1, 25, 10, "#b5b8bd", 1), 44, 12


def tnut():
    return circ(9.5, 9.5, 9.5) + circ(9.5, 9.5, 3, "#fff") + rect(22, 0, 1.5, 19) + rect(23.5, 5.5, 9, 8), 32.5, 19


def wingnut():
    return (rect(8, 8, 8, 6) + poly([(8, 11), (0, 1), (5, 0), (10, 8)]) + poly([(16, 11), (24, 1), (19, 0), (14, 8)])), 24, 14


def switch():
    s = rect(0, 0, 20, 10, "#33363b", 0.5) + circ(5.25, 7, 1.2, "#fff") + circ(14.75, 7, 1.2, "#fff")
    s += f'<line x1="2" y1="-0.3" x2="19" y2="-3" stroke="{DARK}" stroke-width="0.5"/>'
    for i in (2, 10, 18):
        s += rect(i - 0.6, 10, 1.2, 3, BRASS)
    return f'<g transform="translate(0,3.2)">{s}</g>', 20, 16.5


def resistor():
    return f'<line x1="0" y1="5" x2="42" y2="5" stroke="#6b7078" stroke-width="0.6"/>' + rect(10, 0, 22, 10, "#eeece3"), 42, 10


def belt():
    s = rect(0, 0, 50, 6, "#26282b")
    for i in range(1, 25):
        s += f'<line x1="{i * 2}" y1="0" x2="{i * 2}" y2="6" stroke="#9a9da3" stroke-width="0.3"/>'
    return s, 50, 6


def rj45():
    s = rect(0, 0, 36, 30, "#1b7340", 1) + rect(10, 2, 16, 16, "#c0c3c8") + rect(12.2, 2, 11.6, 8, "#26282b")
    for i in range(8):
        s += rect(2.5 + i * 3.9, 21, 3.5, 7, BLUE) + circ(4.25 + i * 3.9, 24.5, 1.1)
    return s, 36, 30


def wago():
    return rect(0, 0, 13, 18, "#ebebe6", 1) + rect(1.5, 0.5, 4.5, 6.5, ORANGE) + rect(7, 0.5, 4.5, 6.5, ORANGE), 13, 18


def rod(length, d, threaded=False):
    return (thread(0, d / 2, d, length) if threaded else rect(0, 0, length, d)), length, d


def ziptie():
    return rect(0, 1.2, 60, 2.5, "#f1f1ee") + rect(60, 0, 5, 5, "#f1f1ee"), 65, 5


HW = {
    "m3x8":    ("M3 x 8 cap screw",) + screw("cap", 3, 8, 5.5, 3),
    "m3x10":   ("M3 x 10 cap screw",) + screw("cap", 3, 10, 5.5, 3),
    "m3x12":   ("M3 x 12 pan head",) + screw("pan", 3, 12, 5.6, 2.4),
    "m2x10":   ("M2 x 10 self-tapper",) + screw("pan", 2, 10, 3.8, 1.5),
    "m5x25":   ("M5 x 25 hex bolt",) + screw("hex", 5, 25, 8, 3.5),
    "m5x30":   ("M5 x 30 hex bolt",) + screw("hex", 5, 30, 8, 3.5),
    "m5x40":   ("M5 x 40 hex bolt",) + screw("hex", 5, 40, 8, 3.5),
    "m5csk":   ("M5 x 30 countersunk",) + screw("csk", 5, 30, 9.2, 2.8),
    "m6x40":   ("M6 x 40 hex bolt",) + screw("hex", 6, 40, 10, 4),
    "m3nut":   ("M3 nut",) + nut(5.5, 2.4),
    "m5nut":   ("M5 plain nut",) + nut(8, 4),
    "m5nyl":   ("M5 nyloc nut (blue ring)",) + nut(8, 5, True),
    "m6nut":   ("M6 nut (goes inside a knob)",) + nut(10, 5),
    "m5wash":  ("M5 washer",) + washer(10, 5.3),
    "m6wash":  ("M6 penny washer",) + washer(25, 6.4),
    "wing":    ("M6 wing nut",) + wingnut(),
    "tnut":    ("M6 T-nut",) + tnut(),
    "625":     ("625ZZ bearing 5 x 16 x 5",) + ring(16, 5, 5),
    "lm8uu":   ("LM8UU bearing 8 x 15 x 24",) + ring(15, 8, 24),
    "pulley":  ("GT2 20-tooth pulley",) + pulley(),
    "idler":   ("Smooth idler, 5mm bore",) + idler(),
    "tnutT8":  ("T8 brass nut",) + ring(22, 8, 15, BRASS),
    "coupler": ("Shaft coupler 5 to 8mm",) + ring(19, 5, 25, "#cfd1d5"),
    "rod":     ("8mm rod, 150 long",) + rod(150, 8),
    "screw":   ("T8 lead screw cut to 115",) + rod(115, 8, True),
    "n20":     ("N20 geared motor",) + n20(),
    "switch":  ("Microswitch",) + switch(),
    "res":     ("120 ohm 5W resistor",) + resistor(),
    "belt":    ("GT2 belt: 6 wide, teeth every 2mm",) + belt(),
    "rj45":    ("RJ45 breakout board (size varies)",) + rj45(),
    "wago":    ("Lever connector",) + wago(),
    "ziptie":  ("Small zip tie",) + ziptie(),
}


def svg(key):
    label, body, w, h = HW[key]
    pad = 0.3
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w + 2 * pad:.2f}mm" height="{h + 2 * pad + 3.2:.2f}mm" '
            f'viewBox="{-pad} {-pad - 3.2} {w + 2 * pad:.2f} {h + 2 * pad + 3.2:.2f}">{body}</svg>')


def ruler(length=150):
    s = f'<line x1="0" y1="8" x2="{length}" y2="8" stroke="{DARK}" stroke-width="0.25"/>'
    for i in range(length + 1):
        t = 5 if i % 10 == 0 else (3.2 if i % 5 == 0 else 1.8)
        s += f'<line x1="{i}" y1="8" x2="{i}" y2="{8 - t}" stroke="{DARK}" stroke-width="0.2"/>'
        if i % 10 == 0:
            s += f'<text x="{i}" y="1.6" font-size="2.6" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{i}</text>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{length + 6}mm" height="10mm" viewBox="-3 -1 {length + 6} 10">{s}</svg>'
