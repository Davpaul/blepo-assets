# Filament on the Sidewinder X1

## 1. What nozzle have I got?

The X1 ships with a **0.4mm** nozzle, and almost everyone keeps that size. Assume 0.4 unless you find otherwise.

To check:
- The size is stamped on one of the flat sides of the nozzle's hex (the brass bit at the very bottom of the print head), e.g. `0.4`. Use your phone torch and zoom in with the camera. If it's crusted in old plastic, heat to 200°C and wipe it with a brass brush or a folded paper towel held in pliers. **It's hot, don't touch.**
- The spare nozzles that came with the printers are usually labelled on the bag or stamped the same way.

If it says something other than 0.4, tell your slicer: printer settings > extruder > nozzle diameter. Klipper itself only needs a change if you go below 0.3 or above 0.6.

## 2. What filament to buy

- **1.75mm PLA** to start. It's the easiest by far. Any brand is fine: eSun, Sunlu, Elegoo, Polymaker, Jayo, etc.
- Hotend **200–210°C**, bed **60°C**.
- Later: PETG (235°C / 80°C) is tougher, but stringier. Avoid flexible TPU at first.

## 3. One-time setup: add the Load / Unload buttons and the sensor

On the Deck, in Konsole:

```bash
cd ~/Downloads/blepo-assets && git pull
bash sidewinder-x1-steamdeck/klipper-deck/add-filament.sh
```

Then in Mainsail's console type `FIRMWARE_RESTART`.

It backs up your `printer.cfg` first, and keeps your saved nozzle height.

You'll now see **LOAD** and **UNLOAD** buttons in the Extruder panel, and three filament sensors in Mainsail (`runout_test_a`, `_b`, `_c`).

## 4. Find which sensor is the real one (2 min)

The X1's runout sensor is the small box on **top of the frame, near the spool holder**. The filament goes through it on its way to the print head.

1. In Mainsail, find the **Filament Sensors** list (Dashboard, under the Miscellaneous / Extruder area).
2. Push a bit of filament into the sensor's hole, then pull it out again. Watch which of the three flips between **detected** and **empty**.
3. In Mainsail: **Machine** > `printer.cfg`. Near the bottom:
   - Delete the two `[filament_switch_sensor runout_test_…]` sections that **didn't** change.
   - In the one that did, change `pause_on_runout: False` to `pause_on_runout: True`. You can also rename it to `[filament_switch_sensor runout]`.
4. **Save & Restart.**

If it shows **detected** when empty and **empty** when loaded, change its `^` to `^!` (e.g. `switch_pin: ^!PE4`).
If **none** of them change, tell me. The sensor may be unplugged or wired elsewhere.

**What it does:** if the filament runs out mid-print, the printer pauses, parks the head and waits. Load new filament (step 5), then press **Resume** in Mainsail. You can switch it on and off with the toggle next to its name.

## 5. Load filament

1. Put the spool on the holder on top of the frame. Filament should come off the **top** of the spool towards the sensor.
2. Cut the end at an angle with side cutters or scissors (a sharp point feeds better), and straighten the last 10cm with your fingers.
3. Feed it through the **runout sensor** hole.
4. Follow it to the **top of the print head**. Squeeze the **extruder lever** on the head (the spring-loaded arm by the gears) and push the filament down into the hole until it stops, about 5–8cm. Let go of the lever.
5. In Mainsail, click **LOAD** in the Extruder panel, or type `LOAD_FILAMENT`. It heats to 200°C and feeds the filament through.
6. When clean plastic is coming out of the nozzle, it's loaded. Pull the blob away with tweezers once it cools a little.
   - Nothing coming out? Click **LOAD** again. Still nothing: the filament probably missed the gears. Press the lever and push harder.
   - Clicking noise from the head: the nozzle may be partly blocked, or it's too cold for that filament.

For PETG type `LOAD_FILAMENT TEMP=235` instead.

## 6. Unload / swap colours

1. Click **UNLOAD**, or type `UNLOAD_FILAMENT`. It heats, pushes a little out, then pulls the filament back.
2. Squeeze the extruder lever and pull the filament out from the top.
3. Snip off the melted end, and tuck the free end into the spool's edge holes so it doesn't unravel.
4. Load the new one (step 5). Let it run until the old colour is gone.

## 7. Quick test print

1. Bed clean: wipe it with isopropyl alcohol and a paper towel. Finger grease stops PLA sticking.
2. Slice a 20mm calibration cube on the Mac (OrcaSlicer: Artillery Sidewinder X1, PLA), and send it to the Deck.
3. Start it from Mainsail and watch the first layer. It should be squished flat and stuck down, not round strands that peel up.
   - Strands are round and lifting: the nozzle is too high. Click **Z offset −0.05** in Mainsail a few times during the first layer.
   - Very thin and see-through, or scraping: the nozzle is too low. Click **+0.05**.
   - Happy with it: after the print, click **Save** next to the Z offset to keep it.
