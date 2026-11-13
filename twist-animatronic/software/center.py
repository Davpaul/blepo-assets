#!/usr/bin/env python3
"""Sends every servo to its centre pulse and holds it there.
Run this BEFORE fitting any horn, so each horn goes on at the true middle of travel."""
import time
from twist.rig import Rig

rig = Rig('config.json')
rig.home()
print('All 13 channels at centre. Fit the horns now. Ctrl-C to finish.')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    rig.relax()
