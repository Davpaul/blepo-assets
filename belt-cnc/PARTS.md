# Parts list

Prices are my estimates (AliExpress / Amazon UK level). Check live listings before ordering.

## From the Artillery Sidewinder X1

Print everything first (see BUILD.md step 1), then strip it. I have not seen your printer, so check each item against what you find inside.

| Part | Qty | Used for | Check |
|---|---|---|---|
| NEMA17 stepper motors | 5 | 4 belt drives + Z axis | X, Y, extruder and the two Z motors. Use the four most alike for the belts. |
| 24V power supply | 1 | Whole machine | Read the label: you need 24V and 5A or more. |
| T8 lead screw + brass nut | 1 of 2 | Z axis | Cut one screw to 115mm with a hacksaw. See the note below. |
| Flexible shaft coupler, 5mm to 8mm | 1 of 2 | Z motor to lead screw | On the Z motors. |
| GT2 20-tooth pulleys | 2 | Belt drives | On the X and Y motors. Must be 5mm bore for 6mm belt. |
| Motor cables and connectors | all | Wiring | The plugs fit the motors. You will extend them. |
| Cooling fan, 24V | 1 | Electronics box | Any of them. |
| Screws, T-nuts, wheels | all | Spares | Keep the lot. |

**Mains warning.** The X1's heated bed runs on mains voltage. Unplug the printer and leave it 10 minutes before opening the base. Do not reuse the bed or its relay.

**Not reusable:** the main board (it cannot run FluidNC), the touch screen, the hot end.

**Lead screw note.** The X1's screws most likely have an 8mm lead (four starts). That works, but the router can creep down when the power is off. A 2mm-lead screw fixes that for about £6 and is on the buy list as optional.

## To buy

### Electronics

| Item | Qty | Est. |
|---|---|---|
| MKS TinyBee V1.0 controller board | 1 | £20 |
| TMC2209 stepper driver modules | 5 | £15 |
| MicroSD card, any size | 1 | £4 |
| 4-core cable, 0.5mm² (alarm cable is fine) | 15m | £10 |
| Microswitch, lever type (KW11 style, 9.5mm hole pitch) | 2 | £2 |
| JST-XH or Dupont connector kit | 1 | £5 |
| Switched extension lead (your emergency stop) | 1 | £8 |

### Belt drive

| Item | Qty | Est. |
|---|---|---|
| GT2 belt, 6mm wide, fibreglass core, open length | 25m | £18 |
| GT2 20-tooth pulley, 5mm bore, 6mm belt | 2 (buy a pack of 5) | £5 |
| GT2 smooth idler (no teeth), 5mm bore, 6mm belt, 12mm barrel | 4 (buy 5) | £5 |
| 625ZZ bearings (5 x 16 x 5mm) | 4 (pack of 10) | £4 |
| Small zip ties, 2.5mm | pack | £2 |

### Z axis

| Item | Qty | Est. |
|---|---|---|
| Smooth steel rod, 8mm x 150mm | 2 | £6 |
| LM8UU linear bearings | 4 | £4 |
| Optional: T8 lead screw, 2mm lead, 150mm, with nut | 1 | £6 |

### Fixings

| Item | Qty | Where |
|---|---|---|
| M5 x 30 hex bolt | 4 | Belt-end posts |
| M5 x 25 hex bolt | 4 | Pinch bearing posts |
| M5 x 30 countersunk bolt | 4 | Sled idlers |
| M5 x 30 hex bolt | 2 | Router clamp |
| M5 x 40 hex bolt | 4 | Thumb screws on the pen and laser caddies |
| M5 nyloc nuts | 12 | Posts and idlers |
| M5 plain nuts | 4 | Router clamp, spares |
| M5 washers | 10 | |
| M3 x 8 cap screws | 20 | Motors |
| M3 x 10 cap screws + M3 nuts | 4 + 4 | Lead screw nut |
| M3 x 12 pan-head screws | 30 | Self-tapped into plastic: guides, bearings, rods, lid |
| M2 x 10 self-tapping screws | 2 | Z switch |
| Wood screws, 4 x 30mm countersunk | 12 | Corner brackets |

An M3 and M5 assortment box covers all of this for about £12.

### Tooling and materials

| Item | Qty | Est. |
|---|---|---|
| Trim router, 65mm body (Katsu or Makita RT0700C) | 1 | £40 |
| Router bits: 1/8" and 1/4" single-flute upcut, 60° V-bit | 3 to 4 | £15 |
| PETG filament | 2kg | £28 |
| XPS foam insulation board, 50mm, to lie under the sheet | 1 to 2 | £12 |
| Buckets or tubs, one per corner, to catch the slack belt | 4 | free |
| Scrap ply or timber for the corner wings (optional, see BUILD.md) | 4 pieces about 300 x 250mm | free |

### Optional tools

| Item | Est. |
|---|---|
| Diode laser module, 5 to 10W, 12V or 24V with PWM input, plus matching safety glasses | £60 to £150 |
| Touch plate for setting Z zero (a scrap of aluminium and a wire) | free |

## Rough total

About £230 new, on top of the donor printer. That leaves headroom under £500 for a laser module and mistakes.

## Printed parts

All STL files are in `stl/`, already turned the right way up for printing. None need supports.

| File | Qty | Notes |
|---|---|---|
| `corner_bracket.stl` | 4 | Top face on the bed, fence walls up. 5 walls, 50% infill. |
| `tail_guide.stl` | 4 | |
| `f_spacer.stl` | 4 | |
| `f_sleeve.stl` | 4 | Must turn freely on an M5 bolt. |
| `k_spacer.stl` | 4 | Small lip faces up. |
| `measuring_cap.stl` | 2 | |
| `sled_base.stl` | 1 | 220 x 220mm. Brim recommended. 4 walls, 40% infill. |
| `z_carriage.stl` | 1 | 5 walls, 50% infill. This holds the router. |
| `z_bridge.stl` | 1 | Top face on the bed. |
| `dust_shoe.stl` | 1 | Bridges 34mm unsupported. Hose spigot is 32mm; edit `cad/parts.py` for another size. |
| `pen_caddy_body.stl` | 1 | |
| `pen_slider.stl` | 1 | Must slide freely in the body. Sand if tight. |
| `thumb_knob.stl` | 4 | Push an M5 hex bolt head into each. |
| `laser_caddy.stl` | 1 | Only if you fit a laser. |
| `laser_shim.stl` | as needed | Packing for laser modules under 40mm square. |
| `riser_shim.stl` | as needed | 6mm lifts for a corner unit, see BUILD.md step 7. |
| `electronics_tray.stl`, `electronics_lid.stl` | 1 each | |

Settings for everything unless noted: PETG, 0.2mm layers, 4 walls, 40% infill. About 0.9kg of filament for one full set. Print one spare each of the small spacers and sleeves while the printer still exists.
