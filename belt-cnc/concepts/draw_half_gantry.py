"""Concept diagram: a passive half gantry that carries the sled's weight.
    python3 draw_half_gantry.py      ->  half_gantry_concept.png
"""
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, Polygon, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
WOOD, WOOD_E = "#ead9b5", "#a8894f"
BLUE, BLUE_E = "#8fb8e6", "#2f6aa8"
ORANGE, ORANGE_E = "#f6b26b", "#b4641c"
STEEL, STEEL_E = "#c9ccd1", "#5a5f66"
DARK = "#2b2f33"
RED = "#d9541e"


def label(ax, xy, text, xytext, ha="left", fs=10.5):
    ax.annotate(text, xy=xy, xytext=xytext, ha=ha, va="center", fontsize=fs,
                arrowprops=dict(arrowstyle="-", color="#444", lw=0.9, shrinkA=0, shrinkB=2),
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#444", lw=0.8))


def plan(ax):
    W, H = 2440, 1220
    ax.add_patch(Rectangle((0, 0), W, H, fc=WOOD, ec=WOOD_E, lw=1.2))
    ax.text(1950, 1060, "sheet", fontsize=11, color="#8a6d32", style="italic")
    for y in (-110, H + 50):                                                  # rails along both long edges
        ax.add_patch(Rectangle((-80, y), W + 160, 60, fc=STEEL, ec=STEEL_E, lw=1))
    bx, sx, sy = 900, 900, 520
    corners = [(-60, -60), (W + 60, -60), (W + 60, H + 60), (-60, H + 60)]
    for (cx, cy) in corners:
        ax.add_patch(FancyBboxPatch((cx - 55, cy - 55), 110, 110, boxstyle="round,pad=0,rounding_size=18", fc=BLUE, ec=BLUE_E, lw=1.2, zorder=4))
        ax.plot([cx, sx], [cy, sy], color=DARK, lw=1.6, zorder=3)
    for dx in (-62, 30):                                                      # twin beams, router drops between them
        ax.add_patch(Rectangle((bx + dx, -150), 32, H + 300, fc=ORANGE, ec=ORANGE_E, lw=1.3, zorder=5))
    for y in (-150, H + 30):                                                  # wheel trucks
        ax.add_patch(Rectangle((bx - 100, y), 200, 120, fc="#ffd9a6", ec=ORANGE_E, lw=1.3, zorder=6))
        for dx in (-60, 60):
            ax.add_patch(Circle((bx + dx, y + 60), 22, fc=STEEL, ec=STEEL_E, lw=1, zorder=7))
    ax.add_patch(FancyBboxPatch((sx - 125, sy - 125), 250, 250, boxstyle="round,pad=0,rounding_size=25", fc=BLUE, ec=BLUE_E, lw=1.4, zorder=8, alpha=0.92))
    ax.add_patch(Circle((sx, sy), 26, fc="#e07a6a", ec="#8a2a1c", lw=1.2, zorder=9))
    ax.add_patch(FancyArrowPatch((bx + 200, H + 270), (bx + 560, H + 270), arrowstyle="<|-|>", mutation_scale=16, color=RED, lw=2))
    ax.text(bx + 380, H + 330, "beams roll along X", ha="center", color=RED, fontsize=10.5, weight="bold")
    ax.add_patch(FancyArrowPatch((sx - 190, sy - 260), (sx - 190, sy + 260), arrowstyle="<|-|>", mutation_scale=16, color=RED, lw=2, zorder=10))
    ax.text(sx - 215, sy + 330, "sled slides along\nthe beams (Y)", ha="right", color=RED, fontsize=10.5, weight="bold", va="center",
            bbox=dict(boxstyle="round,pad=0.25", fc=WOOD, ec="none"))
    label(ax, (1700, -80), "rail along each long edge (aluminium angle or straight timber)", (1600, -330), ha="center")
    label(ax, (bx - 100, H + 90), "wheel truck: V-wheels on the rail", (250, H + 390), ha="center")
    label(ax, (bx - 46, 120), "twin beams, about 1.4m long:\naluminium extrusion, NOT driven", (-620, 160), ha="center")
    label(ax, (sx + 125, sy - 60), "sled hangs between the beams;\nrouter drops through the gap", (W + 500, 560), ha="center")
    label(ax, (W + 110, -40), "corner units and belts:\nunchanged, they still do\nall the positioning", (W + 500, 150), ha="center")
    label(ax, (360, 220), "belt", (-620, 520), ha="center")
    ax.text(W / 2, -480, "SOUTH: you stand here", ha="center", fontsize=10.5, weight="bold")
    ax.set_xlim(-1000, W + 900); ax.set_ylim(-560, H + 470)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Top view", fontsize=14, weight="bold", loc="left")


def end_view(ax):
    """Section across the table, looking along X (south on the left)."""
    H = 1220
    sheet_t = 18
    # trestle/table under the sheet
    ax.add_patch(Rectangle((-40, -60), H + 80, 60, fc="#d9d2c3", ec="#8f8778", lw=1))
    ax.text(H / 2, -32, "support board / foam", ha="center", va="center", fontsize=9.5, color="#5f584a")
    ax.add_patch(Rectangle((0, 0), H, sheet_t, fc=WOOD, ec=WOOD_E, lw=1.2))
    # rails on raised blocks either side
    rail_top = 95
    for x0 in (-170, H + 50):
        ax.add_patch(Rectangle((x0, -60), 120, rail_top - 20 + 60, fc="#d9d2c3", ec="#8f8778", lw=1))     # riser block
        ax.add_patch(Polygon([(x0 + 20, rail_top - 20), (x0 + 100, rail_top - 20), (x0 + 100, rail_top - 14), (x0 + 66, rail_top - 14),
                              (x0 + 66, rail_top + 40), (x0 + 54, rail_top + 40), (x0 + 54, rail_top - 14), (x0 + 20, rail_top - 14)],
                             closed=True, fc=STEEL, ec=STEEL_E, lw=1))                                       # angle rail, edge up
        # wheels: one on top, one under the lip so it cannot lift
        ax.add_patch(Circle((x0 + 60, rail_top + 40 + 22), 22, fc=STEEL, ec=STEEL_E, lw=1, zorder=5))
    beam_y = rail_top + 40 + 44
    ax.add_patch(Rectangle((-200, beam_y), H + 400, 80, fc=ORANGE, ec=ORANGE_E, lw=1.3, zorder=4))
    # sled hanging from the beam
    sx = 520
    car_y = beam_y + 80
    ax.add_patch(Rectangle((sx - 100, car_y), 200, 40, fc="#ffd9a6", ec=ORANGE_E, lw=1.2, zorder=6))     # carriage on top of beam
    for dx in (-60, 60):
        ax.add_patch(Circle((sx + dx, car_y + 2), 14, fc=STEEL, ec=STEEL_E, lw=1, zorder=7))
    ax.add_patch(Rectangle((sx - 110, sheet_t + 6), 220, 16, fc=BLUE, ec=BLUE_E, lw=1.3, zorder=6))         # sled plate, just clear of the sheet
    for dx in (-95, 85):
        ax.add_patch(Rectangle((sx + dx, sheet_t + 22), 10, car_y - sheet_t - 22, fc=BLUE, ec=BLUE_E, lw=1.1, zorder=3))   # hangers
    ax.add_patch(Rectangle((sx - 32, sheet_t + 30), 64, 420, fc="#e07a6a", ec="#8a2a1c", lw=1.2, zorder=8))   # router
    ax.add_patch(Rectangle((sx - 5, sheet_t - 8), 10, 40, fc=DARK, ec=DARK, zorder=8))                         # bit
    # belts at sheet level, out to the corners
    ax.plot([-170, sx - 110], [sheet_t + 14, sheet_t + 14], color=DARK, lw=1.6, zorder=2)
    ax.plot([sx + 110, H + 170], [sheet_t + 14, sheet_t + 14], color=DARK, lw=1.6, zorder=2)
    # labels
    label(ax, (sx, sheet_t + 3), "a few mm gap: the sled no longer\nrests on the work, so it cannot\ntip into cut-outs", (1000, -170), ha="center")
    label(ax, (sx - 32, 380), "router", (260, 520), ha="center")
    label(ax, (H + 110, rail_top + 62), "wheel above the rail,\nlip stops it lifting", (1300, 330), ha="center")
    label(ax, (H / 2 + 330, beam_y + 40), "twin beams (one behind the other in this\nview): the router drops between them", (1150, beam_y + 260), ha="center")
    label(ax, (sx - 140, sheet_t + 14), "belts pull at the\nsled, as now", (110, -170), ha="center")
    label(ax, (-110, 80), "rail on a riser,\nabove sheet height", (-260, 330), ha="center")
    ax.set_xlim(-430, H + 500); ax.set_ylim(-240, 640)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("End view, cut across the table", fontsize=14, weight="bold", loc="left")


def main():
    fig = plt.figure(figsize=(13, 12.5), dpi=150)
    a1 = fig.add_axes([0.02, 0.40, 0.96, 0.56])
    a2 = fig.add_axes([0.02, 0.06, 0.96, 0.34])
    plan(a1); end_view(a2)
    fig.suptitle("Half gantry concept: carries the sled's weight, the belts still drive it", fontsize=16, weight="bold", y=0.995)
    fig.text(0.02, 0.02, "Concept only: not to scale in the end view, not yet designed or checked.", fontsize=9.5, color="#666")
    fig.savefig(os.path.join(HERE, "half_gantry_concept.png"), facecolor="white")
    print("ok")


if __name__ == "__main__":
    main()
