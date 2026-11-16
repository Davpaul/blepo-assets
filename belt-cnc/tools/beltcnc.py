"""One front door for the Belt CNC tools.

    python3 beltcnc.py table 2500.4 1280.8 2500.4 1280.8 2789.6 --write ../belt-cnc.yaml
    python3 beltcnc.py upload --port COM5 ../belt-cnc.yaml
    python3 beltcnc.py setup --port COM5 --config ../belt-cnc.yaml
    python3 beltcnc.py reach --width 2440 --height 1220
    python3 beltcnc.py dots --table 2440 1220 --inset 300 > dots.gcode
    python3 beltcnc.py calibrate --posts ... --dots ...
    python3 beltcnc.py test

Add --help after any command for its options.
"""
import runpy, sys, os

COMMANDS = {
    "table": ("table_config.py", "turn five tape measurements into controller settings"),
    "upload": ("upload_config.py", "send the settings file to the controller"),
    "setup": ("belt_setup.py", "check motor directions, snug the belts, test, pack away"),
    "reach": ("simulate.py", "map where on a table the machine can hold the router"),
    "dots": ("make_test_pattern.py", "write G-code that marks test dots"),
    "calibrate": ("calibrate.py", "work out corrections from measurements of the test dots"),
    "test": ("test_tools.py", "check these tools work on this computer"),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help") or sys.argv[1] not in COMMANDS:
        print(__doc__)
        for name, (_, what) in COMMANDS.items():
            print(f"  {name:10s} {what}")
        sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 1)
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), COMMANDS[sys.argv[1]][0])
    sys.argv = [script] + sys.argv[2:]
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
