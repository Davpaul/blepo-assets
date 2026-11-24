"""Build the illustrated manual: manual.html, then ../belt-cnc-build-guide.pdf.

    python3 build_manual.py            # writes manual.html
    node make_pdf.js                   # prints it to PDF with the headless browser

Pictures come from scenes.py + render.js (img/) and the wiring and reach
diagrams in ../renders. Hardware drawings are life size: print at 100%.
"""
import html, os
from hardware_svg import HW, svg, ruler

HERE = os.path.dirname(os.path.abspath(__file__))
out = []
step_no = [0]


def add(s):
    out.append(s)


def esc(s):
    return html.escape(s, quote=False)


def fmt(s):
    """Tiny markup: **bold**, `code`."""
    s = esc(s)
    import re
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def need(items, title="You need"):
    if not items:
        return ""
    cells = "".join(f'<div class="hw">{svg(k)}<div class="cap">{(str(q) + " x ") if q else ""}{esc(HW[k][0])}</div></div>' for k, q in items)
    return f'<div class="need"><div class="needtitle">{esc(title)} <span>(life size)</span></div><div class="hwrow">{cells}</div></div>'


def box(kind, text):
    titles = {"tip": "Top tip", "dyk": "Did you know?", "warn": "Watch out", "check": "Check before moving on"}
    return f'<div class="note {kind}"><div class="notetitle">{titles[kind]}</div><div>{fmt(text)}</div></div>'


def section(title, intro=None, cls=""):
    add(f'<h1 class="{cls}">{esc(title)}</h1>')
    if intro:
        add(f'<p class="intro">{fmt(intro)}</p>')


def h2(t):
    add(f"<h2>{esc(t)}</h2>")


def p(t):
    add(f"<p>{fmt(t)}</p>")


def ul(items):
    add("<ul>" + "".join(f"<li>{fmt(i)}</li>" for i in items) + "</ul>")


def img(name, cls="pic", folder="img"):
    return f'<img class="{cls}" src="{folder}/{name}">'


def step(title, text, image=None, items=None, tip=None, dyk=None, warn=None, check=None, folder="img", wide=False, parts=None):
    step_no[0] += 1
    head = f'<div class="stephead"><span class="num">{step_no[0]}</span><h3>{esc(title)}</h3></div>'
    if isinstance(text, str):
        text = [text]
    words = "<ol>" + "".join(f"<li>{fmt(t)}</li>" for t in text) + "</ol>" if len(text) > 1 else f"<p>{fmt(text[0])}</p>"
    if parts:
        words = '<div class="printed">Printed parts: ' + ", ".join(f"<code>{esc(x)}</code>" for x in parts) + "</div>" + words
    notes = "".join(box(kind, val) for kind, val in (("warn", warn), ("check", check), ("tip", tip), ("dyk", dyk)) if val)
    if image:
        body = head + f'<div class="cols"><div>{img(image, "pic", folder)}</div><div>{words}{notes}</div></div>' + need(items)
    else:
        body = head + need(items) + words + notes
    add(f'<section class="step">{body}</section>')


def table(rows, widths=None):
    cols = "".join(f'<col style="width:{w}%">' for w in widths) if widths else ""
    h = "".join(f"<th>{esc(c)}</th>" for c in rows[0])
    b = "".join("<tr>" + "".join(f"<td>{fmt(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
    add(f"<table>{cols}<thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>")


# ============================================================================= content
def cover():
    add('<div class="cover"><div class="brand">BELT CNC</div><div class="sub">Build guide</div>')
    add(img("t02_overview.png", "coverpic"))
    add('<p class="lead">A full-sheet CNC router that packs away. A motor at each corner of the table pulls a small sled around on toothed belts. '
        'The sled carries a trim router, a pen or a laser. Spare belt winds onto a reel at each corner.</p>')
    add('<div class="note warn"><div class="notetitle">Read this first</div><div>This design has not been built yet. The parts have been checked on a computer for '
        'clashes, and the control software has been compiled and run in a simulator, but expect to adjust things as you go. '
        '<b>Build and test one corner unit before printing all four.</b> The last page lists what has and has not been checked.</div></div>')
    add('<div class="facts"><div><b>Cuts</b>up to a 2440 x 1220mm sheet</div><div><b>Tools</b>router, pen, laser</div><div><b>Budget</b>about £260 plus a donor 3D printer</div>'
        '<div><b>Time</b>about 98 hours of printing, three days to build</div></div></div>')


def how_to_read():
    section("How to use this guide")
    add('<div class="legend">'
        '<div><span class="num">1</span><span><b>Numbered steps.</b> Do them in order. Each has a picture of what goes where.</span></div>'
        '<div><span class="swatch new"></span><span><b>Blue and orange parts</b> are the ones you are fitting in this step. Grey parts are already fitted.</span></div>'
        '<div><span class="dash"></span><span><b>Dashed orange lines</b> show where each part slides in. This is an "exploded" view: parts are drawn pulled apart along the line they go in on.</span></div>'
        '<div><span class="swatch hwc"></span><span><b>Yellow parts</b> are screws, nuts and bolts. Each step shows the ones it uses <b>life size</b>, so you can lay yours on the page to pick the right one.</span></div>'
        '</div>')
    add(box("tip", "Tips save you time or a reprint.") + box("dyk", "These explain why something is the way it is. Skip them if you are in a hurry.")
        + box("warn", "These are the mistakes that break parts or waste an evening.") + box("check", "A quick test to do before the next step hides the part."))
    h2("Print this guide at 100%")
    p("In the print dialogue choose **Actual size** or **100%**, not \"Fit to page\". Then hold a ruler against this one. 150 here must be 150 on your ruler.")
    add(f'<div class="ruler">{ruler()}</div>')
    h2("Which way is which")
    p("Stand at one long edge of the table. That edge is **south**. The corner on your left is **south-west (SW)**, on your right **south-east (SE)**. "
      "The far corners are **NW** and **NE**. X runs left to right, Y runs away from you. The **front** of the sled is the side with the dust hose.")


def hardware_page():
    section("Every fastener, life size", "Sort your hardware into pots using this page before you start. Screw length is measured from under the head, "
            "except countersunk screws, which are measured overall.")
    groups = [("Small screws", [("m3x8", 20), ("m3x10", 4), ("m3x12", 34), ("m2x10", 2), ("m3nut", 4)]),
              ("Bolts", [("m5x25", 4), ("m5x30", 6), ("m5x40", 4), ("m5csk", 4), ("m6x40", 12)]),
              ("Nuts and washers", [("m5nyl", 12), ("m5nut", 2), ("m5wash", 4), ("m6nut", 12), ("tnut", 12)]),
              ("Bearings and drive parts", [("625", 4), ("lm8uu", 4), ("pulley", 4), ("idler", 4), ("tnutT8", 1), ("coupler", 1)]),
              ("Z axis shafts", [("rod", 2), ("screw", 1)]),
              ("Electrical parts", [("n20", 4), ("switch", 1), ("res", 2), ("rj45", 10), ("wago", 6)]),
              ("Belt and ties", [("belt", 0), ("ziptie", 0)])]
    for title, items in groups:
        add(need(items, title))
    add(box("dyk", "\"M5 x 30\" means a metric thread 5mm across and 30mm long. A **nyloc** nut has a nylon ring that grips the thread, so it stays "
            "wherever you leave it, even loose. That is why the parts that must spin are held with them."))


def before_you_start():
    section("Before you start")
    h2("Tools")
    ul(["Hex keys, 1.5 to 4mm, and small screwdrivers", "8mm and 10mm spanners", "Hacksaw and a round file", "Drill with 3mm and 8mm bits, and a hammer",
        "Tape measure (5m), pencil, string", "Small flat screwdriver (2 to 2.5mm), wire strippers, side cutters", "Multimeter with a continuity beep",
        "A laptop with Python 3"])
    h2("Safety")
    ul(["The router is a mains tool spinning at 30,000 rpm. **Wear eye and ear protection.** Keep hands off the table while it runs.",
        "Plug the router, the vacuum and the 24V power adapter into **one switched extension lead** within arm's reach. That switch is your emergency stop.",
        "Never leave the machine cutting unattended.",
        "**Never plug or unplug a lead with the power on.** It can destroy that motor's driver.",
        "The machine's network leads carry 24V motor current. **Never plug them into a computer or router.** Label them CNC ONLY.",
        "The donor printer's heated bed is mains powered. Unplug the printer and wait 10 minutes before opening it. Do not reuse the bed.",
        "A laser on an open table can blind. Wear glasses rated for its wavelength and keep other people out of the room."])
    h2("Good habits")
    ul(["Lay out the parts for a step before starting it.", "Screws going into plastic: stop as soon as they feel snug. Overtightening strips the hole, and a stripped hole means a reprint.",
        "If a printed hole is tight, twist a drill bit through it by hand.", "Build one corner unit completely and test it before making the other three."])


def printing():
    section("1. Print the parts", "Do this before you take the printer apart. All the files are in the `stl` folder, already turned the right way up. None need supports.")
    h2("Filament and settings")
    p("Use **plain PETG** for everything. It is strong and slightly flexible, so clamps and press fits do not crack, and it copes with a warm motor. "
      "PLA is brittle and slowly deforms under a clamped load, so the router clamp would work loose. You need about **1.75kg** including spares: buy 2kg, or 3kg to allow for a failed print.")
    table([["Setting", "Strong", "Standard", "Light"], ["Used for", "corner brackets, Z carriage, Z bridge", "sled base, tools", "reels, cups, tray, lid, knobs, extras"],
           ["Layer height", "0.2mm", "0.28mm", "0.28mm"], ["Walls", "5", "4", "3"], ["Top / bottom layers", "5 / 4", "4 / 4", "4 / 3"], ["Infill", "35%", "25%", "15%"]], [22, 30, 20, 28])
    p("All three: nozzle 235 to 240°C, bed 80°C, no supports, gyroid infill, and any area under 200mm² printed solid. The presets in `print/orca` set all this for you.")
    p("**The quick way:** the `print` folder has OrcaSlicer presets for your X1 and ten ready-made plates (including the extras below), every part already turned the right way up. "
      "Import the presets, open each plate, pick the preset its name says, print. The full set takes **about 98 hours**. `print/README.md` has the list, times and order.")
    p("**Printed extras:** one more plate holds the 12 hold-down knobs, plus printed replacements for the Z bearings, pinch bearings and belt-end zip ties. "
      "It takes about **7 hours** and **130g**. Ready-to-print G-code for your X1 is in `print/gcode`, and the OpenSCAD source is in `scad`.")
    h2("What to print")
    table([["File", "Qty", "Notes"],
           ["`corner_bracket`", "4", "142 x 176mm. Top face on the bed, fence walls and plug panel pointing up."],
           ["`reel_body`, `reel_flange`", "4 each", "`reel_body` prints with its big flange on the bed."],
           ["`n20_cup`", "4", "Holds the reel motor."],
           ["`f_spacer`, `f_sleeve`, `k_spacer`", "4 each", "Small parts for the posts. Print a spare of each."],
           ["`measuring_cap`", "2", ""],
           ["`sled_base`", "1", "220 x 220mm. Use a brim so the corners do not lift."],
           ["`z_carriage`", "1", "Holds the router."],
           ["`z_bridge`", "1", "Top face on the bed."],
           ["`dust_shoe`", "1", "Bridges 34mm with no support."],
           ["`pen_caddy_body`, `pen_slider`, `thumb_knob` x 4", "1 each", "`pen_slider` must drop freely through the body."],
           ["`laser_caddy`, `laser_shim`", "1 / as needed", "Only if you fit a laser."],
           ["`riser_shim`", "as needed", "See section 7."],
           ["`electronics_tray`, `electronics_lid`", "1 each", "225 x 155mm."]], [38, 14, 48])
    add(box("check", "Test fits as each part comes off the bed: a 65mm router body slides into `z_carriage` with the clamp open; `f_sleeve` spins on an M5 bolt; "
            "an 8mm rod pushes snugly into the sockets of `sled_base` and `z_bridge`; `pen_slider` drops through `pen_caddy_body`. "
            "If a fit is wrong, reprint now, while you still have a printer."))
    add(box("tip", "Print `corner_bracket` first, on its own, and build one whole corner unit with it (section 3). If the pinch gap in step 6 is wrong you will have "
            "wasted one bracket, not four."))


def stripping():
    section("2. Strip the printer", "The Artillery Sidewinder X1 gives you the five motors. I have not seen yours, so check each item as you find it.")
    table([["Keep", "Used for"], ["5 stepper motors with their leads", "4 corner drives and the Z axis. Use the four most alike for the corners."],
           ["Both lead screws with their brass nuts", "One is cut down for the Z axis."], ["Both shaft couplers (on the Z motors)", "Z motor to lead screw."],
           ["The two toothed pulleys on the X and Y motors", "Corner drives, if they are 20-tooth with a 5mm bore."], ["Every screw, a 24V fan", "Spares."]], [45, 55])
    step("Label the motors and cut the lead screw",
         ["Take out the five motors. Label them 1 to 5 with tape. Put the four that look most alike aside for the corners.",
          "Cut one lead screw to **115mm** with a hacksaw. File the cut end smooth so the nut runs on cleanly.",
          "Lay it on the life-size drawing below to check the length."],
         items=[("screw", 1)], warn="The printer's bed runs on mains. Unplug it and wait 10 minutes before you open the base. Do not reuse the bed, its relay or the main board.",
         dyk="These motors are called NEMA17 because their faceplate is 1.7 inches square. Each one moves in 200 exact steps per turn, which is how the machine knows where it is without any sensors.")


def corner():
    section("3. Build the four corner units", "All four are identical. Each one is a motor that winds belt in and out, a post the belt's far end hooks on, "
            "and a reel that stores the slack.")
    add(img("c11_done.png", "pic hero"))
    step("Push in the two bolts", ["Turn `corner_bracket` upside down.", "Push the **M5 x 30** bolt through the hole that sits on its own near the outer edge.",
                                    "Push the **M5 x 25** bolt through the hole right beside the big round motor hole.", "Each head drops into a six-sided pocket, which stops it turning later."],
         "c01_bolts.png", [("m5x30", 1), ("m5x25", 1)], parts=["corner_bracket"],
         tip="The longer bolt goes in the lonely hole. Lay both on the drawings to tell them apart: they differ by only 5mm.")
    step("Fit the motor", ["Hold a stepper against the underside with its shaft up through the big hole and its lead pointing away from the fence walls.",
                            "The motor now covers both bolt heads, so they cannot fall out.", "Turn it right way up and fix the motor with four **M3 x 8** screws from the top. The heads sit down in round recesses."],
         "c02_motor.png", [("m3x8", 4)], warn="Use the 8mm screws here, not longer ones. A screw that is too long bottoms out inside the motor and can crack its end cap.")
    step("Build the belt-end post", ["On the outer bolt, slide `f_spacer` (the fatter ring), then `f_sleeve`, then a washer.", "Add a nyloc nut and tighten until the sleeve **still spins freely**.",
                                      "About 6mm of thread should show above the nut. The measuring cap sits on that later."],
         "c03_post.png", [("m5wash", 1), ("m5nyl", 1)], parts=["f_spacer", "f_sleeve"],
         dyk="The belt's end loop sits on this sleeve. The sleeve turns so the loop can swing round as the sled moves, which keeps the belt length exact.")
    step("Build the pinch post", ["On the bolt beside the motor, slide `k_spacer` with its **small lip upward**.", "Add a 625 bearing, then a nyloc nut with **no washer**.", "Tighten until snug. The outside of the bearing must spin."],
         "c04_pinch.png", [("625", 1), ("m5nyl", 1)], parts=["k_spacer"],
         tip="A printed `pinch_roller` can replace the 625 bearing. It is the same size. Tighten its nut only until the roller still spins freely.",
         warn="No washer here. A washer would rub on the part of the bearing that turns. The spacer's lip is there for the same reason: only the centre of the bearing is clamped.")
    step("Fit the pulley", ["Push a 20-tooth pulley onto the motor shaft with its grub screws at the bottom.", "Leave a gap under it the thickness of a business card.",
                             "Its teeth should be level with the bearing. Tighten one grub screw onto the flat of the shaft, then the other."],
         "c05_pulley.png", [("pulley", 1)],
         dyk="GT2 belt has a tooth every 2mm. A 20-tooth pulley therefore moves exactly 40mm of belt per turn. That fixed number is what makes the machine accurate.")
    step("Check the pinch gap", ["Take a scrap of belt. Hold its teeth against the pulley and slide it between the pulley and the bearing.",
                                  "It should pass with light drag.", "Try to lift the belt off the pulley's teeth beside the bearing. You should not be able to."],
         "c06_gap.png", [("belt", 0)],
         check="**Jams:** ease the pinch bolt's hole in the bracket with a round file and try again. **Belt can lift clear of the teeth:** the gap is too wide, and that bracket needs reprinting. "
               "This is the tightest fit in the whole machine, so get it right on your first bracket before printing the rest.",
         dyk="The bearing never drives anything. Its only job is to stop the belt jumping a tooth when the motor pulls hard.")
    step("Fit the reel motor", ["Push the small N20 motor up into the rectangular pocket under the bracket. Its shaft comes up through the hole.",
                                 "Slide `n20_cup` over it, wires out through the slot.", "Fix the cup with two **M3 x 12** screws."],
         "c07_reelmotor.png", [("n20", 1), ("m3x12", 2)], parts=["n20_cup"],
         tip="Buy N20 motors with wires already soldered on. Their two tabs are tiny and easy to snap.")
    step("Assemble the reel", ["Lay `reel_body` on the bench, big flange down.", "Sit `reel_flange` (the plain disc) on the hub.", "Fix with three **M3 x 12** screws."],
         "c08_reel.png", [("m3x12", 3)], parts=["reel_body", "reel_flange"],
         dyk="The reel holds 5.5m of belt wound flat like a tape measure. Its little motor runs at low power all the time, so it always tugs gently. "
             "The stepper can pull belt off against it, and when the stepper lets belt back, the reel winds it up.")
    step("Push the reel on", ["Line up the flat in the reel's centre hole with the flat on the motor shaft.", "Push the reel down onto the shaft.", "Spin it by hand. It should turn level, clear of the bracket."],
         "c09_reelon.png")
    step("Finished corner unit", "That is one corner unit, apart from its wiring board (section 5). Before you build the other three, do the direction test in section 9 with this one, "
         "or at least repeat the gap check from step 8.", "c11_done.png",
         tip="Write SW, SE, NE or NW on each unit with a paint pen once you decide where it lives. They are identical, but putting each back on the same corner every time keeps your table measurements valid.")


def sled_section():
    section("4. Build the sled", "The sled rides on the workpiece and carries the tool. The belts hook round four idlers near its centre.")
    add(img("s09_done.png", "pic hero tall"))
    step("Fit the four idlers", ["Push four **M5 x 30 countersunk** bolts up through the four holes near the middle of `sled_base`.", "On each, drop a smooth idler onto the raised boss.",
                                  "Add a nyloc nut. The idlers must spin."],
         "s01_idlers.png", [("m5csk", 4), ("idler", 4), ("m5nyl", 4)], parts=["sled_base"],
         check="Run a finger across the underside. Every bolt head must sit **below** the surface, or it will scratch your work. Countersink a little deeper with a drill bit if one is proud.",
         dyk="The belts pull on the sled close to the bit, not at its corners. That lets the bit reach much nearer the edge of the sheet.")
    step("Prepare the carriage", ["Press two **LM8UU** bearings into each side tube of `z_carriage`, from the top.", "Nip each bearing with an **M3 x 12** screw in the small hole in the side of the tube. Just snug.",
                                   "Sit the brass nut on the flat tab at the back, flange on top. Fix it with four **M3 x 10** screws and nuts."],
         "s02_carriage.png", [("lm8uu", 4), ("tnutT8", 1), ("m3x10", 4), ("m3nut", 4), ("m3x12", 4)], parts=["z_carriage"],
         warn="Do not crush the bearings. If a pinch screw is too tight the carriage will bind on the rods. Back it off until the carriage glides.",
         tip="Printed `z_bushing` parts are the same size as LM8UU bearings and press in the same way. Add a drop of light oil to each rod.")
    step("Stand up the rods", ["Push the two 8mm rods into the tall sockets on the base, all the way down.", "Lock each with an **M3 x 12** screw in the side of its socket."],
         "s03_rods.png", [("rod", 2), ("m3x12", 2)])
    step("Slide the carriage on", ["Lower the carriage onto the rods. The clamp slot faces the **front**, the brass nut faces the **back**.", "Slide it up and down by hand."],
         "s04_carriage_on.png", check="The carriage should glide and drop under its own weight. If it sticks, loosen the bearing pinch screws a little, or twist the rods slightly in their sockets until it frees.")
    step("Build up the bridge", ["Sit the fifth stepper on top of `z_bridge`, shaft pointing down through the round hole. Fix with four **M3 x 8** screws from underneath.",
                                  "Push the coupler onto the motor shaft and the cut lead screw into the coupler. Tighten both clamp screws.",
                                  "Screw the microswitch to the small tab that hangs down, on the face that points to the front, lever downward."],
         "s05_bridge.png", [("m3x8", 4), ("coupler", 1), ("screw", 1), ("switch", 1), ("m2x10", 2)], parts=["z_bridge"],
         dyk="The switch tells the machine where \"fully up\" is. Every time you type `homez` the router rises until it clicks the switch, and the machine counts down from there.")
    step("Fit the bridge", ["Hold the bridge above the rod tops.", "Turn the lead screw by hand so it winds into the brass nut as you lower the bridge.", "Push the bridge onto both rods and lock it with an **M3 x 12** screw in each side."],
         "s06_bridge_on.png", [("m3x12", 2)],
         check="Turn the coupler by hand. The carriage should rise and fall smoothly over its whole travel, about 38mm, and click the switch at the top.")
    step("Fit the dust shoe", ["Slide `dust_shoe` in from the front so its round hole sits over the hole in the base.", "Fix with two **M3 x 12** screws through its tabs."],
         "s07_shoe.png", [("m3x12", 2)], parts=["dust_shoe"], tip="Take the dust shoe off for pen and laser work. It is in the way of both.")
    step("Fit the router", ["Slide the router body into the ring from above.", "Drop two **M5 nuts** into the six-sided pockets on the left ear.", "Fit two **M5 x 30** bolts from the right and tighten evenly until the router cannot twist."],
         "s08_router.png", [("m5x30", 2), ("m5nut", 2)],
         tip="Set the router's height in the ring later, when you zero the bit (section 10). For now clamp it so the collet pokes down through the dust shoe.")


def wiring():
    section("5. Wiring", "One main board in a tray drives five motors. Each corner unit joins the tray by an ordinary network lead, and the sled has a fifth. "
            "At each end of every lead is a small breakout board: a network socket with eight numbered screw terminals. Every wire goes under a screw, so there is almost no soldering.")
    add(img("wiring_overview.png", "pic wide", "../renders"))
    add(box("warn", "Everything you wire is 24V or less and cannot shock you. **Never open the power supply.** Unplug from the wall before touching any wiring."))
    step("Learn the screw terminal", ["Strip 6mm of insulation and twist the strands tightly so none stray.", "Undo the terminal screw, push the bare end fully in so no copper shows outside, and tighten firmly.",
                                      "Tug the wire. It must not pull out."], None, [("rj45", 1)],
         tip="Thin wires hold better folded double before they go in. One stray strand touching the next terminal causes faults that are miserable to find, so look closely at every one.")
    add(img("wiring_pinout.png", "pic wide", "../renders"))
    add(box("warn", "The second pair goes on terminals **3 and 6**, not 3 and 4. That matches how the wires are twisted together inside a network lead. It is the mistake most likely to catch you out."))
    step("Find each stepper's wire pairs", ["Set the multimeter to the continuity beep.", "Touch one probe to any motor wire, and the other probe to each of the other three in turn. The one that beeps is its partner.",
                                            "The remaining two are the other pair. Label both pairs with tape."], None,
         dyk="A stepper has two coils inside, and each coil has a wire at both ends. That is why four wires make two pairs. It does not matter which pair goes on terminals 1 and 2: "
             "if a motor turns the wrong way, that is fixed with one word in the settings file.")
    step("Wire the corner units", ["Fix a breakout board to the panel with the grid of holes, socket pointing down. Use M3 screws if the board's holes line up with the grid, or a sticky foam pad and two zip ties through the grid.",
                                   "Cut the stepper's lead so about 150mm stays on the motor. **Keep the off-cut with its plug.**", "One pair into terminals **1 and 2**, the other into **3 and 6**.",
                                   "The reel motor's two wires into terminals **4 and 5**.", "Zip-tie the loose wires to the bracket so nothing tugs on a terminal."],
         "c10_breakout.png", [("rj45", 4), ("ziptie", 0)])
    step("Wire the sled", ["Fix a breakout board on top of the bridge beside the Z motor, using the grid of small holes there.", "Z motor: one pair into terminals **1 and 2**, the other into **3 and 6**.",
                           "Z switch: its two wires into terminals **4 and 5**. Use the switch's two outer tags."], "s09_done.png", [("rj45", 1)],
         tip="Hang the sled's lead, the router flex and the vacuum hose from a hook in the ceiling on a bungee. If they drag on the sled they pull it off line.")
    step("Fit out the tray", ["Fix the main board on M3 standoffs: mark its holes on the tray floor and drill 2.8mm pilot holes.", "Press the five driver modules into their sockets, matching the labels printed on driver and board.",
                              "Stick five breakout boards along the notched wall, one behind each notch. Label them **X=SW, Y=SE, E0=NE, E1=NW, Z=SLED**.",
                              "Plug each motor off-cut into the main board output of that name. Find its pairs and put them into terminals 1 and 2, and 3 and 6, of the matching breakout board.",
                              "Sled board terminals 4 and 5 go to the main board's **Z-** endstop connector: one to the pin marked S, one to the pin marked G."],
         "e01_tray.png", [("rj45", 5)], parts=["electronics_tray", "electronics_lid"],
         warn="A driver module pushed in backwards is destroyed the moment you switch on. Check each one against the labels twice.")
    add(img("wiring_reels.png", "pic wide", "../renders"))
    step("Wire the reel motors", ["Find the main board's **HE0** screw terminals, marked + and -.", "From HE0 +, a wire to one leg of a resistor, joined with a lever connector. From the resistor's other leg, to terminal 4 of the SW board.",
                                  "Terminal 5 of the SW board to terminal 4 of the SE board. Terminal 5 of the SE board back to HE0 -.", "Do the same again with the second resistor for NE and NW, into the same HE0 terminals."],
         None, [("res", 2), ("wago", 4)],
         dyk="Wired in a chain like this, both motors in a pair get exactly the same current, so they pull equally. The resistor limits that current so the motors only tug gently and never overheat.",
         tip="The resistors get warm. Stand them clear of the plastic and of other wires, not taped down.")
    step("Connect the power", ["Use a sealed **24V adapter** rated 5A or more (a brick like a laptop charger). Cut off its round plug and strip the two wires.",
                               "With the adapter plugged in, use the multimeter on DC volts to find which wire is +. Unplug it again.", "Connect + to the main board's power +, and - to -."],
         None, warn="Reversed power kills the board instantly. Check it twice. The printer's own power supply has bare mains terminals once it is out of the printer, so do not run it loose: use the sealed adapter.")
    step("Set the drivers", ["Set the small jumpers under each driver for **16 microsteps**, following the table in the board's manual.",
                             "Set each driver's motor current to about **1A** with its tiny screw. The driver's leaflet gives the voltage to aim for (about 1.2V on common TMC2209 modules)."], None,
         dyk="Microstepping splits each of the motor's 200 steps into 16 smaller ones. That gives 3,200 positions per turn, or 80 for every millimetre of belt.")
    step("Test before you switch on", ["With everything unplugged from the wall, set the multimeter to the continuity beep.", "Each lead, plugged into a board at both ends: terminal 1 to terminal 1 beeps, and so on for 1 to 6.",
                                       "Each corner board: terminals 1 and 2 beep, 3 and 6 beep, 2 and 3 do **not**.", "Main board + to main board - does **not** beep.",
                                       "Now plug in and switch on. Lights come on, and nothing gets warm in the first minute."], None,
         check="If anything smells hot, switch off at once and recheck the power polarity and the driver directions.",
         tip="I worked from the main board's published pin list, not from one in hand. The labels printed on your own board are the authority for the motor pin order, the endstop connector and the + and - marks.")


def software():
    section("6. Software", "The controller runs FluidNC, a free CNC firmware, with one extra module that understands the four belts. You do not need to compile anything: "
            "a ready-made download contains the firmware, the settings file and the setup tools.")
    step("Get the software", ["On GitHub, open the project and click **Actions**, then the latest green **Belt CNC firmware** run.", "Under **Artifacts**, download **belt-cnc-software** and unzip it.",
                              "Install Python 3 from python.org if you do not have it. Then, in a terminal in the unzipped folder, run `pip install pyserial numpy`."], None,
         dyk="That download is rebuilt automatically every time the software changes. Each build compiles the firmware, runs it in a simulator, checks it moves where it is told, and only then packages it.")
    step("Check the tools work", ["In the terminal, run `python3 tools/beltcnc.py test`.", "It runs 22 checks on your computer, with no machine connected, and should end with **all checks passed**."], None)
    step("Put the firmware on the board", ["Connect the main board to the laptop by USB.", "**Mac or Linux:** run `./flash.sh` to list the ports, then `./flash.sh /dev/tty.usbserial-XXXX` with yours.",
                                           "**Windows:** find the port in Device Manager, then run `flash.bat COM5` with yours.", "Wait for it to finish. It takes about a minute."], None,
         tip="If the board is not found, the USB lead may be charge-only. Try another lead before anything else.")
    step("Load the settings", ["Run `python3 tools/beltcnc.py upload --port PORT belt-cnc.yaml`, with your port.", "The board restarts. The tool should report that the **BeltCNC module is running**."], None,
         check="If it reports an error instead, the message names the line of the settings file it did not like.")


def table_setup():
    section("7. Set up the table", "There are two ways to mount the corner units. Pick by how much of the sheet you need to reach.")
    h2("Setup A: units on the sheet's own corners")
    p("Quickest and smallest. Reaches about **70%** of a full sheet. The router cannot hold position within about 210mm of the middle of the long edges or 130mm of the middle of the short edges. "
      "Lay the sheet on 50mm foam board so the motors hang clear of the floor. Leave `belt_dz` at 0 in the settings.")
    add(img("reach_on_corners.png", "pic mid", "../renders"))
    h2("Setup B: end boards")
    p("Reaches about **99%** of a full sheet, with a footprint of 2740 x 1620mm. Cut two boards about 300 x 1620mm. Raise them on 2x2 timber. Lay one under each short end of the sheet, "
      "sticking out 150mm past the short edge and 200mm past both long edges. Support the middle of the sheet at the same height. The corner units go on the outer corners of the end boards. "
      "Set `belt_dz` in the settings to the thickness of your sheet.")
    add(img("reach_with_wings.png", "pic mid", "../renders"))
    add(box("dyk", "The dead zones in setup A are not a fault. Near the middle of an edge the two nearest belts run almost parallel to that edge, so however hard they pull, "
            "very little of the pull points across it. Moving the corners outward steepens the angle. Check any table size with `python3 tools/beltcnc.py reach --width 1200 --height 800`."))
    add(box("tip", "The sled needs support under at least half its base. Along an unsupported edge, plan on a 60mm border, or lay offcuts of the same thickness alongside."))
    step("Fit the mounting studs", ["Hold a corner unit on its corner with both fence walls pushed hard against the edges. Mark through its three holes.", "Drill the three marks **8mm**, right through.",
                                    "From underneath, hammer an M6 T-nut into each hole.", "Screw an **M6 x 40** bolt up through each T-nut from below until it is tight. Each now sticks up as a stud."],
         "t01_mount.png", [("tnut", 3), ("m6x40", 3), ("m6nut", 3)],
         tip="For a one-off sheet you will not use again, skip the studs and drive three wood screws with washers through the holes instead.")
    step("Bolt the units on", ["Press an M6 nut into the hex pocket under each `hold_down_knob`. A few taps with a hammer, or squeeze it in a vice.",
                               "Drop each corner unit over its three studs, fence walls hard against the corner.",
                               "Screw a knob onto each stud. Hand tight is enough."], "t01_mount.png", parts=["hold_down_knob x 3"],
         dyk="The fence does the hard work. The belts pull the unit towards the sheet, straight into the fence, so the knobs only have to hold it down.",
         tip="Print the knobs in a different colour for each corner and you will never put a unit back on the wrong corner.")
    step("Measure the table", ["Put a `measuring_cap` on two belt-end posts. Hook the tape on the flat face of one and read at the flat face of the other.",
                               "Measure five distances, to the millimetre: **S** (SW to SE), **E** (SE to NE), **N** (NW to NE), **W** (SW to NW), and the diagonal **D** (NW to SE).",
                               "Run `python3 tools/beltcnc.py table S E N W D --write belt-cnc.yaml` with your five numbers.", "Upload the settings again (section 6, last step)."],
         "t03_measure.png", parts=["measuring_cap"],
         dyk="Five numbers pin down a four-sided shape completely, even a wonky one. The software works out where every pulley and post is from them, so your table does not need to be square. The tool tells you how far out it is.",
         tip="Measure each distance twice. A 2mm slip here is the commonest reason for a belt going slack later.")
    step("Mark the centre", ["Stretch a string between diagonally opposite belt-end posts. Do the same with the other pair.", "Mark where the strings cross. That is the centre mark. The sled starts every session here."],
         "layout.png", folder="../renders")


def belts():
    section("8. Fit the belts")
    step("Make up four belts", ["Cut four belts. For a full sheet each is **5.6m**. The table tool prints the length for your table.",
                                "At one end, fold 40mm back on itself with the teeth meshed, push the doubled belt through a `belt_clip` and tighten its M3 x 12 screw. (Two small zip ties also work.) The loop left beyond the clip slips over an `f_sleeve`.",
                                "At the other end, fold 10mm over and bind it with one zip tie. This end slides down into the slot in the reel hub."], None, [("belt", 0), ("ziptie", 0)],
         dyk="Each belt runs out to the sled and back, like the rope in a pulley block. That halves the pull each motor has to give and doubles the stiffness, which is why it needs twice the belt.")
    step("Thread each corner", ["Loop over the belt-end post.", "Out round the sled idler, with the **smooth side against the idler**.", "Back to the pulley on the post side, round the outside of the pulley with the **teeth against it**.",
                                "Between the pulley and the pinch bearing.", "Onto the reel. Tuck the end into the hub slot and wind the spare on by hand."], "b01_path.png",
         warn="All four corners must be threaded the same way round. If one is mirrored the machine will not position properly.")
    step("Hook the belts round the sled", "Each belt makes a U-turn round its own idler: the south-west belt round the south-west idler, and so on. With the belts slack you can drop the bend of each one over its idler from above.",
         "b02_sled.png")


def first_run():
    section("9. First power-up", "Connect the laptop by USB and run `python3 tools/beltcnc.py setup --port PORT --config belt-cnc.yaml`. Type the commands shown `like this` at its prompt.")
    step("Check the directions", ["With the belts **off** the sled idlers, type `dirtest`.", "Each corner in turn should pay belt **out**, pause, then take it back.",
                                  "If one pulls in first, the tool tells you which line of the settings file to change. Change it, upload, and repeat.", "Each reel should tug gently in the winding-up direction. If one unwinds, swap its two wires at terminals 4 and 5."], None,
         tip="Do this with your first corner unit on its own, before you build the other three. It proves the whole chain: wiring, driver, firmware and belt path.")
    step("Start at the centre", ["Type `quit`. Hook the belts over the sled idlers.", "Put a V-bit or a pencil in the sled and stand its point on the centre mark, sled edges parallel to the table edges.",
                                 "Switch the controller off and on, then start the setup tool again."], None,
         dyk="The machine has no sensors telling it where the sled is. It simply assumes that when it wakes up, the sled is on the centre mark, and counts motor steps from there.")
    step("Snug the belts", ["Take in belt one corner at a time, for example `sw 5` for 5mm at the south-west, until each belt is straight with no sag.", "Then type `all 0.5` once or twice to add a little tension evenly.",
                            "If the point has drifted off the mark, take in a little on the side it needs to move towards."], None,
         tip="Aim for a loosely strung guitar, not a tight one. Too tight and the motors skip. Too loose and the cut wanders.")
    step("Run the test square", ["Type `square 300 800`. The sled traces a 300mm square at 800mm a minute and returns.", "Then try `square 800 1500`."], None,
         check="The point should come back onto the centre mark, and **no belt should go slack on the way round**. A slack belt means the table measurements are off, or a belt is threaded the wrong way.")
    step("Home the Z axis", "Type `homez`. The router rises until the switch clicks. If it goes down instead, the Z motor is reversed: change it in the settings file the same way as a corner motor.", None)
    h2("Packing away")
    step("Wind the belts in", ["Park the sled on the centre mark and raise Z.", "Type `pack` and unhook the belts when asked. Each corner winds its belt onto its reel, leaving about 150mm out.",
                               "Type `off`, switch off at the wall, unplug the five leads, unscrew the knobs and lift the units off."], None)
    step("Setting up again", ["Bolt each unit back on its own corner, plug in, stand the sled on the centre mark and switch on.", "Type `stowed`, then `unpack`. Each belt pays out to the length it needs.",
                              "Hook the belts on, then snug and test as above."], None,
         dyk="`stowed` moves nothing. It only tells the controller that the belts are wound in, so that `unpack` knows how much to pay out.")


def using():
    section("10. Using it")
    step("Fit the pen holder", ["Take off the dust shoe. Clamp `pen_caddy_body` in the carriage ring, seated on its lip.", "Drop `pen_slider` through it.",
                                "Press a `thumb_knob` onto the head of each **M5 x 40** bolt and screw both into the side of the slider. They cut their own thread.", "Put a pen in and tighten the two knobs. They press the pen into a V, which grips anything from a pencil to a 20mm marker."],
         "p01_pen.png", [("m5x40", 2)], parts=["pen_caddy_body", "pen_slider", "thumb_knob x 2"],
         dyk="The slider floats, so the pen rests on the work under its own weight and follows any dips. For more pressure, loop a rubber band from the two pegs over the top of the slider.")
    step("Draw something first", ["Jog Z down about 15mm from the top. Let the pen touch the surface, tighten, and set Z zero in your sender.", "Make G-code with any program that writes plain G-code: Fusion, Estlcam, Kiri:Moto or Inkscape.",
                                  "Send it with FluidNC's built-in web page or Universal Gcode Sender. Jog to where the job should start and zero X and Y there."], None,
         tip="Draw every job with the pen before you cut it. A wrong drawing costs a sheet of paper. A wrong cut costs a sheet of plywood.")
    step("Calibrate once", ["Run `python3 tools/beltcnc.py dots --table 2440 1220 --inset 300 > dots.gcode` and draw the five dots with the pen.", "Measure the six distances between the dots (run the calibrate command with `--help` for the order).",
                            "Give them to `python3 tools/beltcnc.py calibrate`. It tells you how much to change `steps_per_mm` in the settings."], None,
         dyk="Belts stretch a little under tension, a millimetre or two over a full sheet. Calibration measures that stretch and cancels it out. Expect to do this once and gain a lot.")
    step("Fit a laser (optional)", ["Clamp `laser_caddy` in the ring. Drop the module into the square pocket, packing it with `laser_shim` plates if it is smaller than 40mm.",
                                    "Slide the module up or down to focus, then tighten the two thumb screws.", "Wire its signal input to pin 2 of the main board's EXP1 header, and its power as its maker says."],
         "p02_laser.png", [("m5x40", 2)], parts=["laser_caddy", "thumb_knob x 2"],
         warn="An open diode laser can blind in an instant, including from a reflection. Glasses rated for its wavelength, nobody else in the room, and never over a shiny surface.")
    step("Make your first cuts", ["Zero the bit: jog Z about 15mm down from the top, loosen the clamp, lower the router until the bit touches the wood, tighten, set Z zero.", "Start with the gentle settings below and work up."], None,
         tip="If the cut wanders or a motor clicks, the load is too high. Halve the depth per pass before changing anything else.")
    table([["Setting", "Start with"], ["Bit", "1/8 inch single-flute upcut"], ["Depth per pass", "1.5mm"], ["Feed", "400mm a minute"], ["Plunge", "Ramp in, never straight down"],
           ["Router speed", "Lowest or second lowest"], ["Tabs", "Yes, so cut parts stay put"]], [35, 65])
    add(box("dyk", "An upcut bit's spiral pulls chips up and out of the cut. It also pulls the bit down into the wood, which helps hold the sled flat. "
            "Ramping in means the bit slides down a slope instead of drilling straight in, which is far gentler on a light machine."))


def trouble():
    section("If something is wrong")
    table([["Symptom", "Likely cause"],
           ["A belt goes slack during the test square", "Table measurements are off, or a belt is threaded the wrong way round"],
           ["Sled does not come back to the mark", "A motor skipped: lower the feed, check that driver's current"],
           ["Squares come out as diamonds", "The diagonal D was measured wrongly"],
           ["Everything is slightly too big or small", "Belt stretch: run the calibration"],
           ["Belt jumps teeth at a corner", "Pinch gap too wide: see section 3, step 8"],
           ["Motor buzzes but does not turn", "A wire pair is split: recheck the pairs, and that the second pair is on 3 and 6"],
           ["Motor gets too hot to touch", "Driver current set too high"],
           ["A reel does not wind, or unwinds", "Swap that reel motor's two wires"],
           ["Reels too weak, or loops of slack form", "Fit a lower resistor (82 ohm). If the motors get hot, a higher one"],
           ["Neither reel in a pair turns", "A break in that chain: both leads must be plugged in for either to run"],
           ["Router sinks when powered off", "Park it at the top, or fit a 2mm-lead screw"],
           ["Sled lifts when plunging", "Plunge slower, use an upcut bit, ramp in"],
           ["A motor misbehaves with one particular lead", "That lead is a crossover type or damaged: swap it"]], [42, 58])


def status(ci_ok):
    section("What has and has not been checked")
    h2("Checked on a computer")
    items = ["Every printed part is one solid, fits a 300mm bed and needs no supports.",
             "No part collides with another part, a motor, a bearing or the router, at both ends of the Z travel.",
             "The belt maths in the firmware matches an independent model to within 0.002mm over 400 positions.",
             "The setup tools pass 22 self-checks, including a file transfer and a full snug, test, pack and unpack sequence against a pretend controller.",
             "The reach maps come from a force calculation: 35N per belt from each motor, 15N needed to push the sled."]
    if ci_ok:
        items.insert(2, "The firmware compiles for the controller board, and also runs in FluidNC's own simulator, where it starts up, moves in a straight line to where it is told, and returns.")
    ul(items)
    h2("Not checked")
    ul(["Anything on a physical board or motor. Nothing here has been built.",
        "Any fit that depends on your printer or your particular pulleys, idlers and small motors. The pinch gap is the tightest.",
        "The reels. The resistor value is an estimate. This is the part most likely to need adjusting.",
        "Accuracy while cutting. Expect about 1mm across a sheet after calibration, better over short distances.",
        "The details of the Sidewinder X1 and of the main board's connectors, which I worked out from memory and published pin lists."])


CSS = """
@page { size: A4; margin: 13mm 13mm 15mm 13mm; }
* { box-sizing: border-box; }
html { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; color: #1f2328; }
body { margin: 0; }
h1 { font-size: 19pt; color: #1d5fa8; border-bottom: 0.6mm solid #1d5fa8; padding-bottom: 1.5mm; margin: 0 0 3mm 0; break-before: page; break-after: avoid; }
h2 { font-size: 12.5pt; margin: 5mm 0 2mm 0; break-after: avoid; }
h3 { font-size: 12pt; margin: 0; }
p { margin: 0 0 2.5mm 0; line-height: 1.4; }
p.intro { font-size: 10.5pt; color: #3b4148; }
ul, ol { margin: 0 0 2.5mm 0; padding-left: 6mm; line-height: 1.4; }
li { margin-bottom: 1mm; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.8pt; background: #eef1f4; padding: 0.2mm 1mm; border-radius: 0.8mm; }
table { width: 100%; border-collapse: collapse; margin: 2mm 0 4mm 0; font-size: 9.2pt; break-inside: avoid; }
th { background: #dfe9f5; text-align: left; } th, td { border: 0.2mm solid #b8bfc7; padding: 1.3mm 1.8mm; vertical-align: top; }
.step { border: 0.3mm solid #c9d1d9; border-radius: 3mm; padding: 3.5mm 4.5mm 2.5mm 4.5mm; margin: 0 0 4mm 0; break-inside: avoid; background: #fff; }
.stephead { display: flex; align-items: center; gap: 3mm; margin-bottom: 2.5mm; }
.num { display: inline-flex; align-items: center; justify-content: center; min-width: 8.5mm; height: 8.5mm; border-radius: 4.25mm; background: #1d5fa8; color: #fff; font-weight: 700; font-size: 11.5pt; padding: 0 1.5mm; }
img.pic { display: block; max-width: 100%; max-height: 92mm; margin: 0 auto 2.5mm auto; }
.cols { display: grid; grid-template-columns: 58% 1fr; gap: 4.5mm; align-items: start; margin-bottom: 1mm; }
.cols .note:first-of-type { margin-top: 1mm; }
img.pic.wide { max-height: 105mm; } img.pic.mid { max-height: 68mm; }
img.pic.hero { max-height: 80mm; margin-bottom: 4mm; } img.pic.hero.tall { max-height: 95mm; }
.printed { font-size: 9pt; color: #3b4148; margin-bottom: 2mm; }
.need { border: 0.25mm solid #c9d1d9; background: #f6f8fa; border-radius: 2mm; padding: 2mm 3mm 1.5mm 3mm; margin: 0 0 3mm 0; break-inside: avoid; }
.needtitle { font-weight: 700; font-size: 9pt; color: #57606a; margin-bottom: 1.5mm; } .needtitle span { font-weight: 400; }
.hwrow { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 2.5mm 6mm; }
.hw { display: flex; flex-direction: column; align-items: flex-start; } .hw svg { display: block; } .cap { font-size: 7.6pt; color: #1f2328; margin-top: 0.6mm; }
.note { border-radius: 2mm; padding: 2mm 3mm; margin: 2.5mm 0; font-size: 9.3pt; line-height: 1.38; break-inside: avoid; border-left: 1.4mm solid; }
.notetitle { font-weight: 700; font-size: 8.6pt; text-transform: uppercase; letter-spacing: 0.15mm; margin-bottom: 0.6mm; }
.note.tip { background: #eaf6ec; border-color: #2e8540; } .note.tip .notetitle { color: #226430; }
.note.dyk { background: #eef4fb; border-color: #1d5fa8; } .note.dyk .notetitle { color: #1d5fa8; }
.note.warn { background: #fdf0e6; border-color: #d9541e; } .note.warn .notetitle { color: #b03f10; }
.note.check { background: #f6f1fb; border-color: #7a4bb5; } .note.check .notetitle { color: #5c3691; }
.cover { text-align: left; } .brand { font-size: 44pt; font-weight: 800; color: #1d5fa8; letter-spacing: 0.5mm; margin-top: 6mm; } .sub { font-size: 18pt; color: #57606a; margin-bottom: 4mm; }
img.coverpic { width: 100%; margin: 2mm 0 4mm 0; } p.lead { font-size: 12pt; line-height: 1.45; }
.facts { display: grid; grid-template-columns: 1fr 1fr; gap: 3mm; margin-top: 5mm; } .facts div { background: #f6f8fa; border-radius: 2mm; padding: 2.5mm 3mm; } .facts b { display: block; color: #1d5fa8; font-size: 9pt; text-transform: uppercase; }
.legend div { display: flex; align-items: center; gap: 3mm; margin-bottom: 3mm; line-height: 1.35; }
.swatch { display: inline-block; min-width: 8mm; height: 6mm; border-radius: 1mm; border: 0.3mm solid #1f2328; } .swatch.new { background: linear-gradient(90deg, #5ca3ed 50%, #fa9e4d 50%); } .swatch.old { background: #ccd4db; margin-left: 2mm; } .swatch.hwc { background: #ffcc40; }
.dash { display: inline-block; min-width: 8mm; border-top: 0.6mm dashed #d9541e; }
.ruler { margin: 2mm 0 4mm 0; }
h1.nobreak { break-before: auto; }
"""


def build(ci_ok=True):
    cover(); how_to_read(); hardware_page(); before_you_start(); printing(); stripping(); corner(); sled_section(); wiring(); software(); table_setup(); belts(); first_run(); using(); trouble(); status(ci_ok)
    doc = f'<!doctype html><html><head><meta charset="utf-8"><title>Belt CNC build guide</title><style>{CSS}</style></head><body>{"".join(out)}</body></html>'
    open(os.path.join(HERE, "manual.html"), "w").write(doc)
    print("wrote manual.html:", step_no[0], "steps")


if __name__ == "__main__":
    import sys
    build(ci_ok="--no-ci" not in sys.argv)
