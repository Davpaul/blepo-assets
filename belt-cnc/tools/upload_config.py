"""Send a settings file to the controller over USB and make it the active config.

    python3 upload_config.py --port /dev/ttyUSB0 ../firmware/belt-cnc.yaml     (Windows: --port COM5)

Uses the XMODEM file transfer built into FluidNC. Needs:  pip install pyserial
"""
import argparse, os, sys, time

SOH, EOT, ACK, NAK, CAN, PAD = 0x01, 0x04, 0x06, 0x15, 0x18, 0x1A


def crc16(data):
    crc = 0
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def _wait_for(stream, wanted, timeout):
    """Read single bytes until one of `wanted` turns up. Returns it, or None on timeout."""
    end = time.time() + timeout
    while time.time() < end:
        b = stream.read(1)
        if b and b[0] in wanted:
            return b[0]
    return None


def xmodem_send(stream, data, log=print):
    """stream needs read(n) -> bytes (may be empty on timeout) and write(bytes)."""
    start = _wait_for(stream, (ord("C"), NAK, CAN), 15)
    if start is None:
        raise IOError("the controller did not start the transfer")
    if start == CAN:
        raise IOError("the controller refused the file")
    use_crc = start == ord("C")
    blocks = [data[i:i + 128] for i in range(0, len(data), 128)] or [b""]
    for n, block in enumerate(blocks, start=1):
        block = block.ljust(128, bytes([PAD]))
        check = crc16(block).to_bytes(2, "big") if use_crc else bytes([sum(block) & 0xFF])
        packet = bytes([SOH, n & 0xFF, 0xFF - (n & 0xFF)]) + block + check
        for attempt in range(10):
            stream.write(packet)
            reply = _wait_for(stream, (ACK, NAK, CAN), 5)
            if reply == ACK:
                break
            if reply == CAN:
                raise IOError("the controller cancelled the transfer")
        else:
            raise IOError(f"block {n} was not accepted")
        if n % 8 == 0:
            log(f"   sent {min(n * 128, len(data))} of {len(data)} bytes")
    for attempt in range(10):
        stream.write(bytes([EOT]))
        if _wait_for(stream, (ACK,), 3) == ACK:
            return len(data)
    raise IOError("the controller did not confirm the end of the file")


def upload(stream, path, name=None, log=print):
    data = open(path, "rb").read()
    name = name or os.path.basename(path)
    stream.write(b"\n")
    time.sleep(0.3)
    stream.read(4096)                                     # clear anything waiting
    stream.write(f"$Xmodem/Receive={name}\n".encode())
    n = xmodem_send(stream, data, log)
    time.sleep(0.5)
    log(f"   sent {n} bytes as {name}")
    stream.write(f"$Config/Filename={name}\n".encode())
    time.sleep(0.5)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--port", required=True); ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--no-restart", action="store_true", help="do not restart the controller afterwards")
    a = ap.parse_args()
    import serial
    ser = serial.Serial(a.port, a.baud, timeout=0.2)
    time.sleep(1.5)
    upload(ser, a.file)
    if not a.no_restart:
        ser.write(b"$Bye\n")
        print("   restarting the controller ...")
        end, text = time.time() + 8, b""
        while time.time() < end:
            text += ser.read(4096)
        text = text.decode(errors="replace")
        for line in text.splitlines():
            if "MSG" in line:
                print("   " + line.strip())
        if "Kinematic system: BeltCNC" in text:
            print("Config loaded: the controller reports the BeltCNC module is running.")
        elif "error" in text.lower():
            print("!! The controller reported an error above. Check the config file.")
        else:
            print("Config sent. Could not confirm the restart: open a terminal and look for 'Kinematic system: BeltCNC'.")


if __name__ == "__main__":
    main()
