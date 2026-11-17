"""Run the firmware in FluidNC's PC simulator and check it moves where it should.

    python3 sim_test.py path/to/simulator/program ../firmware/belt-cnc.yaml

The simulator is FluidNC built for a PC (PlatformIO environment "linux"), with
the BeltCNC module compiled in. This feeds it G-code, reads back the positions
it reports, and checks them. It is run automatically by the GitHub workflow.
"""
import math, os, re, subprocess, sys, tempfile

AXES = """
  {name}:
    steps_per_mm: {spm}
    max_rate_mm_per_min: {rate}
    acceleration_mm_per_sec2: {acc}
    max_travel_mm: {travel}
    soft_limits: false
{homing}    motor0:
      standard_stepper:
        step_pin: gpio.{step}
        direction_pin: gpio.{dirn}
"""


def sim_config(real_yaml):
    """The real config with the board-specific parts swapped for simulator ones."""
    text = open(real_yaml).read()
    kin = re.search(r"^kinematics:\n(?:[ \t]+.*\n|\n)+", text, re.M).group(0)
    hx = float(re.search(r"mpos_mm:\s*([-\d.]+)\s*# =home_x", text).group(1))
    hy = float(re.search(r"mpos_mm:\s*([-\d.]+)\s*# =home_y", text).group(1))
    out = 'name: "Belt CNC (simulator)"\nboard: "None"\n\n' + kin + "\nstepping:\n  engine: Timed\n  idle_ms: 255\n  pulse_us: 4\n  dir_delay_us: 1\n  disable_delay_us: 0\n\naxes:"
    pins = {"x": (12, 13), "y": (14, 15), "z": (16, 17), "a": (4, 5), "b": (6, 7)}
    for name in "xyzab":
        homing = ""
        if name == "z":      # FluidNC only accepts $HX/$HY when some axis has a real homing cycle
            homing = "    homing:\n      cycle: 1\n      positive_direction: true\n      mpos_mm: 0\n"
        if name in "xy":
            homing = f"    homing:\n      cycle: -1\n      mpos_mm: {hx if name == 'x' else hy}\n"
        belt = name != "z"
        out += AXES.format(name=name, spm=80 if belt else 400, rate=6000 if belt else 600, acc=300 if belt else 80,
                           travel=6000 if belt else 38, homing=homing, step=pins[name][0], dirn=pins[name][1])
    out += "\nstart:\n  must_home: false\n"
    return out, (hx, hy)


def run(program, config_text, commands, timeout=75):
    """Start the simulator with a list of commands and collect what it prints.
    It is given a pretend terminal, and stopped after `timeout` seconds if it has not finished."""
    import pty, signal, time
    work = tempfile.mkdtemp(prefix="beltsim_")
    os.makedirs(os.path.join(work, "native_localfs")); os.makedirs(os.path.join(work, "native_sd"))
    open(os.path.join(work, "native_localfs", "config.yaml"), "w").write(config_text)
    args = [os.path.abspath(program)]
    if os.geteuid() != 0 and subprocess.run(["sudo", "-n", "true"], capture_output=True).returncode == 0:
        args = ["sudo", "-n"] + args          # the simulator opens network ports 80 and 23, which needs root
    # the simulator quits as soon as it has read its last command, so finish with
    # harmless padding: everything that matters has completed by the time it is read
    for c in list(commands) + ["G4 P0.3", "$I"]:
        args += ["-c", c]
    log = os.path.join(work, "output.txt")
    master, slave = pty.openpty()
    with open(log, "wb") as fh:
        p = subprocess.Popen(args, cwd=work, stdin=slave, stdout=fh, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            subprocess.run(["sudo", "-n", "pkill", "-9", "-f", os.path.basename(program)], capture_output=True)
            p.kill(); p.wait()
            print(f"(simulator stopped after {timeout} s)")
    os.close(master); os.close(slave)
    text = open(log, "rb").read().decode(errors="replace")
    return "\n".join(ln for ln in text.splitlines() if "bind failed" not in ln and "Cannot bind" not in ln)


def reports(output):
    out = []
    for m in re.finditer(r"<(\w+)[^>]*?MPos:([-\d.,]+)", output):
        out.append((m.group(1), [float(v) for v in m.group(2).split(",")]))
    return out


def dist_to_segment(p, a, b):
    ax, ay = a; bx, by = b
    t = ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)
    t = max(0.0, min(1.0, t))
    return math.hypot(p[0] - ax - t * (bx - ax), p[1] - ay - t * (by - ay))


def main():
    program, real_yaml = sys.argv[1], sys.argv[2]
    cfg, home = sim_config(real_yaml)
    target = (home[0] + 280.0, home[1] + 190.0)
    failures = []

    def check(ok, what):
        print(("PASS  " if ok else "FAIL  ") + what)
        if not ok:
            failures.append(what)

    # ---- 1: boots, loads the module, moves in a straight line and comes back
    out = run(program, cfg, ["$Report/Interval=100", f"G90 G21 G1 X{target[0]} Y{target[1]} F3000", "G4 P0.6",
                             f"G1 X{home[0]} Y{home[1]} F3000", "G4 P0.6", "G1 Z-5 F300", "G4 P0.6"])
    print("=" * 30, "simulator output, run 1", "=" * 30); print(out[:3500]); print("   ...   "); print(out[-3500:])
    check("Kinematic system: BeltCNC" in out, "firmware starts with the BeltCNC module")
    check("error" not in out.lower().replace("no error", "") and "ALARM" not in out, "no errors or alarms")
    rep = reports(out)
    check(len(rep) > 10, f"position reports received ({len(rep)})")
    if rep:
        check(math.hypot(rep[0][1][0] - home[0], rep[0][1][1] - home[1]) < 0.05, f"starts at the table centre {rep[0][1][:2]}")
        far = min(math.hypot(r[1][0] - target[0], r[1][1] - target[1]) for r in rep)
        check(far < 0.1, f"reaches the target (closest report {far:.3f} mm away)")
        off = max(dist_to_segment(r[1], home, target) for r in rep)
        check(off < 0.3, f"stays on the straight line between them (worst {off:.3f} mm off)")
        end = rep[-1][1]
        check(math.hypot(end[0] - home[0], end[1] - home[1]) < 0.05, f"comes back to the centre {end[:2]}")
        check(abs(end[2] + 5.0) < 0.02, f"Z moves on its own (Z = {end[2]})")
        check(all(abs(r[1][3]) < 1e-6 and abs(r[1][4]) < 1e-6 for r in rep), "the unused A and B words stay at zero")

    # ---- 2: belt trim does not change the reported position, and "$HX $HY" re-bases cleanly
    out = run(program, cfg, ["$Report/Interval=100", "$/kinematics/BeltCNC/sw_trim=-3.5", f"G90 G53 G1 X{home[0]} Y{home[1]} F600", "G4 P0.6",
                             f"G1 X{home[0] + 100} Y{home[1]} F3000", "G4 P0.6", "$HX", "$HY",
                             "G91 G1 X1 F600", "G90", "G4 P0.6"])   # the 1 mm nudge makes it report the new position
    print("=" * 30, "simulator output, run 2", "=" * 30); print(out[-4000:])
    rep = reports(out)
    check("error" not in out.lower().replace("no error", "") and "ALARM" not in out, "trim and centre commands are accepted")
    if rep:
        mid = min(math.hypot(r[1][0] - (home[0] + 100), r[1][1] - home[1]) for r in rep)
        check(mid < 0.1, f"moves correctly with a trim applied (closest report {mid:.3f} mm from target)")
        end = rep[-1][1]
        check(math.hypot(end[0] - home[0] - 1, end[1] - home[1]) < 0.05, f"$HX $HY declare the centre (1 mm nudge from it ends at {end[:2]})")

    # ---- 3: refuses to leave the table
    out = run(program, cfg, ["G90 G1 X-500 Y610 F3000", "G4 P0.3"])
    check("error" in out.lower() or "ALARM" in out, "a move off the table is refused")

    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED"); sys.exit(1)
    print("all simulator checks passed")


if __name__ == "__main__":
    main()
