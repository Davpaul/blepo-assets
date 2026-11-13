"""Off-hardware test of the software: python3 test_software.py"""
import json, math, os, shutil, struct, sys, tempfile, threading, time, urllib.request, wave
from twist.rig import Rig
from twist.lipsync import envelope, Speaker
from twist.idle import Idle
from twist.server import make_handler
from http.server import ThreadingHTTPServer

tmp = tempfile.mkdtemp()
cfgp = os.path.join(tmp, 'config.json'); shutil.copy('config.json', cfgp)
cfg = json.load(open(cfgp)); cfg['lipsync']['player'] = [sys.executable, '-c', 'import time,sys;time.sleep(1.0)']
json.dump(cfg, open(cfgp, 'w'))
# 1 s test clip: silence, loud burst, silence, quieter burst
wavp = os.path.join(tmp, 't.wav')
with wave.open(wavp, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
    amp = lambda t: 0 if t < .2 else 20000 if t < .5 else 0 if t < .7 else 8000
    w.writeframes(b''.join(struct.pack('<h', int(amp(i / 16000) * math.sin(i * .3))) for i in range(16000)))
env, dur = envelope(wavp)
assert abs(dur - 1.0) < .03 and env[:8].max() < .05 and env[15:24].min() > .8 and env[30:34].max() < .35 and .3 < env[45] < .8, env
rig = Rig(cfgp, mock=True)
# limits and pulse mapping
rig.set('head_roll', 90); assert rig.target['head_roll'] == 25
assert rig.pulse('yaw', 0) == 1500 and abs(rig.pulse('yaw', 90) - 2500) < 1e-6 and abs(rig.pulse('ext_l', 135) - 2500) < 1e-6
assert rig.pulse('pan_r', 45) == 1000          # inverted joint
rig.set('head_yaw', 60); time.sleep(.1); assert 0 < rig.pos['head_yaw'] < 60     # eased, speed limited
time.sleep(1.0); assert abs(rig.pos['head_yaw'] - 60) < 1.5, rig.pos['head_yaw']
assert abs(rig.boards['A'].pulses[4] - rig.pulse('head_yaw', rig.pos['head_yaw'])) < 15
# lip sync follows the clip and closes afterwards
sp = Speaker(rig); peak = [0]
t = sp.play(wavp)
while t.is_alive():
    peak[0] = max(peak[0], rig.pos['jaw']); time.sleep(.01)
time.sleep(.3)
assert peak[0] > 25 and rig.pos['jaw'] < 1, (peak, rig.pos['jaw'])
# web API
idle = Idle(rig); os.makedirs(os.path.join(tmp, 's')); shutil.copy(wavp, os.path.join(tmp, 's', 'hello.wav'))
srv = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(rig, sp, idle, os.path.join(tmp, 's')))
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = 'http://127.0.0.1:%d' % srv.server_address[1]
post = lambda p, d: json.load(urllib.request.urlopen(urllib.request.Request(base + p, json.dumps(d).encode())))
assert b'Twist' in urllib.request.urlopen(base + '/').read()
post('/api/set', {'tilt_l': 30, 'ext_r': 500}); assert rig.target['tilt_l'] == 30 and rig.target['ext_r'] == 125
post('/api/pose', {'name': 'curious'}); assert rig.target['head_roll'] == 18
post('/api/save_pose', {'name': 'mine'}); assert 'mine' in json.load(open(cfgp))['poses']
post('/api/trim', {'name': 'jaw', 'center_us': 1540}); post('/api/save_config', {})
assert json.load(open(cfgp))['joints']['jaw']['center_us'] == 1540
st = json.load(urllib.request.urlopen(base + '/api/state')); assert st['sounds'] == ['hello.wav'] and len(st['joints']) == 13
post('/api/idle', {'on': True}); time.sleep(.3); assert rig.target['lean_pitch'] != 0
post('/api/relax', {}); assert not rig.enabled and not idle.on
try:
    post('/api/set', {'nope': 1}); raise SystemExit('bad joint accepted')
except urllib.error.HTTPError as e:
    assert e.code == 400
print('software OK')
