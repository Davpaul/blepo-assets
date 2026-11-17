# Installing the firmware

The controller runs [FluidNC](https://github.com/bdring/FluidNC), an open-source CNC firmware, with one extra module that understands the four belts.

## What is in this folder

| File | What it is |
|---|---|
| `BeltCNC.h`, `BeltCNC.cpp` | The FluidNC module (kinematics) for the belt machine |
| `BeltKin.h` | The belt geometry maths, kept separate so it can be tested on a PC |
| `belt-cnc.yaml` | FluidNC config for the MKS TinyBee board |
| `test/` | A PC test that checks the maths against the Python model |

## The easy way

Download the **belt-cnc-software** artifact from the latest green **Belt CNC firmware** run under the repo's Actions tab. Run `flash.sh <port>` (Mac, Linux) or `flash.bat COMx` (Windows), then `python3 tools/beltcnc.py upload --port <port> belt-cnc.yaml`.

## Building it yourself

1. Install [VS Code](https://code.visualstudio.com/) and its **PlatformIO** extension.
2. Download the FluidNC source: `git clone https://github.com/bdring/FluidNC.git`
3. Copy `BeltCNC.h`, `BeltCNC.cpp` and `BeltKin.h` into `FluidNC/src/Kinematics/` inside it.
4. Open the FluidNC folder in VS Code. In the PlatformIO panel choose the `wifi` environment and click **Upload**, with the TinyBee connected by USB.
5. Also run **Upload Filesystem Image** once, which installs the web page.

## Load the config

1. Connect to the board (the FluidNC web installer's terminal, or `fluidterm` from the FluidNC download).
2. Upload `belt-cnc.yaml` to the board's local file system.
3. Send `$Config/Filename=belt-cnc.yaml` and restart.
4. On restart the log should show `Kinematic system: BeltCNC` and no errors.

Re-upload the file whenever `tools/table_config.py` changes it.

## Things to adjust in `belt-cnc.yaml`

- **Motor directions.** A positive move must pay belt out. `tools/belt_setup.py` has a `dirtest` command. To reverse a motor, add or remove `:low` on its `direction_pin`.
- **Z direction.** `$HZ` should raise the router. If it goes down, flip the Z `direction_pin` the same way.
- **Z steps.** 400 steps/mm suits the donor 8mm-lead screw. Use 1600 for a 2mm-lead screw.
- **`belt_dz`.** See BUILD.md step 7.

## Commands this adds

- `$HX` and `$HY`: "the bit is at the centre mark now". Nothing moves. Use after re-seating the sled on the mark.
- `$/kinematics/BeltCNC/sw_trim=-2.0` (also `se_`, `ne_`, `nw_`): take in 2mm of belt at that corner. It takes effect on the next move. `belt_setup.py` drives this for you.

## Testing the maths on a PC

```
python3 tools/gen_test_vectors.py
g++ -std=c++17 -O2 -I firmware firmware/test/host_test.cpp -o belt_test && ./belt_test
```

## Status

The automated build compiles this module into FluidNC for the ESP32 and for FluidNC's PC simulator, and runs the simulator against the real config. It has not been run on a physical board. FluidNC's internals change between releases, so the build is pinned to one FluidNC commit (see the workflow file). To move to a newer FluidNC, change that commit and see whether the build stays green.

## Licence

FluidNC is GPLv3, and this module plugs into it, so these firmware files are GPLv3 too. You can use and change them freely. If you pass the firmware on to anyone else, pass on the source with it.
