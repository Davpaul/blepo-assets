#!/usr/bin/env python3
"""Start the Twist control panel.   python3 run.py            (on the Pi)
                                    python3 run.py --mock     (anywhere, no hardware)"""
import argparse
import os

from twist.idle import Idle
from twist.lipsync import Speaker
from twist.rig import Rig
from twist.server import serve

HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--mock', action='store_true', help='run without servo boards')
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--config', default=os.path.join(HERE, 'config.json'))
    a = ap.parse_args()
    rig = Rig(a.config, mock=a.mock)
    serve(rig, Speaker(rig), Idle(rig), os.path.join(HERE, 'sounds'), a.port)
