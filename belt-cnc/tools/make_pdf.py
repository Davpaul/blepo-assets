"""Build the printable step-by-step guide: ../belt-cnc-build-guide.pdf

All hardware drawings are life size. Print at 100% ("actual size"), not "fit to page".

    python3 make_pdf.py
"""
import math, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
REN = os.path.join(ROOT, "renders")
OUT = os.path.join(ROOT, "belt-cnc-build-guide.pdf")
PW, PH = A4[0] / mm, A4[1] / mm
ML, MR, MT, MB = 15, 15, 16, 16
BLUE, GREY, DARK, ORANGE = (0.16, 0.42, 0.68), (0.45, 0.45, 0.45), (0.12, 0.12, 0.12), (0.85, 0.45, 0.1)
STEEL, BRASS = (0.78, 0.8, 0.83), (0.85, 0.72, 0.35)


# ----------------------------------------------------------------------------- life-size hardware
def _rect(c, x, y, w, h, fill=STEEL, r=0):
    c.setFillColorRGB(*fill); c.setStrokeColorRGB(*DARK); c.setLineWidth(0.5)
    if r:
        c.roundRect(x * mm, y * mm, w * mm, h * mm, r * mm, stroke=1, fill=1)
    else:
        c.rect(x * mm, y * mm, w * mm, h * mm, stroke=1, fill=1)


def _poly(c, pts, fill=STEEL):
    c.setFillColorRGB(*fill); c.setStrokeColorRGB(*DARK); c.setLineWidth(0.5)
    p = c.beginPath(); p.moveTo(pts[0][0] * mm, pts[0][1] * mm)
    for (x, y) in pts[1:]:
        p.lineTo(x * mm, y * mm)
    p.close(); c.drawPath(p, stroke=1, fill=1)


def _circ(c, x, y, r, fill=STEEL):
    c.setFillColorRGB(*fill); c.setStrokeColorRGB(*DARK); c.setLineWidth(0.5)
    c.circle(x * mm, y * mm, r * mm, stroke=1, fill=1)


def _hex(c, x, y, af, fill=STEEL):
    R = af / math.sqrt(3)
    _poly(c, [(x + R * math.cos(math.radians(60 * i)), y + R * math.sin(math.radians(60 * i))) for i in range(6)], fill)


def _thread(c, x, y, d, length):
    """Shaft lying along +x from (x, y centre)."""
    _rect(c, x, y - d / 2, length, d)
    c.setLineWidth(0.25); c.setStrokeColorRGB(*GREY)
    n = int(length / 1.0)
    for i in range(1, n):
        c.line((x + i * length / n) * mm, (y - d / 2) * mm, (x + i * length / n - 0.4) * mm, (y + d / 2) * mm)


def screw(kind, d, length, head_d, head_h):
    """Returns (draw(c, x, y_bottom), width, height). Screw lies on its side, head on the left."""
    def draw(c, x, y):
        cy = y + head_d / 2
        if kind == "csk":                       # length includes the head
            _thread(c, x + head_h, cy, d, length - head_h)
            _poly(c, [(x, cy - head_d / 2), (x, cy + head_d / 2), (x + head_h, cy + d / 2), (x + head_h, cy - d / 2)])
        else:
            _thread(c, x + head_h, cy, d, length)
            if kind == "pan":
                _rect(c, x, cy - head_d / 2, head_h, head_d, r=min(head_h * 0.45, 1.0))
            elif kind == "hex":
                _rect(c, x, cy - head_d / 2, head_h, head_d)
                c.setLineWidth(0.3); c.line(x * mm, (cy - head_d / 4) * mm, (x + head_h) * mm, (cy - head_d / 4) * mm)
                c.line(x * mm, (cy + head_d / 4) * mm, (x + head_h) * mm, (cy + head_d / 4) * mm)
            else:                               # cap
                _rect(c, x, cy - head_d / 2, head_h, head_d)
    w = length if kind == "csk" else length + head_h
    return draw, w, head_d


def nut(af, h, nyloc=False):
    def draw(c, x, y):
        _hex(c, x + af * 0.58, y + af / 2, af)
        _circ(c, x + af * 0.58, y + af / 2, af * 0.3, (1, 1, 1))
        sx = x + af * 1.16 + 3
        _rect(c, sx, y, h, af)
        if nyloc:
            _rect(c, sx + h * 0.68, y + af * 0.1, h * 0.32, af * 0.8, (0.3, 0.5, 0.85))
    return draw, af * 1.16 + 3 + h, af


def washer(od, hole, t=1.0):
    def draw(c, x, y):
        _circ(c, x + od / 2, y + od / 2, od / 2); _circ(c, x + od / 2, y + od / 2, hole / 2, (1, 1, 1))
    return draw, od, od


def ring(od, hole, width, fill=STEEL):
    """Bearing-like part: end view plus side view."""
    def draw(c, x, y):
        _circ(c, x + od / 2, y + od / 2, od / 2, fill); _circ(c, x + od / 2, y + od / 2, hole / 2, (1, 1, 1))
        _rect(c, x + od + 3, y, width, od, fill)
    return draw, od + 3 + width, od


def pulley(c, x, y):
    cy = y + 9
    _rect(c, x, cy - 8, 7.5, 16); _rect(c, x + 7.5, cy - 9, 1, 18); _rect(c, x + 8.5, cy - 6.1, 7, 12.2, (0.65, 0.67, 0.7))
    _rect(c, x + 15.5, cy - 9, 1, 18)
    c.setLineWidth(0.25)
    for i in range(1, 7):
        c.line((x + 8.5) * mm, (cy - 6.1 + i * 12.2 / 7) * mm, (x + 15.5) * mm, (cy - 6.1 + i * 12.2 / 7) * mm)
    _circ(c, x + 3.5, cy, 1.4, DARK)


def idler(c, x, y):
    cy = y + 9
    _rect(c, x, cy - 9, 1, 18); _rect(c, x + 1, cy - 6, 7, 12); _rect(c, x + 8, cy - 9, 1, 18)
    _circ(c, x + 9 + 3 + 9, cy, 9); _circ(c, x + 9 + 3 + 9, cy, 6, (0.9, 0.9, 0.92)); _circ(c, x + 21, cy, 2.5, (1, 1, 1))


def n20(c, x, y):
    _rect(c, x, y + 4.5, 10, 3); _rect(c, x + 10, y, 9, 12, BRASS); _rect(c, x + 19, y + 1, 25, 10, (0.7, 0.7, 0.72), r=1)


def tnut(c, x, y):
    _circ(c, x + 9.5, y + 9.5, 9.5); _circ(c, x + 9.5, y + 9.5, 3, (1, 1, 1))
    _rect(c, x + 22, y, 1.5, 19); _rect(c, x + 23.5, y + 5.5, 9, 8)


def wingnut(c, x, y):
    _rect(c, x + 8, y, 8, 6)
    _poly(c, [(x + 8, y + 3), (x, y + 13), (x + 5, y + 14), (x + 10, y + 6)])
    _poly(c, [(x + 16, y + 3), (x + 24, y + 13), (x + 19, y + 14), (x + 14, y + 6)])


def switch(c, x, y):
    _rect(c, x, y + 3, 20, 10, (0.2, 0.2, 0.22), r=0.5)
    _circ(c, x + 5.25, y + 6, 1.2, (1, 1, 1)); _circ(c, x + 14.75, y + 6, 1.2, (1, 1, 1))
    c.setStrokeColorRGB(*DARK); c.setLineWidth(0.8); c.line((x + 2) * mm, (y + 13.2) * mm, (x + 19) * mm, (y + 16) * mm)
    for i in (2, 10, 18):
        _rect(c, x + i - 0.6, y, 1.2, 3, BRASS)


def resistor(c, x, y):
    c.setStrokeColorRGB(*GREY); c.setLineWidth(0.8); c.line(x * mm, (y + 5) * mm, (x + 42) * mm, (y + 5) * mm)
    _rect(c, x + 10, y, 22, 10, (0.93, 0.92, 0.88))


def belt(c, x, y):
    _rect(c, x, y, 50, 6, (0.15, 0.15, 0.15))
    c.setStrokeColorRGB(0.6, 0.6, 0.6); c.setLineWidth(0.5)
    for i in range(1, 25):
        c.line((x + i * 2) * mm, y * mm, (x + i * 2) * mm, (y + 6) * mm)


def rj45(c, x, y):
    """RJ45 breakout board: socket plus a row of eight screw terminals. Sizes vary by seller."""
    _rect(c, x, y, 36, 30, (0.1, 0.45, 0.25), r=1)
    _rect(c, x + 10, y + 12, 16, 16, (0.75, 0.75, 0.78)); _rect(c, x + 12.2, y + 20, 11.6, 8, (0.15, 0.15, 0.17))
    for i in range(8):
        _rect(c, x + 2.5 + i * 3.9, y + 2, 3.5, 7, (0.25, 0.55, 0.85)); _circ(c, x + 4.25 + i * 3.9, y + 5.5, 1.1, STEEL)


def wago(c, x, y):
    _rect(c, x, y, 13, 18, (0.92, 0.92, 0.9), r=1)
    _rect(c, x + 1.5, y + 11, 4.5, 6.5, ORANGE); _rect(c, x + 7, y + 11, 4.5, 6.5, ORANGE)


def rod(length, d, threaded=False):
    def draw(c, x, y):
        if threaded:
            _thread(c, x, y + d / 2, d, length)
        else:
            _rect(c, x, y, length, d)
    return draw, length, d


def simple(fn, w, h):
    return fn, w, h


HW = {
    "m3x8":   ("M3 x 8 cap screw", screw("cap", 3, 8, 5.5, 3)),
    "m3x10":  ("M3 x 10 cap screw", screw("cap", 3, 10, 5.5, 3)),
    "m3x12":  ("M3 x 12 pan head", screw("pan", 3, 12, 5.6, 2.4)),
    "m2x10":  ("M2 x 10 self-tapper", screw("pan", 2, 10, 3.8, 1.5)),
    "m5x25":  ("M5 x 25 hex bolt", screw("hex", 5, 25, 8, 3.5)),
    "m5x30":  ("M5 x 30 hex bolt", screw("hex", 5, 30, 8, 3.5)),
    "m5x40":  ("M5 x 40 hex bolt", screw("hex", 5, 40, 8, 3.5)),
    "m5csk":  ("M5 x 30 countersunk", screw("csk", 5, 30, 9.2, 2.8)),
    "m6x40":  ("M6 x 40 hex bolt", screw("hex", 6, 40, 10, 4)),
    "m3nut":  ("M3 nut", nut(5.5, 2.4)),
    "m5nut":  ("M5 plain nut", nut(8, 4)),
    "m5nyl":  ("M5 nyloc nut (blue ring)", nut(8, 5, True)),
    "m5wash": ("M5 washer", washer(10, 5.3)),
    "m6wash": ("M6 penny washer", washer(25, 6.4)),
    "wing":   ("M6 wing nut", simple(wingnut, 24, 14)),
    "tnut":   ("M6 T-nut", simple(tnut, 32.5, 19)),
    "625":    ("625ZZ bearing 5 x 16 x 5", ring(16, 5, 5)),
    "lm8uu":  ("LM8UU bearing 8 x 15 x 24", ring(15, 8, 24)),
    "pulley": ("GT2 20-tooth pulley", simple(pulley, 16.5, 18)),
    "idler":  ("Smooth idler, 5mm bore", simple(idler, 30, 18)),
    "tnutT8": ("T8 brass nut", ring(22, 8, 15, BRASS)),
    "coupler": ("Shaft coupler 5 to 8mm", ring(19, 5, 25, (0.8, 0.8, 0.82))),
    "rod":    ("8mm rod, 150 long", rod(150, 8)),
    "screw":  ("T8 lead screw cut to 115", rod(115, 8, True)),
    "n20":    ("N20 geared motor", simple(n20, 44, 12)),
    "switch": ("Microswitch", simple(switch, 20, 16)),
    "res":    ("120 ohm 5W resistor", simple(resistor, 42, 10)),
    "belt":   ("GT2 belt, 6 wide, teeth every 2mm", simple(belt, 50, 6)),
    "rj45":   ("RJ45 breakout board (size varies)", simple(rj45, 36, 30)),
    "wago":   ("Lever connector", simple(wago, 13, 18)),
}


# ----------------------------------------------------------------------------- page layout
class Doc:
    def __init__(self, path):
        self.c = canvas.Canvas(path, pagesize=A4)
        self.c.setTitle("Belt CNC build guide"); self.c.setAuthor("belt-cnc")
        self.page = 0
        self.y = PH - MT
        self._start()

    def _start(self):
        self.page += 1
        c = self.c
        c.setFont("Helvetica", 7.5); c.setFillColorRGB(*GREY)
        c.drawString(ML * mm, 8 * mm, "Belt CNC build guide. Print at 100% (actual size): hardware drawings are life size.")
        c.drawRightString((PW - MR) * mm, 8 * mm, f"page {self.page}")
        self.y = PH - MT

    def newpage(self):
        self.c.showPage(); self._start()

    def need(self, h):
        if self.y - h < MB:
            self.newpage()

    def gap(self, h=3):
        self.y -= h

    def text(self, s, size=10, font="Helvetica", color=DARK, indent=0, lead=None, width=None):
        lead = lead or size * 0.47
        width = (width or (PW - ML - MR - indent)) * mm
        for para in s.split("\n"):
            lines = simpleSplit(para, font, size, width) or [""]
            for ln in lines:
                self.need(lead)
                self.y -= lead
                self.c.setFont(font, size); self.c.setFillColorRGB(*color)
                self.c.drawString((ML + indent) * mm, self.y * mm, ln)
        self.y -= 1.2

    def h1(self, s):
        self.need(30)
        self.y -= 4
        self.text(s, 17, "Helvetica-Bold", BLUE, lead=8)
        self.c.setStrokeColorRGB(*BLUE); self.c.setLineWidth(1)
        self.c.line(ML * mm, (self.y - 0.5) * mm, (PW - MR) * mm, (self.y - 0.5) * mm)
        self.y -= 4

    def h2(self, s):
        self.need(70)
        self.y -= 2.5
        self.text(s, 12, "Helvetica-Bold", DARK, lead=6)

    def p(self, s):
        self.text(s, 10)

    def bullets(self, items):
        for it in items:
            lines = simpleSplit(it, "Helvetica", 10, (PW - ML - MR - 5) * mm)
            self.need(4.7 * len(lines))
            self.c.setFillColorRGB(*DARK); self.c.circle((ML + 1.6) * mm, (self.y - 3.3) * mm, 0.6 * mm, stroke=0, fill=1)
            self.text(it, 10, indent=5)

    def step(self, n, s):
        lines = simpleSplit(s, "Helvetica", 10, (PW - ML - MR - 9) * mm)
        self.need(4.7 * len(lines) + 2)
        self.c.setFillColorRGB(*BLUE); self.c.circle((ML + 3) * mm, (self.y - 3.1) * mm, 3 * mm, stroke=0, fill=1)
        self.c.setFillColorRGB(1, 1, 1); self.c.setFont("Helvetica-Bold", 9)
        self.c.drawCentredString((ML + 3) * mm, (self.y - 4.2) * mm, str(n))
        self.text(s, 10, indent=9)
        self.y -= 1

    def note(self, s, color=ORANGE, label="Tip"):
        lines = simpleSplit(s, "Helvetica", 9.5, (PW - ML - MR - 8) * mm)
        h = 4.5 * len(lines) + 9
        self.need(h + 2)
        self.c.setStrokeColorRGB(*color); self.c.setFillColorRGB(1, 0.97, 0.93); self.c.setLineWidth(0.8)
        self.c.roundRect(ML * mm, (self.y - h) * mm, (PW - ML - MR) * mm, h * mm, 2 * mm, stroke=1, fill=1)
        y0 = self.y
        self.y -= 1.5
        self.text(label, 9, "Helvetica-Bold", color, indent=4)
        self.text(s, 9.5, indent=4, lead=4.5, width=PW - ML - MR - 8)
        self.y = y0 - h - 3

    def image(self, name, width=180, max_h=110):
        path = os.path.join(REN, name)
        if name.startswith("step_") or name.startswith("assembly_"):
            # the 3D renders have wide white borders: trim them so the picture fills the space
            from PIL import Image, ImageChops
            im = Image.open(path).convert("RGB")
            box_ = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
            if box_:
                im = im.crop((max(box_[0] - 15, 0), max(box_[1] - 15, 0), min(box_[2] + 15, im.size[0]), min(box_[3] + 15, im.size[1])))
            img = ImageReader(im)
        else:
            img = ImageReader(path)
        iw, ih = img.getSize()
        w = width; h = w * ih / iw
        if h > max_h:
            h = max_h; w = h * iw / ih
        self.need(h + 3)
        self.c.drawImage(img, (ML + (PW - ML - MR - w) / 2) * mm, (self.y - h) * mm, w * mm, h * mm, mask="auto")
        self.y -= h + 3

    def hardware(self, items, title="You need (life size):"):
        """items: list of (key, qty). Drawn life size in a box, wrapping onto rows."""
        rows, row, x = [], [], 0
        avail = PW - ML - MR - 8
        for key, qty in items:
            label, (fn, w, h) = HW[key]
            cap = f"{qty} x {label}" if qty else label
            cw = max(w, self.c.stringWidth(cap, "Helvetica", 7.5) / mm) + 7
            if x + cw > avail and row:
                rows.append(row); row, x = [], 0
            row.append((fn, w, h, cap, cw)); x += cw
        rows.append(row)
        total = sum(max(r_[2] for r_ in r) + 9 for r in rows) + 9
        self.need(total + 2)
        self.c.setStrokeColorRGB(*GREY); self.c.setFillColorRGB(0.97, 0.97, 0.98); self.c.setLineWidth(0.5)
        self.c.roundRect(ML * mm, (self.y - total) * mm, (PW - ML - MR) * mm, total * mm, 2 * mm, stroke=1, fill=1)
        self.c.setFont("Helvetica-Bold", 8.5); self.c.setFillColorRGB(*GREY)
        self.c.drawString((ML + 4) * mm, (self.y - 5) * mm, title)
        y = self.y - 8
        for r in rows:
            rh = max(i[2] for i in r)
            x = ML + 4
            for fn, w, h, cap, cw in r:
                fn(self.c, x, y - rh + (rh - h) / 2)
                self.c.setFont("Helvetica", 7.5); self.c.setFillColorRGB(*DARK)
                self.c.drawString(x * mm, (y - rh - 3.5) * mm, cap)
                x += cw
            y -= rh + 9
        self.y -= total + 3

    def table(self, rows, widths, header=True, size=9):
        total = 0
        for ri, row in enumerate(rows):
            fnt = "Helvetica-Bold" if (header and ri == 0) else "Helvetica"
            total += max(len(simpleSplit(str(t), fnt, size, (w - 3) * mm)) for t, w in zip(row, widths)) * size * 0.45 + 3
        if total < PH - MT - MB - 10:
            self.need(total)                       # keep the whole table on one page
        for ri, row in enumerate(rows):
            cells = [simpleSplit(str(t), "Helvetica-Bold" if (header and ri == 0) else "Helvetica", size, (w - 3) * mm) for t, w in zip(row, widths)]
            h = max(len(cl) for cl in cells) * size * 0.45 + 3
            self.need(h)
            x = ML
            for cl, w in zip(cells, widths):
                if header and ri == 0:
                    self.c.setFillColorRGB(0.88, 0.92, 0.97)
                else:
                    self.c.setFillColorRGB(1, 1, 1)
                self.c.setStrokeColorRGB(0.7, 0.7, 0.7); self.c.setLineWidth(0.3)
                self.c.rect(x * mm, (self.y - h) * mm, w * mm, h * mm, stroke=1, fill=1)
                self.c.setFillColorRGB(*DARK); self.c.setFont("Helvetica-Bold" if (header and ri == 0) else "Helvetica", size)
                for li, ln in enumerate(cl):
                    self.c.drawString((x + 1.5) * mm, (self.y - 1.2 - (li + 1) * size * 0.45) * mm, ln)
                x += w
            self.y -= h
        self.y -= 3

    def ruler(self):
        self.need(26)
        c, x, y = self.c, ML + 10, self.y - 14
        c.setStrokeColorRGB(*DARK); c.setLineWidth(0.6)
        c.line(x * mm, y * mm, (x + 150) * mm, y * mm)
        for i in range(0, 151):
            t = 5 if i % 10 == 0 else (3.2 if i % 5 == 0 else 1.8)
            c.line((x + i) * mm, y * mm, (x + i) * mm, (y + t) * mm)
            if i % 10 == 0:
                c.setFont("Helvetica", 7); c.setFillColorRGB(*DARK); c.drawCentredString((x + i) * mm, (y + 6) * mm, str(i))
        c.setFont("Helvetica", 8); c.drawString(x * mm, (y - 5) * mm, "Millimetres. Hold a ruler against this: 150 here must be 150 on your ruler.")
        self.y -= 26

    def save(self):
        self.c.save()


# ----------------------------------------------------------------------------- content
def build():
    d = Doc(OUT)

    # ---- cover
    d.y -= 6
    d.text("Belt CNC", 30, "Helvetica-Bold", BLUE, lead=13)
    d.text("Step-by-step build guide", 15, color=GREY, lead=8)
    d.gap(4)
    d.image("layout.png", 180, 95)
    d.p("A full-sheet CNC router that packs away. A stepper motor at each corner of the table pulls a small sled around on "
        "toothed belts. The sled carries a trim router, a pen or a laser. Spare belt winds onto a reel at each corner.")
    d.note("This design has not been built yet. It has been checked on a computer for parts clashing and for the maths, but "
           "expect to adjust things as you go. Build and test ONE corner unit before printing all four. The last page lists "
           "what has and has not been checked.", label="Read this first")
    d.h2("How to use this guide")
    d.bullets(["Print it at 100% (\"actual size\"), not \"fit to page\". Check with the ruler on the next page.",
               "Each step shows the screws and parts it uses, drawn life size. Lay yours on the drawing to pick the right one.",
               "Do the steps in order. Sections 1 to 4 are mechanical, 5 is wiring, 6 to 10 are setting up and using it.",
               "The same information, plus the scripts and printable files, is in the project folder: BUILD.md, WIRING.md, PARTS.md."])

    # ---- scale check and hardware sheet
    d.newpage()
    d.h1("Check the print scale")
    d.ruler()
    d.h1("Hardware, life size")
    d.p("Everything below is drawn at its true size. Sort your fasteners into pots using this page before you start. "
        "Screw length is measured from under the head, except countersunk screws, which are measured overall.")
    d.hardware([("m3x8", 20), ("m3x10", 4), ("m3x12", 30), ("m2x10", 2), ("m3nut", 4)], "Small screws")
    d.hardware([("m5x25", 4), ("m5x30", 6), ("m5x40", 4), ("m5csk", 4), ("m6x40", 12)], "Bolts")
    d.hardware([("m5nyl", 12), ("m5nut", 4), ("m5wash", 10), ("m6wash", 12), ("wing", 12), ("tnut", 12)], "Nuts and washers")
    d.hardware([("625", 4), ("lm8uu", 4), ("pulley", 4), ("idler", 4), ("tnutT8", 1), ("coupler", 1)], "Bearings and drive parts")
    d.hardware([("rod", 2), ("screw", 1)], "Z axis shafts")
    d.hardware([("n20", 4), ("switch", 1), ("res", 2), ("rj45", 10), ("wago", 6), ("belt", 0)], "Electrical parts and belt")

    # ---- tools, safety
    d.newpage()
    d.h1("Before you start")
    d.h2("Tools")
    d.bullets(["Hex keys 1.5 to 4mm, small screwdrivers, 8mm and 10mm spanners",
               "Hacksaw and a round file", "Drill with 3mm and 8mm bits", "Tape measure, pencil, string",
               "Small flat screwdriver (2 to 2.5mm), wire strippers, side cutters",
               "Multimeter with a continuity beep", "A laptop with Python 3 for the setup scripts"])
    d.h2("Safety")
    d.bullets(["The router is a mains tool spinning at 30,000 rpm. Wear eye and ear protection. Keep hands off the table while it runs.",
               "Plug the router and the power supply into one switched extension lead within arm's reach. That switch is your emergency stop.",
               "Never leave the machine cutting unattended.",
               "Never plug or unplug a lead with the power on. It can destroy that motor's driver.",
               "Never plug the machine's network leads into a computer or router. They carry 24V motor current. Label them CNC ONLY.",
               "The donor printer's heated bed is mains powered. Unplug the printer and wait 10 minutes before opening it. Do not reuse the bed.",
               "A laser on an open table can blind. Wear glasses rated for its wavelength and keep other people out of the room."])
    d.h2("Tips for a first build")
    d.bullets(["Lay out the parts for each step before starting it.",
               "Screws going into plastic: stop as soon as they feel snug. Overtightening strips the hole.",
               "A nyloc nut has a plastic ring and stays where you leave it. \"Tighten until it still spins\" means exactly that.",
               "If a printed hole is tight, twist a drill bit through it by hand.",
               "Naming: stand at one long edge of the table. That edge is SOUTH. The corner on your left is south-west (SW). "
               "X runs left to right, Y runs away from you."])

    d.newpage()
    d.h1("1. Print the parts")
    d.h2("Which filament")
    d.p("Plain PETG for every part. It is strong, slightly flexible so clamps and press fits do not crack, and it copes with a warm "
        "motor. PLA is stiffer but brittle and creeps under a clamped load, so the router clamp would work loose. "
        "ABS and ASA are strong but warp on large flat parts such as the sled base.")
    d.table([["Setting", "Value"], ["Nozzle / bed", "235 to 245 C / 75 to 80 C"], ["Layer height", "0.2mm, 0.4mm nozzle"],
             ["Walls", "4 (5 for corner brackets and the Z carriage)"], ["Infill", "40% (50% for corner brackets and the Z carriage)"],
             ["Supports", "None needed"], ["Fan", "30 to 50%"], ["Amount", "About 1.5kg for a full set. Buy 2kg, or 3kg to allow for reprints."]], [45, 135])
    d.h2("What to print")
    d.p("Print everything before you take the printer apart, plus one spare of each small spacer. The files in the stl folder are "
        "already turned the right way up.")
    d.table([["File", "Qty", "Notes"],
             ["corner_bracket", "4", "142 x 176mm. Top face on the bed, fence walls pointing up. 5 walls, 50% infill."],
             ["reel_body, reel_flange", "4 each", "Reel body prints with its big flange on the bed."],
             ["n20_cup", "4", "Holds the reel motor."],
             ["f_spacer, f_sleeve, k_spacer", "4 each", "Small parts for the posts. Print spares."],
             ["measuring_cap", "2", ""],
             ["sled_base", "1", "220 x 220mm. Use a brim."],
             ["z_carriage", "1", "Holds the router. 5 walls, 50% infill."],
             ["z_bridge", "1", "Top face on the bed."],
             ["dust_shoe", "1", "Bridges 34mm with no support."],
             ["pen_caddy_body, pen_slider", "1 each", "Slider must drop freely through the body."],
             ["thumb_knob", "4", ""],
             ["laser_caddy, laser_shim", "1 / as needed", "Only for a laser."],
             ["riser_shim", "as needed", "See section 7."],
             ["electronics_tray, electronics_lid", "1 each", "225 x 155mm."]], [58, 24, 98])
    d.note("Test fits as you print: a 65mm router body slides into z_carriage with the clamp open; f_sleeve spins on an M5 bolt; "
           "an 8mm rod pushes snugly into the sockets of sled_base and z_bridge. If a fit is wrong, reprint now while you still have a printer.")

    d.h1("2. Strip the printer")
    d.p("Keep: all five stepper motors with their leads, the 24V power supply, both lead screws with brass nuts, both shaft couplers, "
        "the two 20-tooth pulleys from the X and Y motors, a 24V fan, and every screw.")
    d.step(1, "Label the motors. Use the four most alike for the corners and the fifth for Z.")
    d.step(2, "Cut one lead screw to 115mm with a hacksaw and file the cut end smooth. Check it against the life-size drawing on the hardware page.")
    d.note("The main board, touch screen and hot end are not reused. I worked from memory of this printer model, so check what you find against this list.")

    # ---- corner units
    d.newpage()
    d.h1("3. Build the four corner units")
    d.p("All four are identical. Build one completely first, test it (section 9, step 1), then build the other three.")
    d.h2("3a. Bolts and motor")
    d.hardware([("m5x30", 1), ("m5x25", 1), ("m3x8", 4)], "For each corner unit:")
    d.image("step_corner_1.png", 170, 62)
    d.step(1, "Turn the bracket upside down. Push the M5 x 30 bolt through the hole that sits on its own near the outer edge. "
              "Push the M5 x 25 bolt through the hole right beside the big round motor hole. Each head drops into a six-sided pocket.")
    d.step(2, "Hold a stepper motor against the underside with its shaft through the big hole and its lead pointing away from the "
              "fence walls. The motor covers both bolt heads so they cannot fall out.")
    d.step(3, "Turn it right way up. Fix the motor with four M3 x 8 screws from the top. Their heads sit down in the round recesses.")
    d.image("step_corner_2.png", 170, 62)

    d.h2("3b. Posts, bearing and pulley")
    d.hardware([("m5nyl", 2), ("m5wash", 1), ("625", 1), ("pulley", 1)], "For each corner unit, plus f_spacer, f_sleeve and k_spacer:")
    d.image("step_corner_3.png", 170, 70)
    d.step(4, "Outer bolt (the belt-end post): slide on f_spacer (the fatter one), then f_sleeve, then a washer and a nyloc nut. "
              "Tighten until the sleeve still turns freely. About 6mm of thread should show above the nut.")
    d.step(5, "Bolt beside the motor (the pinch post): slide on k_spacer with its small lip upward, then a 625 bearing, then a nyloc "
              "nut with NO washer. The bearing must spin.")
    d.step(6, "Push a 20-tooth pulley onto the motor shaft, grub-screw end down, leaving a gap the thickness of a business card under it. "
              "Its teeth should be level with the bearing. Tighten one grub screw onto the flat on the shaft, then the other.")
    d.step(7, "Check the gap. Slide a scrap of belt, teeth against the pulley, between pulley and bearing. It should pass with light "
              "drag. If it jams, ease the bolt hole with a round file. If the belt can lift clear of the teeth, the gap is too wide: reprint that bracket.")

    d.h2("3c. Reel")
    d.hardware([("n20", 1), ("m3x12", 5)], "For each corner unit, plus n20_cup, reel_body and reel_flange:")
    d.image("step_corner_4.png", 170, 66)
    d.step(8, "Push the N20 motor up into the small rectangular pocket under the bracket so its shaft comes up through the hole. "
              "Slide n20_cup over it and fix with two M3 x 12 screws. The wires come out through the slot.")
    d.step(9, "Screw reel_flange (the plain disc) to the hub of reel_body with three M3 x 12 screws.")
    d.step(10, "Push the reel onto the motor's D-shaped shaft, flat to flat. It should turn level, clear of the bracket.")
    d.step(11, "The panel that hangs down, with the grid of holes, takes a network breakout board. That is fitted and wired in section 5.")

    # ---- sled
    d.newpage()
    d.h1("4. Build the sled")
    d.h2("4a. Idlers")
    d.hardware([("m5csk", 4), ("idler", 4), ("m5nyl", 4)])
    d.image("step_sled_1.png", 170, 62)
    d.step(1, "Push four M5 x 30 countersunk bolts up through the four holes near the middle of the sled base. The heads must sit below the underside.")
    d.step(2, "On each, drop a smooth idler onto the raised boss and add a nyloc nut. The idlers must spin.")
    d.note("The front of the sled is the side with the two small screw holes near the edge. The dust shoe goes there.", label="Which way round")

    d.h2("4b. Rods and carriage")
    d.hardware([("rod", 2), ("lm8uu", 4), ("tnutT8", 1), ("m3x10", 4), ("m3nut", 4), ("m3x12", 6)])
    d.image("step_sled_2.png", 170, 66)
    d.step(3, "Press two LM8UU bearings into each side tube of z_carriage from the top. Nip each with an M3 x 12 screw in the side hole. Just snug: do not crush them.")
    d.step(4, "Bolt the brass nut to the flat tab at the back of the carriage, flange on top, with four M3 x 10 screws and nuts.")
    d.step(5, "Push the two 8mm rods into the tall sockets on the base, all the way down. Fix each with an M3 x 12 screw in the side hole.")
    d.step(6, "Slide the carriage down onto the rods: clamp slot to the front, brass nut to the back. It should glide by hand.")

    d.h2("4c. Bridge and Z motor")
    d.hardware([("m3x8", 4), ("coupler", 1), ("screw", 1), ("switch", 1), ("m2x10", 2), ("m3x12", 2)])
    d.image("step_sled_3.png", 170, 70)
    d.step(7, "Sit the fifth stepper on top of z_bridge with its shaft pointing down through the round hole. Fix with four M3 x 8 screws from underneath.")
    d.step(8, "Fit the coupler to the motor shaft and the cut lead screw into the coupler. Tighten both clamp screws.")
    d.step(9, "Screw the microswitch to the small tab under the bridge with two M2 screws, on the face that points to the front, lever downward.")
    d.step(10, "Lower the bridge onto the rod tops while turning the lead screw by hand so it winds into the brass nut. Fix the bridge with an M3 x 12 screw in each side hole.")

    d.h2("4d. Dust shoe and router")
    d.hardware([("m3x12", 2), ("m5x30", 2), ("m5nut", 2)])
    d.image("step_sled_4.png", 170, 70)
    d.step(11, "Screw dust_shoe to the front of the base with two M3 x 12 screws. Take it off for pen and laser work.")
    d.step(12, "Slide the router body into the ring. Fit the two M5 x 30 clamp bolts with their nuts in the six-sided pockets and tighten evenly.")

    # ---- wiring
    d.newpage()
    d.h1("5. Wiring")
    d.image("wiring_overview.png", 180, 105)
    d.p("One main board in a tray drives five motors. Each corner unit joins the tray by an ordinary network lead, and the sled has a fifth. "
        "At each end of every lead is a small breakout board: a network socket with eight numbered screw terminals. Every wire goes under a screw, "
        "so there is almost no soldering. Everything you wire is 24V or less and cannot shock you. Never open the power supply.")
    d.hardware([("rj45", 10), ("wago", 6), ("res", 2)], "Wiring parts (life size; breakout boards vary by seller):")
    d.h2("How to put a wire in a screw terminal")
    d.step(1, "Strip 6mm of insulation and twist the strands tightly so none stray.")
    d.step(2, "Undo the terminal screw, push the bare end fully in so no copper shows outside, and tighten firmly.")
    d.step(3, "Tug the wire. It must not pull out. Thin wires hold better folded double.")
    d.note("One stray strand touching the next terminal causes faults that are miserable to find. Look closely at each one. Do one board completely, test it, then do the next.")
    d.image("wiring_pinout.png", 180, 86)
    d.note("The second pair goes on terminals 3 and 6, not 3 and 4. That matches how the wires are twisted together inside a network lead.", label="Watch out")
    d.h2("Finding a stepper's wire pairs")
    d.p("A stepper has four wires that make two pairs. Set the multimeter to the continuity beep. Touch one probe to any wire and try the "
        "other three: the one that beeps is its partner. The remaining two are the other pair. Colours are not reliable. "
        "It does not matter which pair goes on 1 and 2.")
    d.h2("The leads")
    d.bullets(["Corners: any network lead that reaches, about 2m for the near corners and 4m for the far ones.",
               "Sled: about 3m, and it must be a flexible patch lead, because it moves all day. Stiff wall cable will break.",
               "Check each is \"straight\": hold both plugs side by side, clips down. The colour order must be identical. Do not use crossover leads.",
               "Label both ends: SW, SE, NE, NW, SLED, and CNC ONLY."])
    d.h2("5a. Corner units")
    d.step(1, "Fix a breakout board to the panel with the grid of holes, socket pointing down or outward. Use M3 screws through the board's own holes if they line up, or a sticky foam pad plus two zip ties through the grid.")
    d.step(2, "Cut the stepper's lead so about 150mm stays on the motor. Keep the off-cut with its plug for the tray.")
    d.step(3, "Find the pairs. One pair into terminals 1 and 2, the other into 3 and 6.")
    d.step(4, "The reel motor's two wires into terminals 4 and 5. Zip-tie loose wires to the bracket so nothing tugs on a terminal.")
    d.h2("5b. Sled")
    d.step(5, "Fix a breakout board on top of the bridge beside the Z motor, using the grid of small holes there.")
    d.step(6, "Z motor: one pair into terminals 1 and 2, the other into 3 and 6. Z switch: its two wires into terminals 4 and 5.")
    d.h2("5c. Tray")
    d.step(7, "Fix the main board in the tray on M3 standoffs. Press in the five drivers, matching the labels on driver and board. A driver fitted backwards is destroyed at switch-on.")
    d.step(8, "Stick five breakout boards along the notched wall, one behind each notch. Label them X (SW), Y (SE), E0 (NE), E1 (NW), Z (SLED).")
    d.step(9, "Plug each motor off-cut into the main board output of that name. Find its pairs and put them into terminals 1 and 2, and 3 and 6, of the matching breakout board.")
    d.step(10, "Sled board terminals 4 and 5 go to the Z- endstop connector: one to the pin marked S, one to the pin marked G.")
    d.image("wiring_reels.png", 180, 72)
    d.step(11, "Wire the reel motors as shown: two chains, each with one 120 ohm resistor, both across the HE0 screw terminals. Join wire to resistor leg with a lever connector. Stand the resistors clear of plastic. They get warm.")
    d.step(12, "Power: supply V+ to board +, supply V- to board -, in thick wire. Check it twice. Reversed power kills the board.")
    d.step(13, "Set each driver for 16 microsteps (jumper table in the board manual) and about 1A of motor current (the driver's leaflet gives the voltage to set on its small screw).")
    d.h2("5d. Test before switching on")
    d.bullets(["Each lead, plugged into a board at both ends: terminal 1 to terminal 1 beeps, and so on for 1 to 6.",
               "Each corner board: terminals 1 and 2 beep, 3 and 6 beep, 2 and 3 do not.",
               "Main board + to main board - does NOT beep.",
               "Then switch on. Lights come on, nothing gets warm in the first minute. If anything smells hot, switch off."])
    d.note("I worked from the main board's published pin list, not from one in hand. The labels printed on your board are the authority for "
           "motor pin order, the endstop connector and the + and - marks. Network cable is thinner than usual for a stepper: after the first long job, "
           "feel the leads. If one is warm, lower that driver's current.", label="Check as you go")

    # ---- firmware
    d.h1("6. Firmware")
    d.step(1, "Install VS Code and its PlatformIO extension on the laptop.")
    d.step(2, "Download the FluidNC source from github.com/bdring/FluidNC.")
    d.step(3, "Copy BeltCNC.h, BeltCNC.cpp and BeltKin.h from the project's firmware folder into FluidNC/src/Kinematics.")
    d.step(4, "In PlatformIO choose the \"wifi\" environment and click Upload, with the board on USB. Then run \"Upload Filesystem Image\" once.")
    d.step(5, "Upload belt-cnc.yaml to the board, send  $Config/Filename=belt-cnc.yaml  and restart. The start-up log should say \"Kinematic system: BeltCNC\".")
    d.note("This module passes a syntax check against the FluidNC source but has not had a full build. If the build fails, see firmware/INSTALL.md.", label="Untested step")

    # ---- table
    d.newpage()
    d.h1("7. Set up the table")
    d.p("Two ways to mount the corner units. Pick by how much of the sheet you need to reach.")
    d.h2("Setup A: units on the sheet's own corners")
    d.p("Quickest and smallest. Reaches about 70% of a full sheet. The router cannot hold position within about 210mm of the middle of "
        "the long edges or 130mm of the middle of the short edges. Lay the sheet on 50mm foam board so the motors hang clear. Leave belt_dz at 0.")
    d.image("reach_on_corners.png", 150, 70)
    d.h2("Setup B: end boards")
    d.p("Reaches about 99% of a full sheet, with a footprint of 2740 x 1620mm. Cut two boards about 300 x 1620mm. Raise them on 2x2 timber. "
        "Lay one under each short end of the sheet, sticking out 150mm past the short edge and 200mm past both long edges. Support the middle "
        "of the sheet at the same height. Corner units go on the outer corners of the end boards. Set belt_dz to the thickness of your sheet.")
    d.image("reach_with_wings.png", 150, 70)
    d.note("The sled needs support under at least half its base. Along an unsupported edge, plan on a 60mm border, or lay offcuts of the "
           "same thickness alongside.")
    d.h2("Fitting the units")
    d.hardware([("m6x40", 3), ("m6wash", 3), ("wing", 3), ("tnut", 3)], "For each corner unit:")
    d.step(1, "Push the bracket's two fence walls hard against both edges of the corner.")
    d.step(2, "Mark the three holes. Drill 8mm. Hammer a T-nut into each from underneath.")
    d.step(3, "Bolt down with M6 bolts, penny washers and wing nuts. The unit now lifts off in seconds. (For a one-off sheet, three wood screws with washers do.)")
    d.h2("Measuring")
    d.step(4, "Put a measuring_cap on two belt-end posts. Hook the tape on the flat face of one and read at the flat face of the other.")
    d.step(5, "Measure five distances to the millimetre: S (SW to SE), E (SE to NE), N (NW to NE), W (SW to NW), and the diagonal D (NW to SE).")
    d.step(6, "On the laptop:  python3 tools/table_config.py S E N W D --write firmware/belt-cnc.yaml  then upload the file again. The table does not need to be square.")
    d.step(7, "Stretch a string between diagonally opposite posts, then the other pair. Mark where they cross. That is the centre mark.")

    # ---- belts
    d.h1("8. Fit the belts")
    d.image("belt_path.png", 150, 112)
    d.hardware([("belt", 0)], "Belt, life size:")
    d.step(1, "Cut four belts. For a full sheet each is 5.6m. The table_config script prints the length for your table.")
    d.step(2, "At one end, fold 40mm back on itself with the teeth meshed and fix with two small zip ties. This loop slips over the f_sleeve.")
    d.step(3, "At the other end, fold 10mm over with one zip tie and slide it down into the slot in the reel hub.")
    d.step(4, "Thread as in the picture: loop on the post, out round the sled idler (smooth side against the idler), back to the pulley on the post side, "
              "round the outside of the pulley (teeth against it), between pulley and pinch bearing, and onto the reel. Wind the spare onto the reel by hand.")
    d.note("All four corners must be threaded the same way round. If one is mirrored, the machine will not position properly.", label="Watch out")

    # ---- first power up
    d.newpage()
    d.h1("9. First power-up")
    d.p("Connect the laptop by USB and run:   pip install pyserial   then   python3 tools/belt_setup.py --port COM5 --config firmware/belt-cnc.yaml   "
        "(on a Mac or Linux the port looks like /dev/ttyUSB0). Type the commands in bold at its prompt.")
    d.step(1, "Directions. With the belts off the sled idlers, type  dirtest . Each corner should pay belt out, then take it back. "
              "If one pulls in first, the script tells you which line to change in the config. Each reel should pull gently in the winding-up direction: if not, swap its two wires.")
    d.step(2, "Centre. Quit the script. Hook the belts over the sled idlers. Put a V-bit or pencil in the sled and stand it on the centre mark, "
              "sled edges parallel to the table edges. Switch the controller off and on, then start the script again.")
    d.step(3, "Snug. Take in belt one corner at a time, for example  sw 5 , until each belt is straight with no sag. Then  all 0.5  once or twice. "
              "Aim for a loosely strung guitar, not a tight one. If the point drifts off the mark, take in a little on the side it needs to move towards.")
    d.step(4, "Test. Type  square 300 800 . The sled traces a square and should come back onto the mark with no belt going slack. Then  square 800 1500 .")
    d.step(5, "Z. Type  homez . The router rises until the switch clicks.")
    d.h2("Packing away")
    d.step(1, "Park the sled on the centre mark. Type  pack  and unhook the belts when asked. Each corner winds its belt onto its reel.")
    d.step(2, "Type  off , switch off at the wall, unplug the five leads, undo the wing nuts and lift the corner units off.")
    d.h2("Setting up again")
    d.step(1, "Bolt the units back on the same corners, plug in, stand the sled on the centre mark and switch on.")
    d.step(2, "Type  stowed  then  unpack . Each belt pays out to the length it needs. Hook them on, then snug and test as above.")

    d.h1("10. Using it")
    d.h2("Pen")
    d.image("step_pen.png", 120, 55)
    d.hardware([("m5x40", 2)], "Plus two thumb_knobs, pressed onto the bolt heads:")
    d.step(1, "Clamp pen_caddy_body in the carriage ring, seated on its lip. Drop pen_slider through it.")
    d.step(2, "Screw the two M5 x 40 bolts into the side of the slider. They cut their own thread. They press the pen into a V and take anything from a pencil to a 20mm marker.")
    d.step(3, "Jog Z down about 15mm from the top, let the pen touch the surface, tighten, and set Z zero. The slider floats, so the pen follows the surface.")
    d.h2("Laser")
    d.image("step_laser.png", 120, 55)
    d.step(1, "Clamp laser_caddy in the ring. Drop the module into the square pocket, packing it with laser_shim if it is under 40mm.")
    d.step(2, "Slide the module up or down to focus, then tighten the two thumb screws. Wire its signal input to pin 2 of the board's EXP1 header.")
    d.h2("Router: first cuts")
    d.table([["Setting", "Start with"], ["Bit", "1/8 inch single-flute upcut"], ["Depth per pass", "1.5mm"], ["Feed", "400 mm/min"],
             ["Plunge", "Ramp in, never straight down"], ["Router speed", "Lowest or second lowest"], ["Tabs", "Yes, so cut parts stay put"]], [45, 135])
    d.p("To set Z zero: jog Z about 15mm down from the top, loosen the clamp, lower the router until the bit touches the wood, tighten, set Z zero. "
        "Make toolpaths in any program that writes plain G-code and send them with FluidNC's built-in web page or Universal Gcode Sender.")
    d.h2("Calibrate once")
    d.p("Run  python3 tools/make_test_pattern.py > dots.gcode , draw the dots with the pen, measure the six distances between them and give them to "
        "tools/calibrate.py. It tells you how much to change steps_per_mm. Belt stretch is the main error, so this gains a lot.")

    d.h1("If something is wrong")
    d.table([["Symptom", "Likely cause"],
             ["A belt goes slack during the square test", "Table measurements off, or a belt threaded the wrong way round"],
             ["Sled does not come back to the mark", "A motor skipped: lower the feed, check that driver's current"],
             ["Squares come out as diamonds", "The diagonal D was measured wrongly"],
             ["Everything slightly too big or small", "Belt scale: run the calibration"],
             ["Belt jumps teeth at a corner", "Pinch gap too wide"],
             ["Motor buzzes but does not turn", "A wire pair is split: recheck the pairs, and that the second pair is on 3 and 6"],
             ["A reel does not wind, or unwinds", "Swap that reel motor's two wires"],
             ["Reels too weak, or loops of slack form", "Fit a lower resistor (82 ohm). If the motors get hot, a higher one"],
             ["Router sinks when powered off", "Park it at the top, or fit a 2mm-lead screw"],
             ["Sled lifts when plunging", "Plunge slower, use an upcut bit, ramp in"]], [70, 110])

    d.h1("What has and has not been checked")
    d.h2("Checked on a computer")
    d.bullets(["Every printed part is one solid, fits a 300mm bed and needs no supports.",
               "No part collides with another part, a motor, a bearing or the router, at both ends of the Z travel.",
               "The firmware's belt maths matches an independent model to within 0.002mm over 400 positions.",
               "The firmware module passes a syntax check against the current FluidNC source.",
               "The reach maps come from a force calculation: 35N per belt from each motor, 15N needed to push the sled."])
    d.h2("Not checked")
    d.bullets(["A full firmware build and a run on a board.",
               "Any fit that depends on your printer or your particular pulleys, idlers and N20 motors. The pinch gap is the tightest.",
               "The reels. The resistor value is an estimate. This is the part most likely to need adjusting.",
               "Accuracy while cutting. Expect about 1mm across a sheet after calibration, better over short distances.",
               "The details of the Sidewinder X1 and of the TinyBee's connectors."])
    d.save()
    return d.page


if __name__ == "__main__":
    n = build()
    print("wrote", OUT, n, "pages")
