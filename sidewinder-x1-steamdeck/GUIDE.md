# Sidewinder X1 on a Steam Deck

Goal: get one X1 printing with its own touch screen, using the Steam Deck to slice files and (if needed) put the stock firmware back.

## What the listing means

- **Marlin** is the normal firmware that runs on the printer's mainboard. The touch screen only works with Marlin.
- **Klipper** is a mod where a Raspberry Pi does the thinking and the printer board just follows orders. Without the Pi, a Klipper board does nothing and the touch screen shows "no printer" or stays dead.
- **Z stop** (Z endstop) is the little switch/sensor on the left upright that tells the printer where the bottom of the Z axis is. Every print starts by "homing" down to it. If it's unplugged or knocked out of place, the nozzle will crash into the bed. Nothing to buy, just check it's there and wired.

So: one or both printers may still have Klipper on the board. If so, we flash stock Marlin back. The Deck can do that.

You can't sensibly run Klipper on the Deck itself (it needs a machine left on for every print). Stock Marlin + SD card is the easy route.

## What you need

- Steam Deck in Desktop Mode
- USB-A to USB-B cable (the "printer" type). If your Deck has no dock, a USB-C to USB-B cable or a USB-C hub
- A spare microSD card, 32 GB or smaller, **not your games card**. The Deck's card slot can write print files to it
- Internet on the Deck

---

## Step 1. Physical checks (10 min, printer unplugged)

1. **Voltage switch** under the printer: set to 230V for the UK.
2. **Ribbon cables**: the wide flat cables to the hotend and to the X/Z motors. Push them firmly into their sockets at both ends. These fail on X1s, which is why you got spares.
3. **Z stop**: on the left vertical frame, a small sensor with a cable. Check it's mounted and the cable is plugged in.
4. **Belts**: X and Y belts should be firm, not floppy.
5. **Leftover Pi wiring**: if a USB cable or loose jumper wires are hanging off the mainboard from the old Pi, remove them.

## Step 2. Power on both printers and look at the screens

- **Screen boots and you can tap Home and the printer moves** → that printer has Marlin. Skip to Step 6. Use this one first.
- **Screen says "no printer connected", stays on a logo, or nothing moves** → probably Klipper on the board. Carry on with Step 3.

## Step 3. Set up the Deck (once)

1. Hold the power button > **Switch to Desktop**.
2. Open **Konsole** (app menu > System > Konsole).
3. Set a password if you never have (you'll type it blind, that's normal):
   ```bash
   passwd
   ```
4. Get this folder onto the Deck. Easiest: download it from GitHub in the Deck's browser, or copy it from a USB stick into your `Downloads` folder. Then:
   ```bash
   cd ~/Downloads/sidewinder-x1-steamdeck
   bash setup-deck.sh
   ```
   This installs PrusaSlicer from Flathub, lets it see USB devices, sets USB permissions, and copies the checker to `~/x1/`.

## Step 4. Check what firmware the printer has

1. Plug the printer into the Deck by USB, switch the printer on.
2. In Konsole:
   ```bash
   python3 ~/x1/x1tool.py scan
   python3 ~/x1/x1tool.py check
   ```
3. Read the `RESULT:` line.
   - **"Marlin is running"** → firmware is fine. Go to Step 5b (screen) or Step 6.
   - **"KLIPPER"** or **"No Marlin answer"** → flash stock firmware, Step 5.

## Step 5. Flash stock Marlin with PrusaSlicer

**5a. Mainboard**

1. Download the stock X1 firmware `.hex` file. Two good sources:
   - Artillery's own: `github.com/artillery3d/sidewinder-x1-firmware`
   - Ready-built Marlin 2 for the X1 from 3DPrintBeginner (link at the bottom)

   You want the file ending in **`.hex`**. If it's in a zip, right-click > Extract in the file manager.
2. Open **PrusaSlicer**. Skip the wizard for now if it pops up.
3. Menu **Configuration > Flash Printer Firmware**.
4. **Firmware image**: browse to the `.hex`. **Serial port**: pick `/dev/ttyUSB0` (hit Rescan if blank).
5. Click **Flash!** and wait for "Flashing succeeded". Don't unplug anything mid-flash.
6. If it fails with a timeout: switch off, unplug the printer from the wall, take off the bottom cover, unplug the touch screen cable from the mainboard, and flash again. Plug the screen cable back after.
7. Power cycle the printer, then run `python3 ~/x1/x1tool.py check` again. You should now get "Marlin is running".

**5b. Touch screen (only if it still says "no printer" after 5a)**

The screen has its own firmware. The Artillery firmware download includes a TFT folder with a readme. In short: copy the TFT files to the root of a FAT32 microSD, put it in the printer's card slot, power on, wait for the update bar to finish, then remove the card. Follow the readme in the download for the exact file names, they differ by screen version.

## Step 6. First print

1. **Format the spare microSD** as FAT32: app menu > System > KDE Partition Manager, or use the "Format" option when you right-click the card in Dolphin. Double check it's the spare card.
2. **PrusaSlicer setup**: Configuration > Configuration Wizard > find **Artillery** in the vendor list > tick **Sidewinder X1** > Finish. Pick a PLA filament profile.
3. Load an STL (a 20mm test cube is a good start). Click **Slice now**, then **Export G-code** to the microSD card.
4. Eject the card in Dolphin, put it in the printer.
5. On the printer: **level the bed** first (the X1 has manual levelling, use the screen's levelling menu and a sheet of paper under the nozzle at each corner).
6. Print from the card using the touch screen.

## Optional: print over USB from the Deck

Works, but the Deck must stay awake and plugged in for hours. The SD card is more reliable.

```bash
python3 ~/x1/x1tool.py print ~/Downloads/cube.gcode
```
Turn off sleep first: System Settings > Power Management. Ctrl+C stops the print and turns the heaters off.

To type commands by hand (useful for testing):
```bash
python3 ~/x1/x1tool.py term
```
`M119` shows endstop states (check the Z stop says "TRIGGERED" when you block it), `M105` shows temps, `G28` homes.

---

## If something goes wrong

| Problem | Fix |
|---|---|
| `scan` finds nothing | Printer switched on? Try another cable, plenty are charge-only. |
| "permission denied" | `sudo chmod 666 /dev/ttyUSB0`, or re-run `setup-deck.sh` after a SteamOS update |
| PrusaSlicer shows no serial port | Close it, run `flatpak override --user --device=all com.prusa3d.PrusaSlicer`, reopen |
| Flash times out | Unplug the touch screen cable from the mainboard (Step 5a.6) |
| Nozzle crashes into bed when homing | Z stop unplugged or moved. Check with `M119` in `term` |
| Hotend/fan cuts out mid-print | Ribbon cable. Reseat it or swap in a spare |
| Card not seen by printer | Must be FAT32, and ideally 32 GB or smaller |

## Sources

- [3DPrintBeginner: Sidewinder X1 Marlin firmware guide](https://3dprintbeginner.com/sidewinder-x1-firmware/) (includes flashing with PrusaSlicer and unplugging the TFT cable)
- [SimplyPrint: Artillery compatibility notes](https://simplyprint.io/compatibility/artillery-3d) (points to Artillery's published X1 Marlin source)
- [3DPrintBeginner: custom screen firmware for X1](https://3dprintbeginner.com/custom-screen-firmware-for-sidewinder-x1-and-genius/)
