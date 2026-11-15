#!/bin/bash
# add-filament.sh - adds Load/Unload buttons and the runout sensor test to your
# live printer.cfg on the Deck. Safe to run once; makes a backup first.
set -e
KIT="$(cd "$(dirname "$0")" && pwd)"
CFG="$HOME/klipper-deck/printer_data/config/printer.cfg"
ADD="$KIT/filament-addon.cfg"

[ -f "$CFG" ] || { echo "Can't find $CFG. Has Klipper been started at least once?"; exit 1; }
if grep -q "gcode_macro LOAD_FILAMENT" "$CFG"; then
    echo "Already added. Nothing changed."
    exit 0
fi

LATEST="$CFG.bak-$(date +%Y%m%d-%H%M%S)"
cp "$CFG" "$LATEST"
# Insert above the SAVE_CONFIG block if there is one, otherwise at the end
awk -v add="$ADD" '
    BEGIN { while ((getline l < add) > 0) a = a l "\n" }
    /^#\*# <-+ SAVE_CONFIG/ && !done { printf "%s\n", a; done = 1 }
    { print }
    END { if (!done) printf "\n%s", a }
' "$LATEST" > "$CFG"

echo "Added. Backup saved as $LATEST"
echo "Now in Mainsail: click the power icon (top right) > FIRMWARE_RESTART, or type FIRMWARE_RESTART in the console."
