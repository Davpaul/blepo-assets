"""Single source of truth for the machine's dimensions (all mm).

The CAD (parts.py), the Python tools and the firmware constants all come from
here. If you change a number, rebuild the STLs AND regenerate the table config
(tools/table_config.py prints the firmware values).
"""
import math

# ---- bought parts -----------------------------------------------------------
BELT_PITCH = 2.0            # GT2
PULLEY_TEETH = 20
PULLEY_PITCH_R = PULLEY_TEETH * BELT_PITCH / (2 * math.pi)   # 6.366
BELT_BACK_ABOVE_PITCH = 0.376   # GT2: pitch line to smooth back
BELT_BACK_R_ON_PULLEY = PULLEY_PITCH_R + BELT_BACK_ABOVE_PITCH  # 6.742
PULLEY_FLANGE_D = 18.0
IDLER_OD = 12.0             # smooth (toothless) GT2 idler, 5 mm bore, 6 mm belt
IDLER_PITCH_R = IDLER_OD / 2 + BELT_BACK_ABOVE_PITCH          # 6.376
IDLER_H = 9.0
BEARING_625 = dict(d=5.0, D=16.0, B=5.0)
NEMA17 = dict(size=42.3, hole_pitch=31.0, boss_d=22.0, shaft_d=5.0)
LM8UU = dict(D=15.0, L=24.0)
ROD_D = 8.0
ROD_LEN = 150.0
T8_NUT = dict(body_d=10.2, flange_d=22.0, hole_pcd=16.0, hole_d=3.5)
ROUTER_D = 65.0             # Katsu / Makita RT0700C motor body

# ---- belt plane -------------------------------------------------------------
PLATE_T = 6.0               # corner bracket plate and sled base thickness
BELT_Z = 18.0               # belt centre height above the surface the part sits on

# ---- corner drive unit (bracket-local frame) --------------------------------
# Sheet corner at the origin, sheet occupying x>0, y>0, sheet top at z=0.
P_LOCAL = (-30.0, -30.0)                 # motor shaft / drive pulley axis
F_OFFSET = 32.0                          # belt end post, left of P seen from the sled
F_LOCAL = (P_LOCAL[0] - F_OFFSET * math.sqrt(0.5),
           P_LOCAL[1] + F_OFFSET * math.sqrt(0.5))   # (-52.63, -7.37)
PINCH_ANGLE_DEG = 285.0                  # where the pinch bearing holds the belt on the pulley
PINCH_GAP = 0.3
PINCH_DIST = BELT_BACK_R_ON_PULLEY + PINCH_GAP + BEARING_625["D"] / 2   # 15.04
K_LOCAL = (P_LOCAL[0] + PINCH_DIST * math.cos(math.radians(PINCH_ANGLE_DEG)),
           P_LOCAL[1] + PINCH_DIST * math.sin(math.radians(PINCH_ANGLE_DEG)))
FENCE_T = 6.0
FENCE_DEPTH = 12.0
TOP_PLATE = 80.0

# ---- sled -------------------------------------------------------------------
SLED_SIZE = 220.0
IDLER_OFFSET = 32.0         # sled idlers at (+-32, +-32) from the bit
ROD_X = 58.0                # Z guide rods at (+-58, 0)
SCREW_Y = 64.0              # Z lead screw at (0, 64)
BIT_HOLE_D = 36.0
CARRIAGE_H = 50.0
CARRIAGE_Z_MIN = 30.0       # lowest carriage underside above the sheet
BRIDGE_Z = 140.0            # underside of the top bridge
BRIDGE_T = 14.0

# ---- fits -------------------------------------------------------------------
CLEAR_M3 = 3.4
CLEAR_M5 = 5.4
PILOT_M3 = 2.8              # self-tapping M3 into plastic
PILOT_M5 = 4.5              # self-tapping M5 into plastic
HEX_M5_AF = 8.2             # M5 hex head / nut across flats, with clearance

# ---- slack-belt reel at each corner (bracket-local frame) --------------------
REEL_LOCAL = (45.0, -75.0)   # reel axis: outside the sheet, beside the south fence
REEL_HUB_R = 15.0
REEL_FLANGE_R = 56.0         # holds 5.5 m of belt (wound radius about 52 mm)
REEL_CHANNEL = 7.5           # gap between flanges for the 6 mm belt
N20 = dict(w=12.0, d=10.0, body_len=34.0, shaft_d=3.0, shaft_flat=2.5, shaft_len=10.0)
N20_POCKET = 3.5             # gearbox face is let this far into the underside of the plate
