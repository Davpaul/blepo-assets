#!/bin/sh
# Put the Belt CNC firmware on an MKS TinyBee (Mac or Linux).
#   ./flash.sh /dev/tty.usbserial-XXXX      (Mac)
#   ./flash.sh /dev/ttyUSB0                 (Linux)
# Needs Python 3. Installs esptool if it is missing.
set -e
PORT="$1"
if [ -z "$PORT" ]; then
  echo "Usage: ./flash.sh <serial port>"
  echo "Ports that look like a board:"; ls /dev/tty.usb* /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "  (none found: is the board plugged in?)"
  exit 1
fi
cd "$(dirname "$0")"
python3 -m esptool version >/dev/null 2>&1 || python3 -m pip install --user esptool
python3 -m esptool --chip esp32 --port "$PORT" --baud 460800 --before default_reset --after hard_reset \
  write_flash -z --flash_mode dio --flash_freq 80m --flash_size detect \
  0x1000 firmware/bootloader.bin 0x8000 firmware/partitions.bin 0xe000 firmware/boot_app0.bin \
  0x10000 firmware/firmware.bin @FS_OFFSET@ firmware/littlefs.bin
echo
echo "Done. Now load the settings:  python3 tools/upload_config.py --port $PORT belt-cnc.yaml"
