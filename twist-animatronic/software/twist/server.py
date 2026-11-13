"""Web control panel. Open http://<pi address>:8080 on a phone or laptop on the same network."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))


def make_handler(rig, speaker, idle, sounds_dir):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, obj, code=200, ctype='application/json'):
            body = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
            self.send_response(code)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/':
                return self._send(open(os.path.join(HERE, 'panel.html'), 'rb').read(), ctype='text/html')
            if self.path == '/api/state':
                sounds = sorted(f for f in os.listdir(sounds_dir) if f.lower().endswith('.wav'))
                return self._send({
                    'joints': {n: dict(j, pos=round(rig.pos[n], 1), target=round(rig.target[n], 1))
                               for n, j in rig.joints.items()},
                    'poses': sorted(rig.cfg['poses']), 'sounds': sounds, 'idle': idle.on, 'enabled': rig.enabled})
            self._send({'error': 'not found'}, 404)

        def do_POST(self):
            n = int(self.headers.get('Content-Length') or 0)
            try:
                d = json.loads(self.rfile.read(n) or b'{}')
                self._send(self.route(self.path, d))
            except Exception as e:                       # report bad requests instead of dying
                self._send({'error': '%s: %s' % (type(e).__name__, e)}, 400)

        def route(self, path, d):
            if path == '/api/set':
                rig.pose(d)
            elif path == '/api/pose':
                idle.on = False
                rig.home() if d['name'] == 'home' else rig.pose(rig.cfg['poses'][d['name']])
            elif path == '/api/save_pose':
                rig.cfg['poses'][d['name']] = {k: round(v, 1) for k, v in rig.target.items() if abs(v) > 0.5}
                rig.save()
            elif path == '/api/say':
                speaker.say(d['text'])
            elif path == '/api/play':
                speaker.play(os.path.join(sounds_dir, os.path.basename(d['file'])))
            elif path == '/api/stop':
                speaker.stop()
            elif path == '/api/idle':
                idle.on = bool(d['on'])
            elif path == '/api/relax':
                idle.on = False
                rig.relax()
            elif path == '/api/wake':
                rig.wake()
            elif path == '/api/trim':
                j = rig.joints[d['name']]
                for k in ('center_us', 'min', 'max', 'invert'):
                    if k in d:
                        j[k] = d[k]
                rig.set(d['name'], rig.target[d['name']])
            elif path == '/api/save_config':
                rig.save()
            else:
                raise KeyError(path)
            return {'ok': True}

    return H


def serve(rig, speaker, idle, sounds_dir, port=8080):
    srv = ThreadingHTTPServer(('0.0.0.0', port), make_handler(rig, speaker, idle, sounds_dir))
    print('Twist control panel on port %d' % port)
    srv.serve_forever()
