"""Keeps the puppet alive between cues: breathing, small head drifts, the odd glance."""
import math
import random
import threading
import time


class Idle:
    def __init__(self, rig):
        self.rig = rig
        self.on = False
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        t0 = time.monotonic()
        nxt, look = 0.0, (0.0, 0.0, 0.0)
        while True:
            time.sleep(0.05)
            if not self.on:
                continue
            t = time.monotonic() - t0
            if t > nxt:
                nxt = t + random.uniform(2.0, 6.0)
                look = (random.uniform(-35, 35), random.uniform(-8, 12), random.uniform(-8, 8))
            self.rig.set('lean_pitch', 2.5 * math.sin(t * 1.3))
            self.rig.set('lean_roll', 1.5 * math.sin(t * 0.7))
            self.rig.set('head_yaw', look[0])
            self.rig.set('head_pitch', look[1] + 1.5 * math.sin(t * 1.3 + 1))
            self.rig.set('head_roll', look[2])
            self.rig.set('yaw', look[0] * 0.25)
