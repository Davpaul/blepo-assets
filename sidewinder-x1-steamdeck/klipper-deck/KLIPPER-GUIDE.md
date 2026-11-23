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
2. Trigger each one by hand and run `QUERY_ENDSTOPS` again. That one should now say **TRIGGERED**.
   - **Z stop:** the small black square block low on the **right-hand upright** (photo: `../z-stop-circled.jpg`). It has no slot: it senses metal. Hold a screwdriver tip against its flat top.
   - **X / Y:** press the switch by hand.
   - If any read the wrong way round (TRIGGERED when nothing is near): see "Fixing a setting" below.
3. Click the **X** home button only. The head should move left and stop on the switch.
   - If it moves the wrong way, power off and flip that axis's direction (see below).
4. Home **Y**, then **Z**. Z homes in the middle of the bed and both Z motors should turn together. It touches down twice (fast, then slow): that's normal.
   - Put a sheet of paper under the nozzle when homing Z. If the paper gets pinched, the nozzle is reaching the bed before the sensor triggers. Turn all four bed knobs ~2 turns to lower the bed, then try again until there's a small gap.
5. Heat test: set the hotend to 200 and the bed to 60 in the temperature panel. Watch both climb steadily. The hotend fan should come on above 50°C. Turn them off after.
6. Move the axes with the jog buttons. That's it moving under Klipper.

## Step 6. Set the nozzle height and level the bed (paper test)

1. `G28`, then `Z_ENDSTOP_CALIBRATE`
2. Paper under the nozzle. Lower with `TESTZ Z=-0.1` (use `TESTZ Z=-1` while it's still well above). Raise with `TESTZ Z=+0.1`.
3. Stop when the paper drags lightly but still slides. If it pinches, go up 0.1.
4. `ACCEPT`, then `SAVE_CONFIG` (Klipper saves it and restarts).
5. `G28`, then `BED_SCREWS_ADJUST`. At each corner turn the knob until the paper drags lightly, then type `ADJUSTED` (or `ACCEPT` if it was already right). Run it twice.

"Move out of range" while lowering means Klipper won't go below zero. `position_min: -5` under `[stepper_z]` in `printer.cfg` allows it (already in new installs).

### Fixing a setting

In Mainsail: **Machine** > `printer.cfg` > edit > **Save & Restart**. (The file also lives on the Deck at `~/klipper-deck/printer_data/config/printer.cfg`.)

- **Endstop reversed:** in that axis's section, change `endstop_pin: ^!PE5` to `endstop_pin: ^PE5` (remove the `!`), or the other way round.
- **Axis moves the wrong way:** add or remove the `!` on its `dir_pin`.

## Step 7. Send prints from your Mac

**OrcaSlicer (recommended):**
1. Add printer: **Artillery > Sidewinder X1**. If it isn't listed, use Sidewinder X2 and set the bed to 300 × 300.
2. Printer settings > **Basic information** > G-code flavour: **Klipper**.
3. Click the Wi-Fi icon next to the printer name > Host type **Octo/Klipper** > Hostname: the Deck's address (e.g. `192.168.1.42`) > **Test** > OK.
4. Slice, then **Print** uploads and starts it, or **Upload** just sends the file. The **Device** tab shows Mainsail inside Orca.

**PrusaSlicer:** printer tab > **Add physical printer** > Host type **OctoPrint** > Hostname: the Deck's address.

**Any slicer:** export the G-code and drag it onto the Mainsail page.

Uploaded files live on the Deck in `~/klipper-deck/printer_data/gcodes`.

---

## Auto-resume after a USB dropout

If the printer's USB connection drops mid-print, `klipper-deck start` deals with it by itself:

1. Spots the dropout in Klipper's log within a couple of seconds.
2. Gets the printer back fast, because the heaters are off and the bed is cooling:
   - waits about 8 seconds for it to reappear by itself
   - if not, switches the dock's USB off and on in software (same as unplugging and replugging the dock)
   - it only accepts *your printer* coming back (it remembers its USB id), not other gadgets on the dock
   - if still not, resets the Deck's whole USB controller
   - gives up after 5 minutes
3. Restarts Klipper on the new connection. If Klipper can't talk to the printer, it resets the dock again and retries.
4. Works out the exact point the printer had reached, backing up about a second so there's no gap.
5. Builds a `RESUME1-yourfile.gcode` and starts it. That file:
   - reheats the bed, then the nozzle to full temperature, **before anything moves**, so a cold nozzle can't rip the print
   - retracts a little, lifts the nozzle 5mm and homes X and Y only. Z is never homed, so it can't crash into the print
   - moves back to the spot and carries on

You'll see "Print auto-resumed after a USB dropout" in Mainsail's console.

**When it won't resume:**
- The print was cancelled, finished, or stopped for a heater or safety error.
- It keeps dropping within 2 minutes of resuming, 3 times in a row (resuming clearly isn't working, so it stops instead of heating and cooling over and over).

There's no limit on how many times it resumes a print otherwise. If you ever want one: `echo 10 > ~/.config/klipper-deck/max-resumes`
- The printer was gone for more than 5 minutes.

**Before trusting it:** while the motors were off, the gantry may have slipped down a little. If the nozzle is resting on the print when you check, stop it and don't resume.

**What to expect:** a small seam or blob where it restarted, and a few strings from the move back. If the bed cooled a lot, the part may have lifted. PETG and PLA on a warm bed usually stay put.

| Do this | Command |
|---|---|
| Resume by hand (e.g. after the Deck crashed or rebooted) | Start Klipper, then `klipper-deck resume`. It asks before starting |
| Turn auto-resume off / on | `klipper-deck autoresume off` / `on` |
| Dock stuck, printer won't reconnect (instead of unplugging the dock) | `klipper-deck usbreset`, then **FIRMWARE RESTART** in Mainsail |

**Updating to get this** (if you installed before it existed):
```bash
cd ~/Downloads/blepo-assets && git pull
cd sidewinder-x1-steamdeck/klipper-deck && bash install.sh
```
The container build is cached, so it's quick. It also:
- turns off USB power saving
- adds the one setting auto-resume needs to your `printer.cfg`, keeping your calibration

Restart Klipper afterwards.

**Fix the cause too.** Auto-resume is a safety net. Dropouts usually come from the dock or hub: plug the printer straight into the Deck's own USB-C port if you can.

## Phone alerts and remote control

### Phone alerts (5 min)

You get an alert when a print starts, pauses, finishes, fails, or hits a USB dropout. Alerts have buttons:

| Alert | Buttons |
|---|---|
| Print started / resumed | Pause · Cancel · Open Mainsail |
| Print paused (e.g. filament ran out) | Resume · Cancel · Open Mainsail |
| USB dropout: recovering → Print resumed | Pause · Cancel · Open Mainsail |
| Print finished / failed / lost (needs you) | Open Mainsail |

Setup:
1. On the Deck: `klipper-deck notify setup`. It prints a topic name like `klipperdeck-3f9a1c2b7e4d` and sends a test alert.
2. On your phone, install the **ntfy** app (free, no account needed). Tap **+** and subscribe to that topic name.
3. Restart Klipper.

Other commands: `klipper-deck notify test`, `klipper-deck notify off`.

Alerts go through the free public ntfy.sh server. Anyone who knew your topic name could read them (file names and status only). That's why the name is random: keep it to yourself.

### Control from anywhere: Tailscale (10 min)

Without this, Mainsail and the alert buttons only work on your home Wi-Fi. Tailscale is a free private network between your own devices. Nothing gets opened to the public internet.

1. On the Deck, from the kit folder:
   ```bash
   bash remote-access.sh
   ```
   It installs Tailscale using Tailscale's own Steam Deck installer, which survives SteamOS updates and starts on boot. Then it shows a QR code: scan it with your phone and sign in.
2. On your phone, install the **Tailscale** app, sign in with the same account and switch it on.
3. Restart Klipper.

Mainsail is now at `http://100.x.x.x` (the script prints the address) from anywhere: work, 4G, someone else's Wi-Fi. The alert buttons switch to that address automatically. In OrcaSlicer on the Mac you can also use that address to upload prints when you're away.

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
| "Lost communication with MCU" mid-move | USB dropout. Auto-resume should pick it up. Fix the cause: printer straight into the Deck's USB-C (not a dock/hub), unplug the touch screen cable from the mainboard, short good cable |
| Can't open the page from the Mac | Use the IP that `klipper-deck status` shows, not `steamdeck.local`. Both devices must be on the same Wi-Fi. If it loads on the Deck but not the Mac, the Deck's firewall is blocking it: run `sudo firewall-cmd --permanent --add-service=http --add-port=7125/tcp && sudo firewall-cmd --reload` |
| After a SteamOS update, USB or port 80 stops working | Run `install.sh` again. Your config and files are kept |

## Later: both printers at once

The Deck can handle it. Each printer needs its own copy with its own ports and data folder. When you're ready, ask me and I'll add a second instance to `klipper-deck`.

## Going back to stock

Nothing here is permanent. To put the stock touch screen setup back, follow `../GUIDE.md` Step 5 (flash the Artillery `.hex` with PrusaSlicer).
