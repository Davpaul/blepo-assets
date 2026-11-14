# Klipper on the Steam Deck: Sidewinder X1

The Deck runs Klipper in a container. You control the printer from a web page (Mainsail) on any device on your home network, and your Mac's slicer sends files straight to it.

**Time:** about 30 minutes, most of it waiting for the install.

## What you need

- Steam Deck on its charger, connected to your home Wi-Fi
- USB cable from the printer to the Deck (USB-B on the printer end; a USB-C hub or dock on the Deck end)
- Your sudo password (you'll set one in Step 1 if you haven't)

---

## Step 1. Get the kit onto the Deck (5 min)

1. Hold the power button > **Switch to Desktop**.
2. In the Deck's browser, sign in to GitHub and download this branch as a zip:
   `github.com/davpaul/blepo-assets` > branch **claude/epic-mendel-zwt7bu** > **Code** > **Download ZIP**
3. Open **Dolphin** (file manager) > Downloads > right-click the zip > **Extract > Extract archive here**.
4. Open **Konsole** (app menu > System > Konsole). If you've never set a password (you'll be typing blind, that's normal):
   ```bash
   passwd
   ```

## Step 2. Install (10–15 min, mostly waiting)

```bash
cd ~/Downloads/blepo-assets-claude-epic-mendel-zwt7bu/sidewinder-x1-steamdeck/klipper-deck
bash install.sh
```

What it does:
- Checks that podman (the container tool built into SteamOS) is there
- Gives your user access to USB printers and lets the web page use normal port 80
- Builds the container: Klipper, Moonraker (the control API) and Mainsail (the web page)
- Adds a `klipper-deck` command and a **Start Klipper** icon on the desktop

When it ends with **Installed.**, close Konsole and open a new one so the command is picked up.

## Step 3. Put fresh Klipper firmware on the printer (2 min)

The board already has Klipper on it, but it's an unknown version and Klipper needs the board and the Deck to match. Reflashing removes the guesswork.

1. Plug the printer into the Deck by USB, and switch the printer on.
2. Run:
   ```bash
   klipper-deck flash
   ```
3. Wait for **FLASH OK**, then switch the printer off and on again.

**If it says FLASH FAILED:** the X1's touch screen shares the board's USB line. Switch the printer off at the wall, take the bottom cover off, unplug the screen's cable from the mainboard, and run `klipper-deck flash` again. Leave the screen cable unplugged: it doesn't work under Klipper anyway, and it can disrupt Klipper's connection.

## Step 4. Start it

Double-click **Start Klipper** on the desktop, or run:

```bash
klipper-deck start
```

You'll see something like:

```
Mainsail:          http://192.168.1.42
Slicer upload:     host 192.168.1.42:80  (type: Octo/Klipper or OctoPrint)
```

Open that address on your Mac, phone, or the Deck itself. Bookmark it.

**Keep the Konsole window open.** While it's open, the Deck won't go to sleep. Close it or press Ctrl+C to stop Klipper.

## Step 5. First movement safety checks (no filament needed)

Keep a hand near the printer's power switch for these. In Mainsail, click **Console**:

1. Type `QUERY_ENDSTOPS`. All three should say **open**.
2. Hold something in the Z stop sensor (or press the X / Y switch by hand) and run `QUERY_ENDSTOPS` again. That one should now say **TRIGGERED**.
   - If they're the wrong way round (TRIGGERED when nothing is pressed): see "Fixing a setting" below.
3. Click the **X** home button only. The head should move left and stop on the switch.
   - If it moves the wrong way, power off and flip that axis's direction (see below).
4. Home **Y**, then **Z**. Z homes in the middle of the bed and both Z motors should turn together.
5. Heat test: set the hotend to 200 and the bed to 60 in the temperature panel. Watch both climb steadily. The hotend fan should come on above 50°C. Turn them off after.
6. Move the axes with the jog buttons. That's it moving under Klipper.

### Fixing a setting

In Mainsail: **Machine** > `printer.cfg` > edit > **Save & Restart**. (The file also lives on the Deck at `~/klipper-deck/printer_data/config/printer.cfg`.)

- **Endstop reversed:** in that axis's section, change `endstop_pin: ^!PE5` to `endstop_pin: ^PE5` (remove the `!`), or the other way round.
- **Axis moves the wrong way:** add or remove the `!` on its `dir_pin`.

## Step 6. Send prints from your Mac

**OrcaSlicer (recommended):**
1. Add printer: **Artillery > Sidewinder X1**. If it isn't listed, use Sidewinder X2 and set the bed to 300 × 300.
2. Printer settings > **Basic information** > G-code flavour: **Klipper**.
3. Click the Wi-Fi icon next to the printer name > Host type **Octo/Klipper** > Hostname: the Deck's address (e.g. `192.168.1.42`) > **Test** > OK.
4. Slice, then **Print** uploads and starts it, or **Upload** just sends the file. The **Device** tab shows Mainsail inside Orca.

**PrusaSlicer:** printer tab > **Add physical printer** > Host type **OctoPrint** > Hostname: the Deck's address.

**Any slicer:** export the G-code and drag it onto the Mainsail page.

Uploaded files live on the Deck in `~/klipper-deck/printer_data/gcodes`.

---

## Day-to-day

| Do this | Command |
|---|---|
| Start | Double-click **Start Klipper**, or `klipper-deck start` |
| Stop | Close the window, Ctrl+C, or `klipper-deck stop` |
| Is it running / what's the address | `klipper-deck status` |
| Watch the log | `klipper-deck logs` |
| Rebuild after updating the kit | `klipper-deck update` |

**Stay in Desktop Mode while printing.** Switching to Game Mode can let Steam suspend the Deck. For extra safety: System Settings > Power Management > On AC Power > turn off **Suspend session**.

## Showing it to Claude

I can't reach your home network from here. When something looks off, paste me:
- a screenshot of the Mainsail page, or
- the end of the log: `tail -n 80 ~/klipper-deck/printer_data/logs/klippy.log`

## If something goes wrong

| What you see | Fix |
|---|---|
| `podman isn't installed` | Update SteamOS, then run `install.sh` again |
| `install.sh` stops at the build with "429" or "too many requests" | Docker Hub is busy. Run: `podman build --build-arg BASE=public.ecr.aws/docker/library/debian:trixie-slim -t localhost/klipper-deck -f container/Containerfile container` from the kit folder |
| `klipper-deck: command not found` | Open a new Konsole window, or use `~/.local/bin/klipper-deck` |
| `No printer found` | Printer on? Try another cable (plenty are charge-only) |
| Mainsail: "mcu: Unable to connect" | Printer off, or it needs flashing: `klipper-deck stop`, then `klipper-deck flash` |
| Mainsail: "protocol error" / "version mismatch" | `klipper-deck flash` |
| "Lost communication with MCU" mid-move | Unplug the touch screen cable from the mainboard (Step 3) |
| Can't open the page from the Mac | Use the IP that `klipper-deck status` shows, not `steamdeck.local`. Both devices must be on the same Wi-Fi. If it loads on the Deck but not the Mac, the Deck's firewall is blocking it: run `sudo firewall-cmd --permanent --add-service=http --add-port=7125/tcp && sudo firewall-cmd --reload` |
| After a SteamOS update, USB or port 80 stops working | Run `install.sh` again. Your config and files are kept |

## Later: both printers at once

The Deck can handle it. Each printer needs its own copy with its own ports and data folder. When you're ready, ask me and I'll add a second instance to `klipper-deck`.

## Going back to stock

Nothing here is permanent. To put the stock touch screen setup back, follow `../GUIDE.md` Step 5 (flash the Artillery `.hex` with PrusaSlicer).
