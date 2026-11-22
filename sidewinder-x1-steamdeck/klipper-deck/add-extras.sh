#!/bin/bash
# add-extras.sh - adds the kit's extra settings to your live printer.cfg on the Deck:
#   * Load/Unload buttons + filament sensor test   (filament-addon.cfg)
#   * the setting auto-resume needs                 (resume-addon.cfg)
# Only adds what's missing, keeps your calibration, and backs up first.
set -e
KIT="$(cd "$(dirname "$0")" && pwd)"
CFG="$HOME/klipper-deck/printer_data/config/printer.cfg"
[ -f "$CFG" ] || { echo "No printer.cfg yet (start Klipper once first). Skipping."; exit 0; }

add() {   # add <addon file> <text that shows it's already there>
    local addon="$1" marker="$2"
    if grep -qF "$marker" "$CFG"; then
        echo "  $(basename "$addon"): already there"
        return
    fi
    local bak="$CFG.bak-$(date +%Y%m%d-%H%M%S)"
    cp "$CFG" "$bak"
    awk -v add="$addon" '
        BEGIN { while ((getline l < add) > 0) a = a l "\n" }
        /^#\*# <-+ SAVE_CONFIG/ && !done { printf "%s\n", a; done = 1 }
        { print }
        END { if (!done) printf "\n%s", a }
    ' "$bak" > "$CFG"
    echo "  $(basename "$addon"): added (backup: $(basename "$bak"))"
    sleep 1
}

echo "Updating $CFG"
add "$KIT/filament-addon.cfg" "gcode_macro LOAD_FILAMENT"
add "$KIT/resume-addon.cfg" "[force_move]"
echo "Done. If Klipper is running, type FIRMWARE_RESTART in Mainsail's console."
