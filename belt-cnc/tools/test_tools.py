"""Self-test for the Belt CNC tools. No machine needed.

    python3 test_tools.py

It checks the belt maths, the table and calibration tools, the file upload, and
the setup script (against a pretend controller that runs on this computer).
"""
import io, math, os, re, shutil, socket, subprocess, sys, tempfile, threading, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import beltkin as K
import calibrate as C
import upload_config as U
import belt_setup as B
from make_test_pattern import points

CONFIG = os.path.join(HERE, "..", "firmware", "belt-cnc.yaml")
if not os.path.exists(CONFIG):
    CONFIG = os.path.join(HERE, "..", "belt-cnc.yaml")          # layout of the packaged download
results = []


def check(ok, what):
    results.append(ok)
    print(("PASS  " if ok else "FAIL  ") + what)


# ----------------------------------------------------------------------------- belt maths
def test_maths():
    rng = np.random.default_rng(3)
    for t in (K.Table.rectangle(2440, 1220), K.Table.from_measurements(1260.0, 668.5, 1263.2, 671.0, 1424.0)):
        worst = 0.0
        xs, ys = t.C[:, 0], t.C[:, 1]
        for _ in range(60):
            p = np.array([rng.uniform(xs.min() + 60, xs.max() - 60), rng.uniform(ys.min() + 60, ys.max() - 60)])
            worst = max(worst, np.abs(K.forward(t, K.lengths(t, p), guess=p + 30) - p).max())
        check(worst < 1e-4, f"position recovered from belt lengths (worst error {worst:.1e} mm)")
    t = K.Table.rectangle(2440, 1220)
    L = K.lengths(t, t.centre)
    direct = 2 * np.linalg.norm(t.P[0] - (t.centre + K.IDLER_B[0]))
    check(abs(L[0] - direct) < 60, f"belt length is about twice the corner-to-sled distance ({L[0]:.0f} vs {direct:.0f} mm)")
    check(abs(L[0] - L[2]) < 1e-6 and abs(L[1] - L[3]) < 1e-6, "opposite corners match on a square table")


# ----------------------------------------------------------------------------- table tool
def test_table():
    t = K.Table.rectangle(2440, 1220)
    m = t.post_distances()
    back = K.Table.from_measurements(*m)
    check(np.abs(back.C - t.C).max() < 1e-4, "five measurements give back the right table")
    tmp = tempfile.mkdtemp()
    cfg = os.path.join(tmp, "belt-cnc.yaml")
    shutil.copy(CONFIG, cfg)
    skew = (1260.0, 668.5, 1263.2, 671.0, 1424.0)
    out = subprocess.run([sys.executable, os.path.join(HERE, "table_config.py"), *map(str, skew), "--write", cfg], capture_output=True, text=True)
    check(out.returncode == 0 and "updated" in out.stdout, "table_config.py writes a config file")
    want, got = K.Table.from_measurements(*skew), K.Table.from_config(cfg)
    check(np.abs(got.P - want.P).max() < 2e-3 and np.abs(got.F - want.F).max() < 2e-3, "the written config reads back as the same table")
    text = open(cfg).read()
    hx = float(re.search(r"mpos_mm:\s*([-\d.]+)\s*# =home_x", text).group(1))
    check(abs(hx - want.centre[0]) < 2e-3, "home position in the config matches the table centre")
    bad = subprocess.run([sys.executable, os.path.join(HERE, "table_config.py"), "1000", "500", "1000", "500", "3000"], capture_output=True, text=True)
    check(bad.returncode != 0, "impossible measurements are rejected")
    return cfg


# ----------------------------------------------------------------------------- calibration
def test_calibrate():
    posts = [2500.4, 1280.8, 2500.4, 1280.8, 2789.6]
    pts = points(2440, 1220, 300)
    dots = C.predicted(K.Table.from_measurements(*posts), np.array(posts), 1.0015, pts)
    out = subprocess.run([sys.executable, os.path.join(HERE, "calibrate.py"), "--posts", *map(str, posts), "--dots", *[f"{d:.2f}" for d in dots]],
                         capture_output=True, text=True)
    m = re.search(r"moving ([-+\d.]+) parts per thousand", out.stdout)
    check(bool(m) and abs(float(m.group(1)) - 1.5) < 0.15, f"calibration finds a 1.5 per thousand belt scale error (found {m.group(1) if m else '?'})")
    g = subprocess.run([sys.executable, os.path.join(HERE, "make_test_pattern.py")], capture_output=True, text=True).stdout
    check(g.count("G53 G0 X") == 6 and g.strip().endswith("M2"), "test pattern G-code has five dots and returns to centre")


# ----------------------------------------------------------------------------- file upload
class Pipe:
    """One end of an in-memory two-way link, with the read/write calls pyserial has."""
    def __init__(self):
        self.inbox, self.other, self.lock = bytearray(), None, threading.Lock()

    def write(self, data):
        with self.other.lock:
            self.other.inbox += data

    def read(self, n=1):
        end = time.time() + 0.05
        while time.time() < end:
            with self.lock:
                if self.inbox:
                    out = bytes(self.inbox[:n]); del self.inbox[:n]
                    return out
            time.sleep(0.001)
        return b""


def fake_xmodem_receiver(link, store, corrupt_first=True):
    """Stands in for the controller's side of the file transfer."""
    buf = b""
    while b"\n$Xmodem/Receive=" not in buf or not buf.endswith(b"\n"):
        buf += link.read(64)
    store["name"] = buf.split(b"=")[-1].strip().decode()
    link.write(b"C")
    data, expect, nak_once = b"", 1, corrupt_first
    while True:
        b = link.read(1)
        if not b:
            continue
        if b[0] == U.EOT:
            link.write(bytes([U.ACK])); break
        if b[0] != U.SOH:
            continue
        pkt = b""
        while len(pkt) < 132:
            pkt += link.read(132 - len(pkt))
        ok = pkt[0] == expect & 0xFF and pkt[1] == 0xFF - pkt[0] and U.crc16(pkt[2:130]) == int.from_bytes(pkt[130:132], "big")
        if ok and nak_once:
            nak_once = False; link.write(bytes([U.NAK])); continue      # make the sender retry once
        if ok:
            data += pkt[2:130]; expect += 1; link.write(bytes([U.ACK]))
        else:
            link.write(bytes([U.NAK]))
    store["data"] = data.rstrip(bytes([U.PAD]))
    tail = b""
    end = time.time() + 2
    while time.time() < end and b"$Config/Filename=" not in tail:
        tail += link.read(64)
    store["tail"] = tail


def test_upload():
    a, b = Pipe(), Pipe(); a.other, b.other = b, a
    store = {}
    th = threading.Thread(target=fake_xmodem_receiver, args=(b, store)); th.start()
    n = U.upload(a, CONFIG, log=lambda *_: None)
    th.join(10)
    original = open(CONFIG, "rb").read()
    check(store.get("data") == original and n == len(original), f"settings file transfers intact, including a resend ({n} bytes)")
    check(store.get("name") == "belt-cnc.yaml" and b"$Config/Filename=belt-cnc.yaml" in store.get("tail", b""), "upload names the file and makes it the active config")
    check(U.crc16(b"123456789") == 0x31C3, "checksum matches the XMODEM standard")


# ----------------------------------------------------------------------------- setup script
class FakeController(threading.Thread):
    """Pretends to be the controller on a local network port, using the same belt maths."""
    def __init__(self, table):
        super().__init__(daemon=True)
        self.t, self.pos, self.trim = table, [table.centre[0], table.centre[1], 0.0], dict.fromkeys(B.CORNERS, 0.0)
        self.zero = K.lengths(table, table.centre)
        self.motors = np.zeros(4)                # belt paid out beyond the centre position
        self.log, self.reels = [], False
        self.srv = socket.socket(); self.srv.bind(("127.0.0.1", 0)); self.srv.listen(1)
        self.port = self.srv.getsockname()[1]

    def targets(self):
        return K.lengths(self.t, self.pos[:2]) - self.zero + np.array([self.trim[c] for c in B.CORNERS])

    def run(self):
        conn, _ = self.srv.accept()
        buf = b""
        while True:
            try:
                data = conn.recv(4096)
            except OSError:
                break
            if not data:
                break
            buf += data
            while b"?" in buf.split(b"\n")[0] if buf else False:
                buf = buf.replace(b"?", b"", 1)
                conn.sendall(f"<Idle|MPos:{self.pos[0]:.3f},{self.pos[1]:.3f},{self.pos[2]:.3f},0.000,0.000|FS:0,0>\r\n".encode())
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.decode().strip()
                if not line:
                    continue
                self.log.append(line)
                m = re.match(r"\$/kinematics/BeltCNC/(\w\w)_trim=([-\d.]+)", line)
                if m:
                    self.trim[m.group(1)] = float(m.group(2))
                elif line == "M8":
                    self.reels = True
                elif line == "M9":
                    self.reels = False
                elif line in ("$HX", "$HY"):
                    self.pos[0 if line == "$HX" else 1] = self.t.centre[0 if line == "$HX" else 1]
                    self.motors = self.targets()
                elif "G1" in line:
                    for ax, val in re.findall(r"([XYZ])([-\d.]+)", line):
                        self.pos["XYZ".index(ax)] = float(val)
                    self.motors = self.targets()         # a move is what applies a changed trim
                conn.sendall(b"ok\r\n")


def test_setup(cfg):
    table = K.Table.from_config(cfg)
    fake = FakeController(table); fake.start()
    real_stdout, sys.stdout = sys.stdout, io.StringIO()
    real_input = getattr(__builtins__, "input", None)
    try:
        import builtins
        builtins.input = lambda *a: ""
        s = B.Setup(B.Link(host="127.0.0.1", tcp_port=fake.port), cfg)
        s.cmd_take("sw", 4.0); s.cmd_take("all", 0.5)
        after_snug = fake.motors.copy()
        s.cmd_square(200, 1500)
        after_square = list(fake.pos)
        s.cmd_pack()
        packed = fake.motors.copy()
        s.cmd_stowed(); s.cmd_unpack()
        unpacked = fake.motors.copy()
    finally:
        builtins.input = real_input or builtins.input
        sys.stdout = real_stdout
    check(fake.reels, "setup script switches the reel motors on")
    check(np.allclose(after_snug, [-4.5, -0.5, -0.5, -0.5], atol=1e-6), f"snugging takes in the right belt at each corner {np.round(after_snug, 2)}")
    check(abs(after_square[0] - table.centre[0]) < 1e-3 and abs(after_square[1] - table.centre[1]) < 1e-3, "test square returns to the centre")
    left_out = fake.zero + packed
    check(np.allclose(left_out, 150.0, atol=1e-3), f"pack winds each belt in to 150 mm left out {np.round(left_out, 1)}")
    check(np.allclose(unpacked, 0.0, atol=1e-6), "stowed then unpack pays the belts back out to the centre lengths")
    check("$HX" in fake.log and "$HY" in fake.log, "stowed tells the controller without moving")


# ----------------------------------------------------------------------------- reach
def test_reach():
    t = K.Table.rectangle(2440, 1220)
    mid = K.worst_tension(t, (1220, 610), 15, 3)
    edge = K.worst_tension(t, (1220, 60), 15, 3)
    check(mid is not None and mid < 20, f"centre of a full sheet needs little belt tension ({mid:.0f} N)")
    check(edge is None or edge > 35, "middle of the long edge is beyond the motors, as the reach map says")


if __name__ == "__main__":
    test_maths()
    cfg = test_table()
    test_calibrate()
    test_upload()
    test_setup(cfg)
    test_reach()
    print()
    if all(results):
        print(f"all {len(results)} checks passed")
    else:
        print(f"{results.count(False)} of {len(results)} checks FAILED"); sys.exit(1)
