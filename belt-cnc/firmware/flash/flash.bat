@echo off
rem Put the Belt CNC firmware on an MKS TinyBee (Windows).
rem   flash.bat COM5
rem Needs Python 3 from python.org. Installs esptool if it is missing.
if "%1"=="" (
  echo Usage: flash.bat COMx
  echo Find the port in Device Manager under "Ports (COM and LPT)".
  exit /b 1
)
cd /d "%~dp0"
python -m esptool version >nul 2>&1 || python -m pip install --user esptool
python -m esptool --chip esp32 --port %1 --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 80m --flash_size detect 0x1000 firmware\bootloader.bin 0x8000 firmware\partitions.bin 0xe000 firmware\boot_app0.bin 0x10000 firmware\firmware.bin @FS_OFFSET@ firmware\littlefs.bin
echo.
echo Done. Now load the settings:  python tools\upload_config.py --port %1 belt-cnc.yaml
