# Klipper on a Steam Deck: handover notes

You're running on the owner's Steam Deck (SteamOS, Desktop Mode). This folder is the kit that runs their 3D printer. Read this before touching anything.

## The setup

- **Printer:** Artillery Sidewinder X1 (stock MKS Gen L style board, ATmega2560, CH340 USB `1a86:7523`, TMC2100 drivers, dual Z). Flashed with Klipper by `klipper-deck flash`. The stock touch screen is unused.
- **Host:** the Deck, docked. The printer is on the dock's USB. The 5V pin on the USB cable has been taped over (backfeed fix), so the printer only appears on USB while it's powered on.
- **Software:** one podman container (rootless) with Klipper + Moonraker + Mainsail, built from `container/Containerfile`. Versions are pinned there.
- **Data (not in this folder):** `~/klipper-deck/printer_data/` holds `config/` (printer.cfg, moonraker.conf), `gcodes/`, `logs/klippy.log`. Never delete or overwrite these. The owner's nozzle calibration lives in the `SAVE_CONFIG` block at the bottom of printer.cfg.
- **State:** `~/klipper-deck/resume-state.json` (last print snapshot), `usb-topology.json`, `printer-usb-id`. Settings in `~/.config/klipper-deck/` (`notify.json`, `auto-resume`, `max-resumes`, `src`).
- **Installed copies:** `~/.local/bin/klipper-deck` (launcher), `~/.local/share/klipper-deck/guard.py`, `/etc/klipper-deck/usb-reset` (root, passwordless via `/etc/sudoers.d/zz-klipper-deck`).
- **Web:** Mainsail on port 80 at the Deck's LAN IP. Optional Tailscale (`remote-access.sh`) for access from anywhere. firewalld is on; http and 7125 are opened.

## Files here

| File | What it does |
|---|---|
| `klipper-deck` | Launcher: start, stop, flash, logs, status, update, shell, resume, autoresume, usbreset, notify |
| `guard.py` | Runs the container, snapshots the print every 2s, detects USB dropouts in klippy.log, resets the dock in software, reconnects, builds a `RESUMEn-<file>.gcode` and starts it. Also phone alerts (ntfy) |
| `install.sh` | One-time setup and updates. Rebuilds the container (cached), installs launcher and guard, udev rules, firewall, USB autosuspend off, sudo rule, then `add-extras.sh` |
| `add-extras.sh` | Adds missing bits to the live printer.cfg (filament macros, `[force_move]`) and moonraker.conf (Tailscale range). Backs up first, inserts above SAVE_CONFIG |
| `container/defaults/` | Starting printer.cfg / moonraker.conf, only copied if missing |
| `KLIPPER-GUIDE.md`, `FILAMENT-GUIDE.md` | The owner's instructions |

## How auto-resume works (guard.py)

1. While printing or paused, saves a snapshot (file, file_position, temps, Z offset, toolhead position, state).
2. Watches klippy.log for `Got EOF`, `in write: (19)`, `No such device`, `Timeout with MCU`, `Lost communication`.
3. Recovery: wait about 8s for the printer, then `usb-reset hub <dock>`, then `usb-reset controller <pci>`. Only accepts the saved printer USB id; other gadgets such as a `/dev/ttyACM0` are ignored. Gives up after 5 min.
4. Position: the last `Stats ... sd_pos=` line **before** the first error (later ones are unreliable), walking back `buffer_time + 1s` of moves.
5. Resume file: heat bed, heat nozzle (TEMPERATURE_WAIT within 2/3°C, not M109), retract, lift 5mm, `G28 X Y` only (never home Z over a print), purge 8mm at front-left, move back, lower, continue. Z is set with `SET_KINEMATIC_POSITION ... SET_HOMED=Z`, which needs `[force_move] enable_force_move: True`.
6. A RESUME file is always mapped back to the **original** G-code via its header note, `; original: X  resumed at byte N`. Older RESUME files carry every earlier note, so use the **last** note before the first G-code line (`resume_note` / `start_in_original`).
7. Paused prints: uses the real lifted Z (Mainsail's PAUSE lifts about 2mm) and the exact position, then waits for a Continue button rather than starting by itself.
8. No limit on resumes. It stops after 3 dropouts in a row within 120s of resuming.

Manual: `klipper-deck resume` (asks first), `--touch` (lower onto paper on top of the print to measure the true height), `--redo-last` (restart from the furthest point any resume began, with touch-off; lists the files and asks).

## Rules

- **Never stop Klipper, run install.sh, or restart the container while a print is running.** Check first: `curl -s localhost:7125/printer/objects/query?print_stats` and look at `state`.
- Ask the owner before anything that moves the printer, heats it, flashes firmware, or edits printer.cfg/moonraker.conf. Explain what and why in plain words.
- Don't delete files in `printer_data/gcodes` or the config backups without asking.
- Don't expose Moonraker to the internet. It trusts the LAN with no login. Use Tailscale for remote access.
- The owner prefers short, plain answers and step-by-step commands, one per line.

## Handy checks

```bash
klipper-deck status
tail -n 80 ~/klipper-deck/printer_data/logs/klippy.log
grep -n -iE "shutdown|lost communication|Got EOF|No such device" ~/klipper-deck/printer_data/logs/klippy.log | tail
sudo journalctl -k -b | grep -iE "usb|ch341|ttyUSB" | tail -30     # did the USB/dock drop?
curl -s "localhost:7125/printer/objects/query?print_stats&extruder&heater_bed&webhooks"
sudo -k; sudo -n /etc/klipper-deck/usb-reset     # should print usage, not ask for a password
```

## History and open items

- USB dropouts during long prints are the recurring problem. Kernel logs showed the whole dock hub resetting, with other devices and the network dropping at the same moment. Tried so far: other USB devices removed from the dock, a 45W charger, the 5V pin taped. **Not yet known whether the taping fixed it.**
- Heater wobbles about ±3°C. The owner was told to run `PID_CALIBRATE HEATER=extruder TARGET=235` (fan at M106 S128) and `PID_CALIBRATE HEATER=heater_bed TARGET=80`, then `SAVE_CONFIG`. **Not yet confirmed done.**
- Z stop: a metal-sensing square block low on the right upright (`^!PD3`). Z is calibrated with `Z_ENDSTOP_CALIBRATE`, and `position_min: -5`.
- Filament sensor pin unknown: `add-extras` added test sensors on PE4/PG5/PD2. **Not yet confirmed which one is real.**
- Fixed bugs (now in guard.py): wrong device picked after a dropout; sudo rule overridden by SteamOS; the resume count carried across reprints; paused-dropout height off by 2mm; resume-of-resume height; `--redo-last` reading the wrong header note.
- Future: second printer (separate container, ports and data folder). Possibly a BLTouch for true height after a crash.

## Testing changes

Don't test guard.py on a live print. The development copy has offline tests: build a RESUME file with `python3 guard.py make-resume FILE SD_POS BUFFER_TIME OUT` and check it in Klipper batch mode inside the container. After changing anything, re-run `bash install.sh` (only when idle) so the installed copies update.
