#!/bin/bash
# Builds Klipper firmware for the Sidewinder X1 mainboard (MKS Gen L, ATmega2560)
# and flashes it over USB. The printer appears inside the container as /dev/printer.
set -e

DEV=/dev/printer
if [ ! -e "$DEV" ]; then
    echo "No printer device passed in. Plug the printer in, switch it on, and try again."
    exit 1
fi

cd /opt/klipper
cat > .config <<'EOF'
CONFIG_MACH_AVR=y
CONFIG_MACH_atmega2560=y
CONFIG_CLOCK_FREQ=16000000
CONFIG_SERIAL=y
CONFIG_SERIAL_BAUD=250000
EOF
make olddefconfig > /dev/null
echo "Building Klipper firmware for ATmega2560..."
make -j"$(nproc)" > /tmp/build.log 2>&1 || { tail -30 /tmp/build.log; exit 1; }
echo "Built out/klipper.elf.hex"

echo "Flashing (about 1 minute, don't unplug anything)..."
if make flash FLASH_DEVICE="$DEV"; then
    echo
    echo "FLASH OK. Power cycle the printer, then run: klipper-deck start"
else
    echo
    echo "FLASH FAILED."
    echo "Most likely cause on the X1: the touch screen shares the board's USB serial line."
    echo "Switch off, unplug the screen cable from the mainboard (under the base), and try again."
    exit 1
fi
