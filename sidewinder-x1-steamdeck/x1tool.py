#!/usr/bin/env python3
"""
x1tool.py - talk to an Artillery Sidewinder X1 over USB from a Steam Deck (or any Linux box).

No installs needed: uses only the Python that ships with SteamOS.
If the optional 'pyserial' package happens to be installed it is used too,
which lets the tool also try 250000 baud (common with Klipper/custom Marlin).

Commands:
  python3 x1tool.py scan              list USB serial devices and guess what board each is
  python3 x1tool.py check             find the printer and work out what firmware it runs
  python3 x1tool.py term              type G-code by hand (M105 = temps, G28 = home, etc.)
  python3 x1tool.py print FILE.gcode  stream a sliced file over USB (SD card is more reliable)

Options:
  --port /dev/ttyUSB0   pick the port yourself
  --baud 115200         pick the baud rate yourself
"""

import argparse
import glob
import os
import re
import select
import sys
import termios
import threading
import time

KNOWN_USB = {
    ("1a86", "7523"): "CH340 USB-serial chip. This is the stock Sidewinder X1 mainboard (ATmega2560, MKS-style).",
    ("0483", "5740"): "STM32 board running Marlin (newer Artillery 'Ruby' style board).",
    ("1d50", "614e"): "Board running KLIPPER firmware (native USB). Needs stock firmware put back for the touch screen.",
    ("2341", "0042"): "Arduino Mega 2560.",
    ("0403", "6001"): "FTDI USB-serial chip.",
}

BAUDS = [115200, 250000]


# ---------------------------------------------------------------- serial layer

class StdlibPort:
    """Minimal raw serial port using termios. Supports standard baud rates only."""

    SPEEDS = {9600: termios.B9600, 57600: termios.B57600, 115200: termios.B115200}

    def __init__(self, path, baud):
        if baud not in self.SPEEDS:
            raise ValueError(f"{baud} baud needs pyserial (pip install pyserial)")
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        attrs = termios.tcgetattr(self.fd)
        cc = attrs[6]
        cc[termios.VMIN] = 0
        cc[termios.VTIME] = 0
        speed = self.SPEEDS[baud]
        cflag = termios.CS8 | termios.CREAD | termios.CLOCAL | termios.HUPCL
        termios.tcsetattr(self.fd, termios.TCSANOW, [0, 0, cflag, 0, speed, speed, cc])
        termios.tcflush(self.fd, termios.TCIOFLUSH)

    def write(self, data):
        os.write(self.fd, data)

    def read(self, timeout):
        r, _, _ = select.select([self.fd], [], [], timeout)
        if not r:
            return b""
        try:
            return os.read(self.fd, 4096)
        except BlockingIOError:
            return b""

    def close(self):
        os.close(self.fd)


class PyserialPort:
    def __init__(self, path, baud):
        import serial  # noqa: optional
        self.s = serial.Serial(path, baud, timeout=0)

    def write(self, data):
        self.s.write(data)

    def read(self, timeout):
        end = time.time() + timeout
        while time.time() < end:
            n = self.s.in_waiting
            if n:
                return self.s.read(n)
            time.sleep(0.02)
        return b""

    def close(self):
        self.s.close()


def have_pyserial():
    try:
        import serial  # noqa
        return True
    except ImportError:
        return False


def open_port(path, baud):
    if have_pyserial():
        return PyserialPort(path, baud)
    return StdlibPort(path, baud)


class LineReader:
    def __init__(self, port):
        self.port = port
        self.buf = b""

    def readline(self, timeout):
        end = time.time() + timeout
        while b"\n" not in self.buf:
            left = end - time.time()
            if left <= 0:
                return None
            self.buf += self.port.read(min(left, 0.2))
        line, self.buf = self.buf.split(b"\n", 1)
        return line.decode("utf-8", "replace").strip()


# ---------------------------------------------------------------- helpers

def usb_ids(tty):
    """Walk sysfs up from /sys/class/tty/<tty>/device to find idVendor/idProduct."""
    p = os.path.realpath(f"/sys/class/tty/{tty}/device")
    for _ in range(6):
        v, d = os.path.join(p, "idVendor"), os.path.join(p, "idProduct")
        if os.path.exists(v) and os.path.exists(d):
            return open(v).read().strip(), open(d).read().strip()
        p = os.path.dirname(p)
    return None, None


def find_ports():
    return sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))


def permission_hint(path):
    print(f"\n  Can't open {path}: permission denied.")
    print("  Quick fix for this session:")
    print(f"    sudo chmod 666 {path}")
    print("  Permanent fix: run setup-deck.sh again, then log out and back in.\n")


def pick_port(args):
    if args.port:
        return args.port
    ports = find_ports()
    if not ports:
        print("No USB serial device found.")
        print("  - Is the printer switched on and the USB cable plugged into the Deck (or its dock)?")
        print("  - Try a different cable. Some USB cables are charge-only.")
        sys.exit(1)
    if len(ports) > 1:
        print(f"Found several ports, using {ports[0]}. Use --port to pick another: {', '.join(ports)}")
    return ports[0]


# ---------------------------------------------------------------- commands

def cmd_scan(args):
    ports = find_ports()
    if not ports:
        print("No USB serial devices found. Plug the printer in and switch it on.")
        return
    for p in ports:
        tty = os.path.basename(p)
        vid, pid = usb_ids(tty)
        desc = KNOWN_USB.get((vid, pid), "Unknown device.")
        print(f"{p}  [{vid}:{pid}]  {desc}")


def probe(path, baud):
    """Open the port, let the board reboot, send M115. Returns (lines, firmware_line)."""
    port = open_port(path, baud)
    rd = LineReader(port)
    lines = []
    # Opening the port resets the ATmega board. Collect its boot chatter.
    end = time.time() + 4
    while time.time() < end:
        line = rd.readline(0.5)
        if line:
            lines.append(line)
    port.write(b"\nM115\n")
    end = time.time() + 3
    fw = None
    while time.time() < end:
        line = rd.readline(0.5)
        if line:
            lines.append(line)
            if "FIRMWARE_NAME" in line:
                fw = line
    port.close()
    return lines, fw


def cmd_check(args):
    path = pick_port(args)
    tty = os.path.basename(path)
    vid, pid = usb_ids(tty)
    print(f"Port: {path}  USB id {vid}:{pid}")
    print(f"Board guess: {KNOWN_USB.get((vid, pid), 'unknown')}\n")

    if (vid, pid) == ("1d50", "614e"):
        print("RESULT: KLIPPER firmware is on this board. See GUIDE.md step 4 to put stock firmware back.")
        return

    bauds = [args.baud] if args.baud else BAUDS
    if not have_pyserial():
        bauds = [b for b in bauds if b in StdlibPort.SPEEDS] or [115200]

    for baud in bauds:
        print(f"Trying {baud} baud (board will reboot, takes ~7s)...")
        try:
            lines, fw = probe(path, baud)
        except PermissionError:
            permission_hint(path)
            sys.exit(1)
        except ValueError as e:
            print(f"  skipped: {e}")
            continue
        readable = [l for l in lines if re.search(r"[A-Za-z]{3}", l)]
        for l in readable[:15]:
            print("   ", l)
        if fw:
            name = re.search(r"FIRMWARE_NAME:([^ ]+(?: [^ :]+)?)", fw)
            print(f"\nRESULT: Marlin is running at {baud} baud ({name.group(1) if name else fw}).")
            print("The board firmware is fine. If the touch screen still does nothing, see GUIDE.md step 5.")
            return
        if any("ok" == l or l.startswith("ok ") for l in lines) or any("echo:" in l for l in lines):
            print(f"\nRESULT: Marlin-like replies at {baud} baud but no version line. Probably usable.")
            return
        print("  no Marlin reply at this speed.\n")

    print("RESULT: No Marlin answer.")
    if not have_pyserial():
        print("  Only 115200 baud was tried. To also try 250000:")
        print("    python3 -m venv ~/x1env && ~/x1env/bin/pip install pyserial")
        print("    ~/x1env/bin/python x1tool.py check")
    print("  If 250000 also gives nothing readable, the board is most likely running KLIPPER.")
    print("  That matches the seller's note. Go to GUIDE.md step 4 and flash stock firmware.")


def cmd_term(args):
    path = pick_port(args)
    baud = args.baud or 115200
    try:
        port = open_port(path, baud)
    except PermissionError:
        permission_hint(path)
        sys.exit(1)
    print(f"Connected to {path} at {baud}. Type G-code and press Enter. Ctrl+C to quit.")
    print("Handy: M115 (firmware info)  M105 (temps)  G28 (home all)  M119 (endstop states)")
    stop = threading.Event()

    def reader():
        rd = LineReader(port)
        while not stop.is_set():
            line = rd.readline(0.3)
            if line:
                print(f"< {line}")

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    try:
        for line in sys.stdin:
            port.write((line.strip() + "\n").encode())
    except KeyboardInterrupt:
        pass
    stop.set()
    port.close()


def clean_gcode(path):
    with open(path, "r", errors="replace") as f:
        for raw in f:
            line = raw.split(";", 1)[0].strip()
            if line:
                yield line


def cmd_print(args):
    path = pick_port(args)
    baud = args.baud or 115200
    lines = list(clean_gcode(args.file))
    print(f"{len(lines)} commands to send. Keep the Deck awake and plugged in for the whole print.")
    print("Tip: in Desktop Mode, System Settings > Power Management, turn off screen/suspend timers.\n")
    try:
        port = open_port(path, baud)
    except PermissionError:
        permission_hint(path)
        sys.exit(1)
    rd = LineReader(port)
    time.sleep(4)  # board reboot on connect
    while rd.readline(0.5) is not None:
        pass

    start = time.time()
    try:
        for i, cmd in enumerate(lines, 1):
            port.write((cmd + "\n").encode())
            last_rx = time.time()
            while True:
                reply = rd.readline(1)
                if reply is None:
                    if time.time() - last_rx > 120:
                        raise RuntimeError(f"Printer stopped answering at line {i}: {cmd}")
                    continue
                last_rx = time.time()
                if reply.startswith("ok"):
                    break
                if reply.lower().startswith("error"):
                    print(f"\n! printer error: {reply}")
                    if "kill" in reply.lower() or "halted" in reply.lower():
                        raise RuntimeError("Printer halted.")
                if reply.startswith("Resend"):
                    port.write((cmd + "\n").encode())
            if i % 25 == 0 or i == len(lines):
                pct = 100 * i / len(lines)
                mins = (time.time() - start) / 60
                print(f"\r  {pct:5.1f}%  line {i}/{len(lines)}  {mins:5.1f} min", end="", flush=True)
    except KeyboardInterrupt:
        print("\nStopping: turning heaters off.")
        port.write(b"M104 S0\nM140 S0\nM84\n")
    except RuntimeError as e:
        print(f"\n{e}")
        port.write(b"M104 S0\nM140 S0\n")
    finally:
        time.sleep(0.5)
        port.close()
    print("\nDone.")


def main():
    ap = argparse.ArgumentParser(description="Artillery Sidewinder X1 helper for Steam Deck")
    ap.add_argument("--port")
    ap.add_argument("--baud", type=int)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan")
    sub.add_parser("check")
    sub.add_parser("term")
    p = sub.add_parser("print")
    p.add_argument("file")
    args = ap.parse_args()
    {"scan": cmd_scan, "check": cmd_check, "term": cmd_term, "print": cmd_print}[args.cmd](args)


if __name__ == "__main__":
    main()
