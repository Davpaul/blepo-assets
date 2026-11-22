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
MAX_OUTAGE = float(os.environ.get("KD_MAX_OUTAGE", 5 * 60))   # bed is cooling: don't wait forever
STEP_WAIT = float(os.environ.get("KD_STEP_WAIT", "8"))        # wait between USB recovery steps
EXTRA_BACKUP = 1.0         # seconds re-printed on top of Klipper's buffer, to avoid a gap
TOPO = os.path.join(STATE_DIR, "usb-topology.json")
USB_RESET = shlex.split(os.environ.get("KD_USB_RESET", "sudo -n /etc/klipper-deck/usb-reset"))
SYS_TTY = os.environ.get("KD_SYS_TTY", "/sys/class/tty")

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


def usb_topology(dev):
    """From /dev/ttyUSB0 work out the printer's USB device, the hub it hangs off
    (normally the dock) and the USB controller. Returns a dict or None."""
    try:
        p = os.path.realpath(os.path.join(SYS_TTY, os.path.basename(dev), "device"))
    except OSError:
        return None
    parts = p.split("/")
    usb = [x for x in parts if re.fullmatch(r"\d+-[\d.]+", x)]
    pci = [x for x in parts if re.fullmatch(r"[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]", x)]
    if not usb:
        return None
    printer = usb[-1]
    hub = usb[-2] if len(usb) > 1 else None
    return {"printer": printer, "hub": hub, "controller": pci[-1] if pci else None}


def remember_topology(dev):
    t = usb_topology(dev)
    if t:
        with open(TOPO, "w") as f:
            json.dump(t, f)
    return t


def load_topology():
    try:
        with open(TOPO) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def usb_reset(kind, target):
    """kind: 'hub' (like unplugging the dock) or 'controller' (all USB ports)."""
    if not target:
        return False
    say("Resetting USB %s %s (like unplugging and replugging it)..." % (kind, target))
    r = subprocess.run(USB_RESET + [kind, target], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        say("USB reset didn't work: %s" % (r.stdout.strip() or r.returncode))
        return False
    return True


def wait_for_printer(seconds):
    end = time.time() + seconds
    while time.time() < end:
        dev = find_printer()
        if dev:
            return dev
        time.sleep(1)
    return None


def bring_printer_back(deadline):
    """Wait for the printer's USB; if it doesn't come back, reset the dock/hub,
    then the whole USB controller. Returns the device path or None."""
    topo = load_topology() or {}
    steps = [("wait", None)]
    if topo.get("hub"):
        steps.append(("hub", topo["hub"]))
    if topo.get("controller"):
        steps.append(("controller", topo["controller"]))
    for kind, target in steps:
        if kind != "wait":
            usb_reset(kind, target)
        dev = wait_for_printer(min(STEP_WAIT if kind == "wait" else STEP_WAIT * 2,
                                   max(0, deadline - time.time())))
        if dev:
            return dev
    # Last resort: keep waiting until the deadline (someone may replug it)
    say("Still no printer. Unplug and replug the dock or printer USB if you're there.")
    return wait_for_printer(max(0, deadline - time.time()))


# ---------------------------------------------------------------- phone alerts (ntfy)

NOTIFY = os.path.join(CONF_DIR, "notify.json")


def notify_conf():
    try:
        with open(NOTIFY) as f:
            c = json.load(f)
        return c if c.get("topic") and c.get("enabled", True) else None
    except (OSError, ValueError):
        return None


def notify(title, message, priority=3, tags=None, buttons=("open",)):
    """Send a phone alert through ntfy. Buttons: open, pause, resume, cancel (max 3)."""
    c = notify_conf()
    if not c:
        return False
    base = c.get("url", "").rstrip("/")
    acts = []
    for b in buttons[:3]:
        if not base:
            break
        if b == "open":
            acts.append({"action": "view", "label": "Open Mainsail", "url": base, "clear": False})
        else:
            acts.append({"action": "http", "label": b.capitalize(), "method": "POST",
                         "url": "%s/printer/print/%s" % (base, b), "clear": True})
    body = {"topic": c["topic"], "title": title, "message": message,
            "priority": priority, "tags": list(tags or []), "actions": acts}
    if base:
        body["click"] = base
    try:
        req = urllib.request.Request(c.get("server", "https://ntfy.sh").rstrip("/"),
                                     data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=8).read()
        return True
    except Exception as e:
        say("Phone alert failed: %s" % e)
        return False


def tailscale_ip():
    for exe in ("tailscale", "/opt/tailscale/tailscale"):
        try:
            r = subprocess.run([exe, "ip", "-4"], capture_output=True, text=True, timeout=5)
            ip = r.stdout.strip().splitlines()[0] if r.returncode == 0 and r.stdout.strip() else ""
            if ip:
                return ip
        except (OSError, subprocess.SubprocessError, IndexError):
            pass
    return None


def lan_ip():
    try:
        r = subprocess.run(["ip", "-4", "route", "get", "1.1.1.1"], capture_output=True, text=True)
        m = re.search(r"src (\S+)", r.stdout)
        return m.group(1) if m else None
    except OSError:
        return None


def deck_url():
    ip = tailscale_ip() or lan_ip() or "steamdeck.local"
    return "http://%s%s" % (ip, "" if HTTP_PORT == "80" else ":" + HTTP_PORT)


def notify_cmd(args):
    import secrets
    sub = args[0] if args else "status"
    os.makedirs(CONF_DIR, exist_ok=True)
    c = {}
    try:
        with open(NOTIFY) as f:
            c = json.load(f)
    except (OSError, ValueError):
        pass
    if sub == "setup":
        c.setdefault("topic", "klipperdeck-" + secrets.token_hex(6))
        c.setdefault("server", "https://ntfy.sh")
        c["url"] = deck_url()
        c["enabled"] = True
        with open(NOTIFY, "w") as f:
            json.dump(c, f, indent=1)
        print("Phone alerts are set up.")
        print()
        print("  1. Install the 'ntfy' app on your phone (App Store / Play Store).")
        print("  2. In the app tap + and subscribe to this topic:")
        print()
        print("        %s" % c["topic"])
        print()
        print("  Buttons in alerts will open/control: %s" % c["url"])
        if not tailscale_ip():
            print("  (That's your home network address, so buttons only work at home.")
            print("   Run remote-access.sh to make them work from anywhere.)")
        print()
        print("Sending a test alert now...")
        notify("Klipper on the Deck", "Test alert. If you can see this, alerts work.",
               tags=["printer"], buttons=("open",))
    elif sub == "test":
        print("Sent." if notify("Klipper on the Deck", "Test alert.", tags=["printer"])
              else "Not set up yet: run  klipper-deck notify setup")
    elif sub == "off":
        c["enabled"] = False
        with open(NOTIFY, "w") as f:
            json.dump(c, f, indent=1)
        print("Phone alerts off. 'klipper-deck notify setup' turns them back on.")
    else:
        print("Phone alerts: %s" % ("ON, topic " + c["topic"] if notify_conf() else "off"))
        print("Use: klipper-deck notify setup | test | off")


def api(path, method="GET", timeout=5):
    req = urllib.request.Request(API + path, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def query_status():
    q = "print_stats&virtual_sdcard&gcode_move&extruder=target&heater_bed=target&fan&webhooks&display_status"
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
    add("RESPOND MSG=\"Auto-resume: reheating before anything moves\"")
    pre.extend(defines)
    if total_layer:
        add(total_layer)
    if rs.layer:
        add(rs.layer)
    # Nothing moves until the nozzle is fully hot: a cold nozzle is stuck in the
    # plastic and lifting it would rip the print.
    add("M140 S%.0f" % bed)
    add("M104 S%.0f" % min(hot, 140))           # warm while the bed heats, without oozing much
    add("SET_KINEMATIC_POSITION X=0 Y=0 Z=%.3f SET_HOMED=Z" % zphys)
    if bed:
        add("M190 S%.0f" % bed)
    add("M109 S%.0f" % hot)                      # fully melted before any movement
    add("M83")
    add("G1 E-1.5 F1800")                        # pull back the ooze straight away
    add("G91")
    add("G1 Z5 F600")                            # now lift clear of the print
    add("G90")
    add("G28 X Y")
    add("SET_GCODE_OFFSET X=%.3f Y=%.3f Z=%.3f" % (origin[0], origin[1], zoff))
    add("G90")
    add("G1 X%.3f Y%.3f F6000" % (rs.pos["X"], rs.pos["Y"]))
    add("G1 Z%.3f F600" % rs.pos["Z"])
    add("G1 E1.5 F1800")
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
    fname = snap.get("original") or snap.get("filename")
    if not auto_enabled():
        say("Auto-resume is off. Run 'klipper-deck resume' to resume by hand.")
        notify("Print stopped: USB dropout", "%s stopped. Auto-resume is off." % fname,
               priority=5, tags=["warning"])
        return
    if snap.get("attempts", 0) >= MAX_ATTEMPTS:
        say("Already auto-resumed %d times for this print; not trying again." % MAX_ATTEMPTS)
        notify("Print stopped: too many dropouts", "%s dropped %d times. Not resuming again; "
               "check the USB/dock." % (fname, MAX_ATTEMPTS + 1), priority=5, tags=["warning"])
        return
    say("Waiting for the printer's USB to come back (heaters are off, so speed matters)...")
    notify("USB dropout: recovering", "%s lost its USB link. Reconnecting and resuming "
           "automatically..." % fname, priority=4, tags=["rotating_light"], buttons=("open",))
    deadline = time.time() + MAX_OUTAGE
    time.sleep(2)
    ready = False
    for attempt in range(3):
        dev = bring_printer_back(deadline)
        if not dev:
            say("Printer didn't come back within %d minutes. Giving up; "
                "you can still try 'klipper-deck resume'." % (MAX_OUTAGE // 60))
            notify("Print lost: printer didn't come back", "%s: printer USB didn't return in %d min. "
                   "Needs you: replug the dock, then 'klipper-deck resume'."
                   % (fname, MAX_OUTAGE // 60), priority=5, tags=["sos"])
            return
        remember_topology(dev)
        say("Printer is back on %s. Restarting Klipper..." % dev)
        start_container(dev)
        if wait_ready(timeout=60):
            ready = True
            break
        # Printer is visible but Klipper can't talk to it: same as having to
        # unplug the dock by hand. Reset the hub and try again.
        say("Klipper couldn't connect. Resetting the dock's USB and trying again...")
        topo = load_topology() or {}
        usb_reset("hub", topo.get("hub")) or usb_reset("controller", topo.get("controller"))
        time.sleep(3)
        if time.time() > deadline:
            break
    if not ready:
        say("Klipper didn't get ready. Check Mainsail; you can try 'klipper-deck resume'.")
        notify("Print lost: Klipper won't reconnect", "%s: needs you. Check Mainsail, then "
               "'klipper-deck resume'." % fname, priority=5, tags=["sos"])
        return
    try:
        if do_resume(snap, failure_text, start=start):
            notify("Print resumed", "%s resumed after the USB dropout. Check it when you can: "
                   "there may be a small seam." % fname, priority=4, tags=["white_check_mark"],
                   buttons=("pause", "cancel", "open"))
        gcode('RESPOND TYPE=command MSG="Print auto-resumed after a USB dropout"')
    except Exception as e:
        say("Resume failed: %s" % e)
        notify("Print lost: resume failed", "%s: %s" % (fname, e), priority=5, tags=["sos"])


def print_alert(prev, state, fname, st, pending_error):
    """Phone alerts for print state changes. Returns a pending error (or None)."""
    name = re.sub(r"^(RESUME\d*-)+", "", fname)
    if state == "printing" and prev in ("standby", "complete", "cancelled", "error"):
        if not fname.startswith("RESUME"):
            notify("Print started", name, priority=2, tags=["printer"],
                   buttons=("pause", "cancel", "open"))
    elif state == "printing" and prev == "paused":
        notify("Print resumed", name, priority=2, tags=["arrow_forward"],
               buttons=("pause", "cancel", "open"))
    elif state == "paused":
        notify("Print paused", "%s is paused (filament runout or someone pressed pause)." % name,
               priority=4, tags=["pause_button"], buttons=("resume", "cancel", "open"))
    elif state == "complete":
        mins = int((st["print_stats"].get("print_duration") or 0) // 60)
        notify("Print finished", "%s done in %dh %02dm." % (name, mins // 60, mins % 60),
               priority=3, tags=["tada"])
    elif state == "cancelled":
        notify("Print cancelled", name, priority=3, tags=["stop_button"])
    elif state == "error" and prev == "printing":
        msg = st["print_stats"].get("message") or st["webhooks"].get("state_message") or "error"
        return (time.time(), name, msg.strip().splitlines()[0][:200])
    return pending_error


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
    topo = remember_topology(dev)
    if topo:
        say("USB: printer %s on hub %s, controller %s" % (topo["printer"], topo["hub"], topo["controller"]))
    start_container(dev)
    say("Auto-resume after USB dropouts is %s." % ("ON" if auto_enabled() else "OFF"))
    say("Phone alerts are %s." % ("ON" if notify_conf() else "off (klipper-deck notify setup)"))
    log_pos = log_size()
    was_printing = False
    prev_state = None
    pending_error = None      # (when, filename, message): held briefly in case it's a USB dropout
    try:
        while not stop["flag"]:
            time.sleep(POLL)
            try:
                st = query_status()
                state = st["print_stats"].get("state")
                fname = st["print_stats"].get("filename") or ""
                if prev_state is not None and state != prev_state:
                    pending_error = print_alert(prev_state, state, fname, st, pending_error)
                prev_state = state
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
                    pending_error = None          # the recovery sends its own alerts
                    recover(snap, window, start=log_pos - win_start)
                size = log_size()
                was_printing = False
                prev_state = None
            if pending_error and time.time() - pending_error[0] > 3 * POLL + 2:
                notify("Print failed", "%s: %s" % (pending_error[1], pending_error[2]),
                       priority=5, tags=["x"])
                pending_error = None
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
    elif cmd == "notify":
        notify_cmd(sys.argv[2:])
    elif cmd == "usbreset":
        topo = load_topology()
        if not topo:
            print("Don't know the printer's USB layout yet. Start Klipper once with the printer plugged in.")
            sys.exit(1)
        ok = usb_reset("hub", topo.get("hub"))
        dev = wait_for_printer(STEP_WAIT * 2)
        if not dev and topo.get("controller"):
            usb_reset("controller", topo["controller"])
            dev = wait_for_printer(STEP_WAIT * 2)
        print("Printer is back on %s. In Mainsail press FIRMWARE RESTART." % dev if dev
              else "Printer still not showing up. Check the cable and that it's switched on.")
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
