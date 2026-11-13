"""Servo layer: named joints, calibration, software limits and smooth motion."""
import json
import threading
import time


class MockBoard:
    """Stands in for a PCA9685 when running off the Pi (or with --mock)."""

    def __init__(self, addr):
        self.addr = addr
        self.pulses = {}

    def set_us(self, ch, us):
        self.pulses[ch] = us

    def release(self, ch):
        self.pulses.pop(ch, None)


class PCA9685Board:
    def __init__(self, addr):
        import board
        import busio
        from adafruit_pca9685 import PCA9685
        self.pca = PCA9685(busio.I2C(board.SCL, board.SDA), address=addr)
        self.pca.frequency = 50

    def set_us(self, ch, us):
        self.pca.channels[ch].duty_cycle = int(us / 20000.0 * 0xFFFF)

    def release(self, ch):
        self.pca.channels[ch].duty_cycle = 0


class Rig:
    def __init__(self, config_path, mock=False):
        self.config_path = config_path
        self.cfg = json.load(open(config_path))
        cls = MockBoard if mock else PCA9685Board
        self.boards = {k: cls(int(v, 16)) for k, v in self.cfg['boards'].items()}
        self.joints = self.cfg['joints']
        self.pos = {n: 0.0 for n in self.joints}       # where each joint is being driven now
        self.target = dict(self.pos)
        self.direct = set()                           # joints that skip smoothing (lip sync)
        self.enabled = True
        self.lock = threading.Lock()
        self._stop = False
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    # ---------------------------------------------------------------- maths
    def clamp(self, name, deg):
        j = self.joints[name]
        return max(j['min'], min(j['max'], float(deg)))

    def pulse(self, name, deg):
        j = self.joints[name]
        us_per_deg = 2000.0 / j['range_deg']
        us = j['center_us'] + (-1 if j.get('invert') else 1) * deg * us_per_deg
        return max(500.0, min(2500.0, us))

    # -------------------------------------------------------------- control
    def set(self, name, deg, direct=False):
        if name not in self.joints:
            raise KeyError(name)
        with self.lock:
            self.target[name] = self.clamp(name, deg)
            (self.direct.add if direct else self.direct.discard)(name)

    def pose(self, values):
        for n, v in values.items():
            self.set(n, v)

    def home(self):
        self.pose({n: 0 for n in self.joints})

    def relax(self):
        """Stop sending pulses so the servos go limp."""
        self.enabled = False
        for n, j in self.joints.items():
            self.boards[j['board']].release(j['ch'])

    def wake(self):
        self.enabled = True

    def save(self):
        json.dump(self.cfg, open(self.config_path, 'w'), indent=2)

    def step(self, dt):
        with self.lock:
            for n, j in self.joints.items():
                err = self.target[n] - self.pos[n]
                if n in self.direct:
                    self.pos[n] = self.target[n]
                else:
                    # ease in to the target, capped at the joint's top speed
                    move = err * min(1.0, 8.0 * dt)
                    cap = j['speed'] * dt
                    self.pos[n] += max(-cap, min(cap, move))
                if self.enabled:
                    self.boards[j['board']].set_us(j['ch'], self.pulse(n, self.pos[n]))

    def _loop(self):
        dt = 1.0 / self.cfg.get('update_hz', 50)
        nxt = time.monotonic()
        while not self._stop:
            self.step(dt)
            nxt += dt
            time.sleep(max(0.0, nxt - time.monotonic()))

    def close(self):
        self._stop = True
        self.thread.join(timeout=1)
