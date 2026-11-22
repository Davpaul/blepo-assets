#!/usr/bin/env python3
"""
guard.py - runs the Klipper container and auto-resumes prints after a USB dropout.

Used by `klipper-deck start`. What it does:
  * starts the container with the printer's current USB port
  * while printing, saves a snapshot of the job every 2 seconds
  * watches klippy.log for a lost USB link ("No such device", "Got EOF", ...)
  * if that happens mid-print: waits for the printer to come back, restarts the
    container on the new USB port, works out the exact point the printer had
    reached, builds a "resume" G-code file and starts it

It only resumes after a lost USB connection. A thermal error, an emergency stop
or a cancel never triggers a resume.

Also usable by hand:
  guard.py resume      build + start a resume from the last saved print (asks first)
  guard.py make-resume GCODE SD_POS BUFFER_TIME OUT   (testing: just build the file)
"""

import json
import math
import os
import re
import shlex
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HOME = os.path.expanduser("~")
NAME = os.environ.get("KD_NAME", "klipper-deck")
IMAGE = os.environ.get("KD_IMAGE", "localhost/klipper-deck")
DATA = os.environ.get("KD_DATA", os.path.join(HOME, "klipper-deck", "printer_data"))
STATE_DIR = os.environ.get("KD_STATE", os.path.join(HOME, "klipper-deck"))
CONF_DIR = os.environ.get("KD_CONF", os.path.join(HOME, ".config", "klipper-deck"))
HTTP_PORT = os.environ.get("KD_HTTP_PORT", "80")
API = os.environ.get("KD_API", "http://127.0.0.1:7125")
PODMAN = shlex.split(os.environ.get("KD_PODMAN", "podman"))
DEV_GLOBS = os.environ.get(
    "KD_DEV_GLOBS", "/dev/serial/by-id/*1a86*:/dev/serial/by-id/*:/dev/ttyUSB*:/dev/ttyACM*").split(":")

LOG = os.path.join(DATA, "logs", "klippy.log")
GCODES = os.path.join(DATA, "gcodes")
SNAP = os.path.join(STATE_DIR, "resume-state.json")

POLL = float(os.environ.get("KD_POLL", "2"))
MAX_ATTEMPTS = 3           # auto-resumes per print
MAX_OUTAGE = 15 * 60       # give up if the printer is gone longer than this
EXTRA_BACKUP = 1.0         # seconds re-printed on top of Klipper's buffer, to avoid a gap

COMMS_LOSS = re.compile(
    r"Got EOF when reading from device|in write: \(19\)|No such device|"
    r"Timeout with MCU|Lost communication with MCU")


def say(msg):
    print(time.strftime("%H:%M:%S ") + msg, flush=True)


# ---------------------------------------------------------------- helpers

def auto_enabled():
    try:
        with open(os.path.join(CONF_DIR, "auto-resume")) as f:
            return f.read().strip() != "off"
    except OSError:
        return True


def find_printer():
    import glob
    for pattern in DEV_GLOBS:
        for d in sorted(glob.glob(pattern)):
            if os.path.exists(d):
                return os.path.realpath(d)
    return None


def api(path, method="GET", timeout=5):
    req = urllib.request.Request(API + path, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def query_status():
    q = "print_stats&virtual_sdcard&gcode_move&extruder=target&heater_bed=target&fan&webhooks"
    return api("/printer/objects/query?" + q)["result"]["status"]


def gcode(script):
    try:
        api("/printer/gcode/script?script=" + urllib.parse.quote(script), "POST", timeout=10)
    except Exception:
        pass


def podman(*args, check=False):
    return subprocess.run(PODMAN + list(args), stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, check=check)


def start_container(dev):
    podman("rm", "-f", NAME)
    args = ["run", "-d", "--rm", "--name", NAME, "--network", "host",
            "-e", "HTTP_PORT=" + HTTP_PORT, "-v", DATA + ":/root/printer_data"]
    if dev:
        args += ["--device", dev + ":/dev/printer"]
    podman(*args, IMAGE, "run", check=True)


def wait_ready(timeout=120):
    """Wait for Moonraker + Klipper to be ready. Firmware-restarts once if needed."""
    end = time.time() + timeout
    restarted = False
    while time.time() < end:
        try:
            st = query_status()["webhooks"]["state"]
            if st == "ready":
                return True
            if st in ("shutdown", "error") and not restarted:
                api("/printer/firmware_restart", "POST")
                restarted = True
        except Exception:
            pass
        time.sleep(2)
    return False


def save_snapshot(st):
    snap = {
        "time": time.time(),
        "filename": st["print_stats"].get("filename"),
        "file_position": st["virtual_sdcard"].get("file_position", 0),
        "extruder_target": st["extruder"].get("target", 0),
        "bed_target": st["heater_bed"].get("target", 0),
        "fan": st.get("fan", {}).get("speed", 0),
        "homing_origin": st["gcode_move"].get("homing_origin", [0, 0, 0, 0]),
        "speed_factor": st["gcode_move"].get("speed_factor", 1),
        "extrude_factor": st["gcode_move"].get("extrude_factor", 1),
        "attempts": 0,
    }
    old = load_snapshot()
    if old and old.get("filename") == snap["filename"]:
        snap["attempts"] = old.get("attempts", 0)
        snap["original"] = old.get("original", snap["filename"])
    else:
        snap["original"] = snap["filename"]
    tmp = SNAP + ".tmp"
    with open(tmp, "w") as f:
        json.dump(snap, f)
    os.replace(tmp, SNAP)


def load_snapshot():
    try:
        with open(SNAP) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def last_position_from_log(text, start=0):
    """Find the last Stats line (sd_pos + buffer_time) before the USB link died.

    Uses the first comms error at or after `start`. Later Stats lines can't be
    trusted: Klipper keeps reading the file for a while after the link is gone.
    """
    m = COMMS_LOSS.search(text, start)
    before = text[:m.start()] if m else text
    sd = re.findall(r"sd_pos=(\d+)", before)
    bt = re.findall(r"buffer_time=([\d.]+)", before)
    if not sd:
        return None, None
    return int(sd[-1]), float(bt[-1]) if bt else 1.0


# ---------------------------------------------------------------- resume file builder

AXES = "XYZE"


class GState:
    def __init__(self):
        self.pos = {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0}
        self.f = 3000.0
        self.abs_coord = True
        self.abs_e = True
        self.fan = None
        self.hot = 0.0
        self.bed = 0.0
        self.m220 = None
        self.m221 = None
        self.accel = None        # last M204 / SET_VELOCITY_LIMIT line
        self.pa = None           # last SET_PRESSURE_ADVANCE line
        self.layer = None        # last SET_PRINT_STATS_INFO CURRENT_LAYER line
        self.obj = None          # EXCLUDE_OBJECT_START NAME currently open

    def copy(self):
        c = GState.__new__(GState)
        c.__dict__ = dict(self.__dict__)
        c.pos = dict(self.pos)
        return c


def params(parts):
    out = {}
    for p in parts[1:]:
        if len(p) > 1 and p[0].upper() in "XYZEFSP":
            try:
                out[p[0].upper()] = float(p[1:])
            except ValueError:
                pass
    return out


def apply_line(st, raw):
    """Update state with one G-code line. Returns move duration in seconds (0 if none)."""
    line = raw.split(";", 1)[0].strip()
    if not line:
        return 0.0
    parts = line.split()
    cmd = parts[0].upper()
    if cmd in ("G0", "G1", "G2", "G3"):
        p = params(parts)
        if "F" in p and p["F"] > 0:
            st.f = p["F"]
        old = dict(st.pos)
        for a in AXES:
            if a in p:
                rel = (not st.abs_coord) or (a == "E" and not st.abs_e)
                st.pos[a] = st.pos[a] + p[a] if rel else p[a]
        d = math.sqrt(sum((st.pos[a] - old[a]) ** 2 for a in "XYZ"))
        if d == 0:
            d = abs(st.pos["E"] - old["E"])
        return d / (st.f / 60.0) if st.f > 0 else 0.0
    if cmd == "G90":
        st.abs_coord = True
    elif cmd == "G91":
        st.abs_coord = False
    elif cmd == "M82":
        st.abs_e = True
    elif cmd == "M83":
        st.abs_e = False
    elif cmd == "G92":
        p = params(parts)
        if not any(a in p for a in AXES):
            p = {a: 0.0 for a in AXES}
        for a in AXES:
            if a in p:
                st.pos[a] = p[a]
    elif cmd == "G28":
        p = [x.upper() for x in parts[1:]]
        for a in "XYZ":
            if not p or any(x.startswith(a) for x in p):
                st.pos[a] = 0.0
    elif cmd in ("M104", "M109"):
        s = params(parts).get("S")
        if s is not None:
            st.hot = s
    elif cmd in ("M140", "M190"):
        s = params(parts).get("S")
        if s is not None:
            st.bed = s
    elif cmd == "M106":
        st.fan = params(parts).get("S", 255.0)
    elif cmd == "M107":
        st.fan = 0.0
    elif cmd == "M220":
        st.m220 = line
    elif cmd == "M221":
        st.m221 = line
    elif cmd == "M204" or cmd == "SET_VELOCITY_LIMIT":
        st.accel = line
    elif cmd == "SET_PRESSURE_ADVANCE":
        st.pa = line
    elif cmd == "SET_PRINT_STATS_INFO" and "CURRENT_LAYER" in line.upper():
        st.layer = line
    elif cmd == "EXCLUDE_OBJECT_START":
        st.obj = line
    elif cmd == "EXCLUDE_OBJECT_END":
        st.obj = None
    return 0.0


def build_resume(gcode_path, sd_pos, back_seconds, snap=None):
    """Return (resume_bytes, resume_offset, state) for restarting gcode_path at sd_pos."""
    with open(gcode_path, "rb") as f:
        data = f.read()
    sd_pos = min(sd_pos, len(data))
    st = GState()
    header, defines, total_layer = [], [], None
    in_header = True
    history = []                  # (offset, duration, state-before-line) for recent lines
    off = 0
    while off < sd_pos:
        nl = data.find(b"\n", off)
        end = len(data) if nl < 0 else nl + 1
        raw = data[off:end].decode("utf-8", "replace")
        s = raw.strip()
        if in_header:
            if s.startswith(";") or not s:
                header.append(raw.rstrip("\r\n"))
            else:
                in_header = False
        u = s.upper()
        if u.startswith("EXCLUDE_OBJECT_DEFINE"):
            defines.append(s)
        elif u.startswith("SET_PRINT_STATS_INFO") and "TOTAL_LAYER" in u:
            total_layer = s
        before = st.copy()
        dur = apply_line(st, raw)
        history.append((off, dur, before))
        if len(history) > 4000:
            del history[:1000]
        off = end
    # Walk back over the moves that were buffered but never made it to the motors
    resume_off, resume_state, t = sd_pos, st, 0.0
    for o, dur, before in reversed(history):
        if t >= back_seconds:
            break
        t += dur
        resume_off, resume_state = o, before
    rs = resume_state
    snap = snap or {}
    hot = snap.get("extruder_target") or rs.hot or 200
    bed = snap.get("bed_target") or rs.bed or 0
    origin = snap.get("homing_origin") or [0, 0, 0, 0]
    zoff = origin[2] if len(origin) > 2 else 0.0
    zphys = rs.pos["Z"] + zoff

    pre = []
    add = pre.append
    add("; ---- AUTO-RESUME (klipper-deck) ----")
    add("; original: %s  resumed at byte %d (last read %d, backed up %.2fs)"
        % (os.path.basename(gcode_path), resume_off, sd_pos, t))
    add("RESPOND MSG=\"Auto-resume: reheating and re-homing X/Y\"")
    pre.extend(defines)
    if total_layer:
        add(total_layer)
    if rs.layer:
        add(rs.layer)
    add("M140 S%.0f" % bed)
    add("M104 S%.0f" % min(hot, 170))           # warm, but below oozing temperature
    add("SET_KINEMATIC_POSITION X=0 Y=0 Z=%.3f SET_HOMED=Z" % zphys)
    add("G91")
    add("G1 Z5 F600")                            # lift off the print before anything moves
    add("G90")
    add("G28 X Y")
    add("SET_GCODE_OFFSET X=%.3f Y=%.3f Z=%.3f" % (origin[0], origin[1], zoff))
    if bed:
        add("M190 S%.0f" % bed)
    add("M109 S%.0f" % hot)
    add("M83")
    add("G1 E-1.0 F1800")                        # pull back the ooze from heating
    add("G90")
    add("G1 X%.3f Y%.3f F6000" % (rs.pos["X"], rs.pos["Y"]))
    add("G1 Z%.3f F600" % rs.pos["Z"])
    add("G1 E1.0 F1800")
    if rs.fan is not None:
        add("M106 S%.0f" % rs.fan)
    elif snap.get("fan"):
        add("M106 S%.0f" % (snap["fan"] * 255))
    for extra in (rs.m220, rs.m221, rs.accel, rs.pa):
        if extra:
            add(extra)
    if snap.get("speed_factor") and not rs.m220:
        add("M220 S%.0f" % (snap["speed_factor"] * 100))
    if snap.get("extrude_factor") and not rs.m221:
        add("M221 S%.0f" % (snap["extrude_factor"] * 100))
    add("G90" if rs.abs_coord else "G91")
    add("M82" if rs.abs_e else "M83")
    if rs.abs_e and rs.abs_coord:
        add("G92 E%.5f" % rs.pos["E"])
    add("G1 F%.0f" % rs.f)
    if rs.obj:
        add(rs.obj)
    add("RESPOND MSG=\"Auto-resume: continuing print\"")
    add("; ---- original file continues ----")
    body = "\n".join(header + pre) + "\n"
    return body.encode() + data[resume_off:], resume_off, rs


# ---------------------------------------------------------------- recovery

def do_resume(snap, log_text, ask=False, start=0):
    fname = snap.get("filename")
    src = os.path.join(GCODES, fname) if fname else None
    if not src or not os.path.exists(src):
        say("Can't find the G-code file %r, so can't resume." % fname)
        return False
    sd_pos, buf = last_position_from_log(log_text, start)
    if sd_pos is None:
        sd_pos, buf = snap.get("file_position", 0), 2.0
        say("No position in the log; using the last snapshot (less exact).")
    data, off, rs = build_resume(src, sd_pos, buf + EXTRA_BACKUP, snap)
    base = os.path.basename(snap.get("original") or fname)
    base = re.sub(r"^(RESUME\d*-)+", "", base)
    out_name = "RESUME%d-%s" % (snap.get("attempts", 0) + 1, base)
    out = os.path.join(GCODES, out_name)
    with open(out, "wb") as f:
        f.write(data)
    say("Resume file written: %s (from byte %d, Z=%.2f)" % (out_name, off, rs.pos["Z"]))
    if ask:
        a = input("Check the print head hasn't dropped onto the print. Start the resume? [y/N] ")
        if not a.lower().startswith("y"):
            say("Not started. The file is in your print list if you want it later.")
            return False
    snap["attempts"] = snap.get("attempts", 0) + 1
    snap["filename"] = out_name
    with open(SNAP, "w") as f:
        json.dump(snap, f)
    api("/printer/print/start?filename=" + urllib.parse.quote(out_name), "POST", timeout=15)
    say("Resume started.")
    return True


def read_log_from(offset):
    try:
        with open(LOG, "r", errors="replace") as f:
            f.seek(offset)
            return f.read()
    except OSError:
        return ""


def log_size():
    try:
        return os.path.getsize(LOG)
    except OSError:
        return 0


def recover(snap, failure_text, start):
    say("USB link to the printer was lost mid-print.")
    if not auto_enabled():
        say("Auto-resume is off. Run 'klipper-deck resume' to resume by hand.")
        return
    if snap.get("attempts", 0) >= MAX_ATTEMPTS:
        say("Already auto-resumed %d times for this print; not trying again." % MAX_ATTEMPTS)
        return
    say("Waiting for the printer's USB to come back...")
    t0 = time.time()
    dev = None
    time.sleep(3)
    while time.time() - t0 < MAX_OUTAGE:
        dev = find_printer()
        if dev:
            break
        time.sleep(2)
    if not dev:
        say("Printer didn't come back within %d minutes. Giving up." % (MAX_OUTAGE // 60))
        return
    say("Printer is back on %s. Restarting Klipper..." % dev)
    start_container(dev)
    if not wait_ready():
        say("Klipper didn't get ready. Check Mainsail; you can try 'klipper-deck resume'.")
        return
    try:
        do_resume(snap, failure_text, start=start)
        gcode('RESPOND TYPE=command MSG="Print auto-resumed after a USB dropout"')
    except Exception as e:
        say("Resume failed: %s" % e)


def run():
    stop = {"flag": False}

    def handler(signum, frame):
        stop["flag"] = True
    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(s, handler)

    os.makedirs(STATE_DIR, exist_ok=True)
    dev = find_printer()
    if not dev:
        say("No printer found yet. Plug it in by USB and switch it on; waiting...")
        while not dev and not stop["flag"]:
            time.sleep(2)
            dev = find_printer()
    if stop["flag"]:
        return
    say("Printer found on %s. Starting Klipper..." % dev)
    start_container(dev)
    say("Auto-resume after USB dropouts is %s." % ("ON" if auto_enabled() else "OFF"))
    log_pos = log_size()
    was_printing = False
    try:
        while not stop["flag"]:
            time.sleep(POLL)
            try:
                st = query_status()
                state = st["print_stats"].get("state")
                if state == "printing":
                    save_snapshot(st)
                # A USB dropout turns the state into "error": keep the last real
                # state so we know a print was running. Cancel / complete clear it.
                if state != "error":
                    was_printing = state == "printing"
            except Exception:
                pass  # Moonraker briefly unreachable is normal during restarts
            size = log_size()
            if size < log_pos:
                log_pos = 0          # log was rotated
            new = read_log_from(log_pos)
            if new and COMMS_LOSS.search(new) and was_printing:
                # include what came just before, for the last sd_pos
                win_start = max(0, log_pos - 300000)
                window = read_log_from(win_start)
                snap = load_snapshot()
                if snap:
                    recover(snap, window, start=log_pos - win_start)
                size = log_size()
                was_printing = False
            log_pos = size
    finally:
        say("Stopping Klipper...")
        podman("stop", "-t", "10", NAME)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        run()
    elif cmd == "resume":
        snap = load_snapshot()
        if not snap:
            print("No saved print to resume.")
            sys.exit(1)
        print("Last print: %s (saved %s)" % (snap.get("filename"),
              time.strftime("%Y-%m-%d %H:%M", time.localtime(snap.get("time", 0)))))
        if not wait_ready(timeout=30):
            print("Klipper isn't ready. Start it first with: klipper-deck start")
            sys.exit(1)
        text = read_log_from(0)
        i = text.rfind("Starting SD card print")
        do_resume(snap, text[i:] if i >= 0 else text, ask=True)
    elif cmd == "make-resume":
        g, sd, bt, out = sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
        data, off, rs = build_resume(g, sd, bt + EXTRA_BACKUP)
        with open(out, "wb") as f:
            f.write(data)
        print(json.dumps({"offset": off, "X": rs.pos["X"], "Y": rs.pos["Y"],
                          "Z": rs.pos["Z"], "E": rs.pos["E"], "abs_e": rs.abs_e}))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
