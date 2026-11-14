"""Draw the wiring diagrams used in WIRING.md."""
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "renders")


def boxp(ax, x, y, w, h, text, fc="#dfe9f5", ec="#3b78b5", fs=10):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def wire(ax, pts, color="#333", lw=2, ls="-"):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, solid_capstyle="round")


def overview():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=120)
    boxp(ax, 0.3, 6.6, 2.6, 0.9, "Switched extension lead\n(your emergency stop)", "#fde3c8", "#c8742a")
    boxp(ax, 0.3, 4.9, 2.6, 0.9, "24V power supply\n(from the printer)", "#fde3c8", "#c8742a")
    boxp(ax, 0.3, 3.2, 2.6, 0.9, "Router\n(its own mains plug)", "#fde3c8", "#c8742a")
    wire(ax, [(1.6, 6.6), (1.6, 5.8)], "#c0392b", 3); wire(ax, [(0.15, 7.05), (0.15, 3.65), (0.3, 3.65)], "#c0392b", 3); wire(ax, [(0.15, 7.05), (0.3, 7.05)], "#c0392b", 3)
    ax.text(1.75, 6.15, "mains", color="#c0392b", fontsize=9)
    # tray
    ax.add_patch(FancyBboxPatch((3.9, 1.0), 4.4, 6.6, boxstyle="round,pad=0.02,rounding_size=0.15", fc="#f4f4f4", ec="#777", lw=1.5, ls="--"))
    ax.text(6.1, 7.35, "ELECTRONICS TRAY", ha="center", fontsize=11, color="#555")
    boxp(ax, 4.2, 2.0, 2.2, 4.9, "", "#e4f3e1", "#3d8b37")
    ax.text(5.3, 6.65, "MKS TinyBee", ha="center", fontsize=10, color="#2c6a27")
    wire(ax, [(2.9, 5.35), (4.2, 5.35)], "#c0392b", 3); ax.text(3.0, 5.5, "24V + and -", fontsize=9, color="#c0392b")
    rows = [("X", 5.9, "SW corner"), ("Y", 5.2, "SE corner"), ("E0", 4.5, "NE corner"), ("E1", 3.8, "NW corner"), ("Z", 3.1, "Sled")]
    for name, y, dest in rows:
        boxp(ax, 5.25, y - 0.2, 1.0, 0.4, name + " driver", "#ffffff", "#3d8b37", 8.5)
        ax.add_patch(Circle((7.9, y), 0.2, fc="#bbb", ec="#333"))
        wire(ax, [(6.25, y), (7.7, y)], "#1f6fb5", 2.2)
        wire(ax, [(8.1, y), (9.6, y)], "#111", 4)
        boxp(ax, 9.6, y - 0.3, 3.0, 0.6, "", "#dfe9f5")
        if dest == "Sled":
            ax.text(11.1, y, "Sled: Z motor + Z switch", ha="center", va="center", fontsize=9.5)
        else:
            ax.text(11.1, y, dest + ": stepper + reel motor", ha="center", va="center", fontsize=9.5)
    ax.text(7.0, 6.2, "4 wires", fontsize=8, color="#1f6fb5", ha="center"); ax.text(8.85, 6.2, "6-core lead", fontsize=8.5, ha="center")
    ax.text(7.9, 6.45, "GX16-6\nsockets", fontsize=8, ha="center", color="#333")
    boxp(ax, 4.35, 2.2, 0.9, 0.4, "HE0", "#ffffff", "#3d8b37", 8.5); boxp(ax, 5.35, 2.2, 0.9, 0.4, "Z- stop", "#ffffff", "#3d8b37", 8.5)
    wire(ax, [(4.8, 2.2), (4.8, 1.55), (5.6, 1.55)], "#e67e22", 2, "--")
    boxp(ax, 5.6, 1.25, 2.55, 0.6, "reel motors: pins 5 and 6 of the\nfour corner sockets (next diagram)", "#fff3e6", "#e67e22", 8)
    wire(ax, [(5.8, 2.6), (5.8, 2.8), (7.6, 2.8), (7.78, 2.95)], "#8e44ad", 1.8, ":")
    ax.text(7.2, 2.45, "Z switch: pins 5 and 6\nof the sled socket", fontsize=8, color="#8e44ad", ha="center")
    ax.set_xlim(0, 12.9); ax.set_ylim(0.6, 7.9); ax.axis("off")
    ax.set_title("Wiring overview")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "wiring_overview.png")); plt.close(fig)


def pinout():
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=120)
    cols = ["#c0392b", "#2980b9", "#27ae60", "#f1c40f", "#e67e22", "#7f8c8d"]
    corner = ["stepper coil A", "stepper coil A", "stepper coil B", "stepper coil B", "reel motor", "reel motor"]
    sled = ["Z motor coil A", "Z motor coil A", "Z motor coil B", "Z motor coil B", "Z switch", "Z switch"]
    for row, (title, labels) in enumerate((("Corner sockets and leads", corner), ("Sled lead", sled))):
        y = 2.9 - row * 2.0
        ax.text(0.1, y + 0.75, title, fontsize=11, weight="bold")
        for i in range(6):
            x = 0.4 + i * 1.75
            ax.add_patch(Circle((x + 0.25, y), 0.25, fc=cols[i], ec="k"))
            ax.text(x + 0.25, y, str(i + 1), ha="center", va="center", fontsize=11, color="white", weight="bold")
            ax.text(x + 0.6, y, labels[i], va="center", fontsize=9)
        for a in (0, 2, 4):
            x0, x1 = 0.4 + a * 1.75, 0.4 + (a + 1) * 1.75 + 1.55
            ax.plot([x0, x0, x1, x1], [y - 0.38, y - 0.5, y - 0.5, y - 0.38], color="#555", lw=1.2)
            ax.text((x0 + x1) / 2, y - 0.72, "a pair", ha="center", fontsize=8.5, color="#555")
    ax.text(0.1, -0.15, "Pin numbers are moulded into the plastic beside each pin. The wire colours here are only an example:\nwhat matters is that every plug and socket uses the same pin for the same job.", fontsize=9.5, color="#333")
    ax.set_xlim(0, 11); ax.set_ylim(-0.5, 4.0); ax.axis("off")
    ax.set_title("What goes on each pin of the 6-pin connectors")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "wiring_pinout.png")); plt.close(fig)


def reels():
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=120)
    for row, (a, b) in enumerate((("SW", "SE"), ("NE", "NW"))):
        y = 3.0 - row * 1.7
        boxp(ax, 0.2, y - 0.3, 1.3, 0.6, "HE0  +", "#e4f3e1", "#3d8b37")
        boxp(ax, 2.2, y - 0.25, 1.6, 0.5, "120 ohm 5W", "#fff3c4", "#b7950b", 9)
        boxp(ax, 4.6, y - 0.4, 1.9, 0.8, f"{a} socket\npin 5      pin 6", "#dfe9f5", fs=9)
        boxp(ax, 7.2, y - 0.4, 1.9, 0.8, f"{b} socket\npin 5      pin 6", "#dfe9f5", fs=9)
        boxp(ax, 9.7, y - 0.3, 1.3, 0.6, "HE0  -", "#e4f3e1", "#3d8b37")
        for x0, x1 in ((1.5, 2.2), (3.8, 4.6), (6.5, 7.2), (9.1, 9.7)):
            wire(ax, [(x0, y), (x1, y)], "#e67e22", 2.5)
    ax.text(0.2, 0.35, "Two chains, both across the same HE0 terminals. Each chain: resistor, then one reel motor, then the next.\n"
            "All of this wiring is inside the tray, between the backs of the sockets. Nothing extra goes out to the corners.", fontsize=9.5)
    ax.set_xlim(0, 11.2); ax.set_ylim(0, 3.9); ax.axis("off")
    ax.set_title("Reel motor wiring inside the tray")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "wiring_reels.png")); plt.close(fig)


if __name__ == "__main__":
    overview(); pinout(); reels(); print("ok")
