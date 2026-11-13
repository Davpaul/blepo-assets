# Shopping list

Everything that does not come off the printer. Prices are rough, in USD, late 2026.

About the links: Adafruit and Raspberry Pi links go to the exact product. For generic parts (servos, screws, converters) the link is a search, because individual marketplace listings vanish every few months. Any listing matching the spec column will do. I don't know which country you're in, so swap amazon.com for your local store.

## Servos

| Qty | Part | Spec to match | Used for | Approx | Link |
|---|---|---|---|---|---|
| 2 | DS3235 digital servo, 180° | 35 kg·cm, 40 x 20 mm body, 25T spline, metal gear | Body lean (roll, pitch) | $20 ea | [Amazon](https://www.amazon.com/s?k=DS3235+35kg+servo+180+degree) · [AliExpress](https://www.aliexpress.com/wholesale?SearchText=DS3235+35kg+servo+180) |
| 9 | DS3218 digital servo, 180° | 20 kg·cm, same body and spline | Body twist, head x3, jaw, arm pan x2, arm tilt x2 | $13 ea | [Amazon](https://www.amazon.com/s?k=DS3218+20kg+servo+180+degree) · [AliExpress](https://www.aliexpress.com/wholesale?SearchText=DS3218+20kg+servo+180) |
| 2 | DS3218 digital servo, **270°** | As above but 270° travel | Arm pistons (gives 100 mm stroke; a 180° one gives 85 mm) | $13 ea | [Amazon](https://www.amazon.com/s?k=DS3218+20kg+servo+270+degree) · [AliExpress](https://www.aliexpress.com/wholesale?SearchText=DS3218+270+degree) |
| 15 | 25T aluminium disc horn | 20 mm disc, 4 x M3 tapped holes on a 14 mm circle | One per servo, two spare | $1 ea | [Amazon](https://www.amazon.com/s?k=25T+aluminum+servo+horn+disc+M3) · [AliExpress](https://www.aliexpress.com/wholesale?SearchText=25T+aluminum+servo+horn+disc) |
| 10 | Servo extension lead, 500 mm | 3-pin JR/Futaba style, 22 AWG | Head, jaw, arm units | $8 / 10 | [Amazon](https://www.amazon.com/s?k=servo+extension+cable+500mm+22awg) |

Saving money: the six arm-unit servos carry very little load, so MG996R servos ($5 each) fit the same pockets. Keep the DS32xx ones for the body and head.

## Electronics

| Qty | Part | Spec to match | Approx | Link |
|---|---|---|---|---|
| 1 | Raspberry Pi Zero 2 W with headers | Any Pi with a 40-pin header works. Get a Pi 4 or 5 if you plan to do vision or AI voice on board later | $18 | [raspberrypi.com](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) |
| 1 | microSD card, 32 GB | Class 10 / A1 | $8 | [Amazon](https://www.amazon.com/s?k=32GB+microSD+A1) |
| 2 | PCA9685 16-channel servo driver | I2C, 12-bit | $15 ea (Adafruit), $4 ea (generic) | [Adafruit 815](https://www.adafruit.com/product/815) · [Amazon](https://www.amazon.com/s?k=PCA9685+16+channel+servo+driver) |
| 1 | MAX98357A I2S amplifier | 3 W mono, class D | $6 | [Adafruit 3006](https://www.adafruit.com/product/3006) |
| 1 | Speaker, 4 Ω, 3 to 5 W | 40 to 57 mm across. The printed cradle takes anything in that range | $5 | [Adafruit 3968](https://www.adafruit.com/product/3968) |
| 1 | 12 V 10 A DC power supply | Enclosed "brick" type with 5.5 x 2.1 mm barrel plug | $20 | [Amazon](https://www.amazon.com/s?k=12V+10A+power+supply+adapter+5.5x2.1) |
| 1 | Barrel jack to screw terminal adapter | 5.5 x 2.1 mm female | $1 | [Amazon](https://www.amazon.com/s?k=5.5x2.1+female+barrel+jack+screw+terminal) |
| 1 | Buck converter, 20 A adjustable | 12 V in, set to 6.0 V out, 300 W class | $12 | [Amazon](https://www.amazon.com/s?k=300W+20A+DC+DC+buck+converter+adjustable) |
| 1 | Buck converter, 12 V to 5 V 3 A USB | Micro-USB plug for a Pi Zero, USB-C for a Pi 4/5 | $8 | [Amazon](https://www.amazon.com/s?k=12V+to+5V+3A+buck+converter+micro+usb) |
| 1 | Inline blade fuse holder + 10 A fuse | 16 AWG leads | $5 | [Amazon](https://www.amazon.com/s?k=inline+blade+fuse+holder+16awg) |
| 1 | Rocker switch | 12 V, 10 A or more | $3 | [Amazon](https://www.amazon.com/s?k=rocker+switch+12V+16A) |
| 2 | Electrolytic capacitor | 1000 µF, 16 V. One per servo board | $1 | [Amazon](https://www.amazon.com/s?k=1000uF+16V+electrolytic+capacitor) |
| 2 m | Silicone wire, 16 AWG, red + black | Servo power | $8 | [Amazon](https://www.amazon.com/s?k=16awg+silicone+wire+red+black) |
| 1 | Jumper wire set | Female-female, 200 mm | $5 | [Amazon](https://www.amazon.com/s?k=dupont+jumper+wires+female+female+20cm) |
| 1 | Nylon standoff kit, M2.5 | For screwing boards to plywood | $8 | [Amazon](https://www.amazon.com/s?k=M2.5+nylon+standoff+kit) |
| 1 | Cable ties + spiral wrap | 100 x 2.5 mm ties | $5 | [Amazon](https://www.amazon.com/s?k=spiral+cable+wrap+6mm) |

## From the hardware store

This is where timber and pipe save a lot of print time.

| Qty | Part | Spec | Notes |
|---|---|---|---|
| 1.5 m | PVC pressure pipe, 26.7 mm outside diameter | Sold as 3/4 inch Schedule 40 (US) or 20 mm PN12/PN18 (AU/NZ) | Boom, mast, entry pipe, outrigger. A hacksaw cuts it. Measure the outside with calipers before printing clamps |
| | *Stiffer alternative* | 25 mm aluminium tube or 25 mm hardwood dowel | Print the clamps from the `pipe_25.0mm` folder instead. Recommended if Twist is heavy or you want crisp, wobble-free moves |
| 1 | Plywood, 12 mm, about 180 x 400 mm | Any flat offcut | Two decks: 170 x 170 fixed, 180 x 180 turntable |
| 1 | Plywood or MDF, 6 to 9 mm, 150 x 170 mm | | Electronics board, clamps to the mast |
| 1 | Lazy susan bearing, 150 mm (6 inch) | Steel, ball bearing, about 8.5 mm thick | Carries the whole rig so the twist servo only has to turn it. [Amazon](https://www.amazon.com/s?k=6+inch+lazy+susan+bearing) |
| 1 | 1/4"-20 hex nut | Zinc or stainless | Tripod thread. Light stands need a 5/8" spigot to 1/4" adapter |
| 2 | Velcro strap or 20 mm elastic, 300 mm | | Holds the puppet's mouth plates to the paddles |
| | *Optional* 3 mm plywood or acrylic | 115 x 56 mm x 2 | Cut the mouth paddles instead of printing them (use `paddle.stl` as a template) |

## Fasteners

All metric. A boxed M3/M4/M5 assortment covers most of this.

| Qty | Fastener | Where |
|---|---|---|
| 60 | M4 x 16 button head | Servo ears (52), paddles (4), rack guides (4) |
| 56 | M4 nyloc nut | Servo ears, paddles |
| 20 | M4 plain nut | Captive nuts in pitch and tilt yokes (16), rack guides (4) |
| 8 | M4 x 12 socket head | Carriage and head frame onto their yokes |
| 8 | M4 x 10 socket head | Slide stages onto tilt yokes |
| 12 | M3 x 6 button head | bracket_L onto horns |
| 32 | M3 x 8 socket head | Yoke arms and yaw hub onto horns |
| 8 | M3 x 12 socket head | Pinions onto horns |
| 6 | M3 x 16 socket head + M3 nut | Rod clamps, rack end stops |
| 7 | M5 x 16 socket head + M5 nyloc nut | Idle-side pivots of the seven yokes |
| 14 | M5 x 25 socket head + M5 nyloc nut | Clamp pinch bolts |
| 50 | M5 washer | Pivots (3 each) and pinch bolts (2 each) |
| 3 | M6 x 50 hex bolt + M6 wing nut | Knuckle pairs |
| 4 | M6 x 30 hex bolt + M6 nut | Arm bases, speaker, accessory mount (captive nut) |
| 1 | M6 x 35 hex bolt + M6 nut | Neck base |
| 16 | M6 washer | |
| 14 | Self-tapping screw 3.5 x 13 pan head | Locks each clamp to its pipe once you're happy with the fit |
| 8 | Wood screw 4 x 16 | tripod_base to deck (4), bracket_L to turntable (4) |
| 8 | Wood screw 3.5 x 10 | Lazy susan to both decks |
| 4 | Wood screw 3.5 x 20 | Turntable deck down into the yaw hub |
| 4 | Wood screw 4 x 12 | Pipe saddles to the electronics board |

## Later: camera and microphone

Nothing to buy now. The design leaves room for them:

| Part | How it fits |
|---|---|
| [Raspberry Pi Camera Module 3](https://www.raspberrypi.com/products/camera-module-3/) (plus the Zero cable) | Plugs into the Pi's camera port. Bolt it to the printed `accessory_mount`, which clips to any knuckle, or hide it in the puppet |
| USB microphone or [Adafruit I2S mic 3421](https://www.adafruit.com/product/3421) | USB is plug and play. The I2S mic shares the amplifier's clock pins (see WIRING.md) |
| 3 spare servo channels on each driver board | Eyebrows, eyelids, ears |

## Rough total

Servos about $190, electronics about $115, hardware store about $45, fasteners about $30, filament about $30. Call it **$400 to $420**, or near $360 with MG996R servos in the arm units.
