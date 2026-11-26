# Minimum test kit: one corner unit on a bench

Before printing the whole machine, build **one corner unit** and prove it works. It exercises the parts most likely to need adjusting: the belt pinch gap, the motor and firmware, and the reel. It costs about £50, takes about 9 hours of printing, and needs no sled, no table and no router.

## What to print

One plate, ready to go: `print/gcode/00_test_kit_x1_petg_klipper.gcode` (sliced for your X1 on Klipper with PETG). Or open `print/plates/00_test_kit.3mf` in OrcaSlicer and use the **strong** preset.

| Part | Qty |
|---|---|
| `corner_bracket` | 1 |
| `reel_body`, `reel_flange`, `n20_cup` | 1 each |
| `f_spacer`, `f_sleeve`, `k_spacer` | 2 each (one spare of each) |

**9h 20m and 160g of PETG**, with a 5mm brim on the bracket so it does not lift. Everything is in the same settings as the real build, so if this bracket works, the other three will.

## What to get

| Item | Qty | Est. |
|---|---|---|
| MKS TinyBee controller board | 1 | £20 |
| TMC2209 stepper driver | 1 | £3 |
| NEMA17 stepper (from the X1) | 1 | free |
| 20-tooth GT2 pulley, 5mm bore (from the X1) | 1 | free |
| N20 geared motor, 6V, about 100 rpm, wires attached | 1 | £3 |
| 120 ohm 5W resistor | 1 | £1 |
| GT2 belt, 6mm wide | 2m | £2 |
| 625 bearing | 1 | £1 |
| Smooth GT2 idler, 5mm bore (stands in for the sled's idler) | 1 | £1 |
| M5 x 30 and M5 x 25 hex bolts | 1 each | |
| M5 nyloc nuts | 3 | |
| M5 washer | 1 | |
| M3 x 8 cap screws | 4 | |
| M3 x 12 pan-head screws | 5 | |
| M5 x 30 bolt for the stand-in idler (and a nut) | 1 | |
| RJ45 breakout boards with screw terminals | 2 | £3 |
| Network lead, 1 to 2m, straight (not crossover) | 1 | £2 |
| Sealed 24V adapter, 5A or more | 1 | £15 |
| Small zip ties | 2 | |
| USB lead, laptop | 1 | |
| A flat board with a square corner, about 600 x 400mm, and two clamps | 1 | scrap |

The fixings are about £4 from an assortment box. No tray, no knobs, no soldering iron: the motors need wires under screw terminals only.

## What to do

Everything below points at the manual (`belt-cnc-build-guide.pdf`), so you are following the same steps you will use for the real build.

1. **Print the plate.**
2. **Build the corner unit.** Manual section 3, steps 1 to 10. When you reach the **pinch-gap check** (step 7), stop and do it carefully: this is the tightest fit in the whole machine. A scrap of belt must pass between pulley and bearing with light drag, and not be able to lift off the teeth.
3. **Clamp the bracket** to the square corner of your board, fence walls hard against the two edges.
4. **Fit the stand-in idler.** Bolt a smooth idler to the board with an M5 bolt and nut, about 500mm from the bracket along the line running diagonally into the board. It stands in for the sled's idler.
5. **Wire it.** Manual section 5: one breakout board on the bracket's panel, one on the bench, joined by the network lead. Stepper pairs on terminals 1 and 2, and 3 and 6. Reel motor on terminals 4 and 5, then from the bench board to the main board's HE0 terminals through the resistor. Set the driver for 16 microsteps and about 1A. Do the continuity tests before you switch on.
6. **Load the software.** Manual section 6: download the software from GitHub, flash the board, upload `belt-cnc.yaml`.
7. **Thread the belt.** Manual section 8, step 2 (thread each corner), using the stand-in idler in place of the sled's.
8. **Run the checks** from the laptop with `python3 tools/beltcnc.py setup --port PORT --config belt-cnc.yaml`:
   - `dirtest`. Press Enter at the three corners that have no motor. At the SW corner, belt should pay out then come back in.
   - `sw 40`. The pulley should make **exactly one full turn**, and 40mm of belt should pass. If not, the microstep jumpers or `steps_per_mm` are wrong. Mark the pulley and belt with a pen to see it.
   - Watch the reel: it should tug gently the whole time, and wind spare belt on when the stepper takes belt in.
   - Run `sw 5` a few times, then `sw -5` to return, listening for clicks or grinding.

## What it tells you

| Passes | Means |
|---|---|
| Pinch gap holds the belt, and the belt runs smoothly | The bracket, spacers and bearing fit. Print the other three brackets. |
| `dirtest` runs, one turn for `sw 40` | The wiring, driver, firmware and step settings are right. |
| Reel tugs but does not strain the motor, motors stay cool | The 120 ohm resistor is about right. If the reel is weak, fit 82 ohm; if the N20 gets hot, a higher one. |
| Belt feeds on and off the reel without snagging | The reel works. This is the part I trust least, so it is the most valuable thing to learn. |

## What it cannot tell you

- Anything about the **sled** or the **Z axis**: the next small test, once this passes, is the sled with its idlers and carriage on the bench.
- How the **four belts work together**: balancing tension, the test square, the reach near the edges.
- **Accuracy.** That needs all four corners and a table.

If anything here fails, tell me which step and what you saw. A change to the bracket costs one 9-hour plate, not four brackets and a reel set.
