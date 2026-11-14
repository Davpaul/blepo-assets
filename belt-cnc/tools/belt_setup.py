"""Talk to the controller to check motor directions, snug the belts and test.

Connect over USB (needs:  pip install pyserial)  or over Wi-Fi:

    python3 belt_setup.py --port /dev/ttyUSB0        (Windows: --port COM5)
    python3 belt_setup.py --host 192.168.0.42

Then type commands at the prompt. Type  help  for the list.

How snugging works: every corner has a "trim", extra belt paid out (+) or
taken in (-). The sled is assumed to be sitting at the table centre when the
controller boots. You take in belt at each corner until all four are snug and
the bit is still over the centre mark. Nothing here is saved: do it each time
you set the machine up.
"""
import argparse, re, socket, sys, time

CORNERS = ["sw", "se", "ne", "nw"]


class Link:
    def __init__(self, port=None, baud=115200, host=None, tcp_port=23):
        if host:
            self.sock = socket.create_connection((host, tcp_port), timeout=5)
            self.sock.settimeout(0.2)
            self.ser = None
        else:
            import serial
            self.ser = serial.Serial(port, baud, timeout=0.2)
            self.sock = None
        self.buf = b""
        self.machine_coords = True
        time.sleep(1.0)
        self._read()

    def _read(self):
        try:
            data = self.ser.read(4096) if self.ser else self.sock.recv(4096)
        except (socket.timeout, BlockingIOError):
            data = b""
        self.buf += data or b""

    def _lines(self):
        while b"\n" in self.buf:
            line, self.buf = self.buf.split(b"\n", 1)
            yield line.decode(errors="replace").strip()

    def write(self, text):
        raw = text.encode()
        self.ser.write(raw) if self.ser else self.sock.sendall(raw)

    def send(self, line, timeout=20.0, quiet=False):
        """Send one line and wait for ok / error."""
        self.write(line + "\n")
        end, out = time.time() + timeout, []
        while time.time() < end:
            self._read()
            for ln in self._lines():
                if ln == "ok":
                    return out
                if ln.startswith("error") or ln.startswith("ALARM"):
                    if not quiet:
                        print("   controller says:", ln)
                    return out + [ln]
                if ln:
                    out.append(ln)
        print("   (no reply to", repr(line), ")")
        return out

    def status(self):
        self.write("?")
        end = time.time() + 2
        while time.time() < end:
            self._read()
            for ln in self._lines():
                m = re.match(r"<(\w+).*?(M|W)Pos:([-\d.,]+)", ln)
                if m:
                    self.machine_coords = m.group(2) == "M"
                    return m.group(1), [float(v) for v in m.group(3).split(",")]
        return None, None

    def wait_idle(self, timeout=120):
        end = time.time() + timeout
        while time.time() < end:
            state, pos = self.status()
            if state == "Idle":
                return pos
            time.sleep(0.2)
        print("   (machine did not go idle)")
        return None


class Setup:
    def __init__(self, link):
        self.l = link
        self.trim = dict.fromkeys(CORNERS, 0.0)

    def apply(self, feed=300):
        """Trims take effect on the next move, so send a move to where we already are."""
        pos = self.l.wait_idle()
        if pos is None:
            return
        self.l.send(f"{self.g53()}G90 G1 X{pos[0]:.3f} Y{pos[1]:.3f} F{feed}")
        self.l.wait_idle()

    def g53(self):
        # positions are sent back in whichever coordinates the controller reports them in
        return "G53 " if self.l.machine_coords else ""

    def set_trim(self, corner, value):
        self.trim[corner] = value
        self.l.send(f"$/kinematics/BeltCNC/{corner}_trim={value:.3f}")

    def show(self):
        state, pos = self.l.status()
        print(f"   state {state}   X {pos[0]:.2f}  Y {pos[1]:.2f}  Z {pos[2]:.2f}" if pos else "   no status")
        print("   trims (mm of belt):  " + "   ".join(f"{c.upper()} {self.trim[c]:+.1f}" for c in CORNERS))

    def cmd_take(self, corner, mm):
        for c in (CORNERS if corner == "all" else [corner]):
            self.set_trim(c, self.trim[c] - mm)
        self.apply()
        self.show()

    def cmd_dirtest(self):
        print("   Each corner in turn pays OUT 20 mm of belt, waits, then takes it back.")
        print("   Watch the belt at that corner. If it pulls IN first, that motor is reversed:")
        print("   add or remove ':low' on its direction_pin in the config file.")
        for c in CORNERS:
            input(f"   Press Enter to test {c.upper()} ...")
            self.set_trim(c, self.trim[c] + 20); self.apply()
            time.sleep(1.0)
            self.set_trim(c, self.trim[c] - 20); self.apply()

    def cmd_square(self, size, feed):
        state, pos = self.l.status()
        x, y = pos[0], pos[1]
        h = size / 2
        print(f"   Tracing a {size:.0f} mm square about the centre at {feed:.0f} mm/min, then returning.")
        for px, py in ((x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h), (x - h, y - h), (x, y)):
            self.l.send(f"{self.g53()}G90 G1 X{px:.3f} Y{py:.3f} F{feed}")
        self.l.wait_idle(600)
        print("   Done. The bit should be back over the centre mark, and no belt should have gone slack on the way.")

    def run(self):
        print(__doc__.split("How snugging works")[0].split("Then type")[0].strip().splitlines()[0])
        self.cmd_help()
        while True:
            try:
                words = input("belt> ").strip().lower().split()
            except (EOFError, KeyboardInterrupt):
                break
            if not words:
                continue
            w = words[0]
            try:
                if w in ("q", "quit", "exit"):
                    break
                elif w == "help":
                    self.cmd_help()
                elif w == "status":
                    self.show()
                elif w == "dirtest":
                    self.cmd_dirtest()
                elif w in CORNERS or w == "all":
                    self.cmd_take(w, float(words[1]) if len(words) > 1 else 1.0)
                elif w == "zero":
                    for c in CORNERS:
                        self.set_trim(c, 0.0)
                    self.apply(); self.show()
                elif w == "centre" or w == "center":
                    self.l.send("$HX"); self.l.send("$HY"); self.show()
                elif w == "square":
                    self.cmd_square(float(words[1]) if len(words) > 1 else 300.0, float(words[2]) if len(words) > 2 else 800.0)
                elif w == "homez":
                    self.l.send("$HZ", timeout=60); self.show()
                elif w == "off":
                    self.l.send("$MD"); print("   motors released")
                elif w == "raw":
                    for ln in self.l.send(" ".join(words[1:]).upper() if words[1:] else "$I"):
                        print("   " + ln)
                else:
                    print("   unknown command, type help")
            except (ValueError, IndexError):
                print("   could not understand that, type help")

    @staticmethod
    def cmd_help():
        print("""
  dirtest          check each motor turns the right way (do this first, belts off the sled)
  sw 2             take IN 2 mm of belt at the south-west corner (also se, ne, nw)
  sw -2            pay OUT 2 mm at that corner
  all 0.5          take in 0.5 mm at all four corners (adds tension evenly)
  zero             put all trims back to nothing
  centre           tell the controller "the bit is over the centre mark right now"
  square 300 800   trace a 300 mm square at 800 mm/min and come back (tension test)
  homez            raise the router to its top switch
  status           show position and trims
  off              release the motors
  raw <gcode>      send a line straight to the controller
  quit
""")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port"); ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--host"); ap.add_argument("--tcp-port", type=int, default=23)
    a = ap.parse_args()
    if not a.port and not a.host:
        ap.error("give --port (USB) or --host (Wi-Fi)")
    Setup(Link(a.port, a.baud, a.host, a.tcp_port)).run()


if __name__ == "__main__":
    main()
