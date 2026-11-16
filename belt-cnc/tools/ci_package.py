"""Collect the built firmware, flashing scripts, config and tools into one folder.

    python3 ci_package.py <fluidnc checkout> <belt-cnc folder> <output folder>

Run by the GitHub workflow after the firmware build.
"""
import glob, os, shutil, struct, sys


def fs_offset(partitions_bin):
    """Offset of the file-system partition, read from the built partition table."""
    data = open(partitions_bin, "rb").read()
    for i in range(0, len(data) - 31, 32):
        magic, ptype, sub, offset, size = struct.unpack_from("<HBBII", data, i)
        if magic != 0x50AA:
            continue
        label = data[i + 12:i + 28].split(b"\0")[0].decode(errors="replace")
        if ptype == 1 and sub in (0x82, 0x83) or label in ("spiffs", "littlefs"):
            return offset
    raise SystemExit("no file-system partition found in " + partitions_bin)


def main():
    fluidnc, src, out = sys.argv[1:4]
    dest = os.path.join(out, "belt-cnc-software")
    fw = os.path.join(dest, "firmware")
    os.makedirs(fw, exist_ok=True)
    build = os.path.join(fluidnc, ".pio", "build", "wifi")
    for name in ("firmware.bin", "bootloader.bin", "partitions.bin", "littlefs.bin"):
        shutil.copy(os.path.join(build, name), fw)
    boot = glob.glob(os.path.expanduser("~/.platformio/packages/framework-arduinoespressif32*/tools/partitions/boot_app0.bin"))
    if not boot:
        raise SystemExit("boot_app0.bin not found in the PlatformIO packages")
    shutil.copy(boot[0], fw)
    off = fs_offset(os.path.join(build, "partitions.bin"))
    for script in glob.glob(os.path.join(src, "firmware", "flash", "*")):
        text = open(script).read().replace("@FS_OFFSET@", hex(off))
        open(os.path.join(dest, os.path.basename(script)), "w", newline="\r\n" if script.endswith(".bat") else "\n").write(text)
    for name in ("flash.sh",):
        if os.path.exists(os.path.join(dest, name)):
            os.chmod(os.path.join(dest, name), 0o755)
    shutil.copy(os.path.join(src, "firmware", "belt-cnc.yaml"), dest)
    shutil.copytree(os.path.join(src, "tools"), os.path.join(dest, "tools"), ignore=shutil.ignore_patterns("__pycache__", "ci_package.py", "make_pdf.py", "draw_*.py"))
    shutil.copytree(os.path.join(src, "cad"), os.path.join(dest, "cad"), ignore=shutil.ignore_patterns("__pycache__"))
    os.makedirs(os.path.join(dest, "source"), exist_ok=True)
    for name in ("BeltCNC.h", "BeltCNC.cpp", "BeltKin.h", "INSTALL.md"):
        shutil.copy(os.path.join(src, "firmware", name), os.path.join(dest, "source"))
    open(os.path.join(dest, "VERSION.txt"), "w").write(
        "FluidNC commit: " + os.popen(f"git -C {fluidnc} rev-parse HEAD").read().strip() + "\n"
        "belt-cnc commit: " + os.popen("git rev-parse HEAD").read().strip() + "\n"
        f"file system offset: {hex(off)}\n")
    print("packaged into", dest)
    for root, _, files in os.walk(dest):
        for f in sorted(files):
            p = os.path.join(root, f)
            print(f"  {os.path.relpath(p, dest):45s} {os.path.getsize(p):>9d}")


if __name__ == "__main__":
    main()
