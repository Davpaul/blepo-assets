"""Mouth sync: turns a WAV file into a jaw-angle timeline and plays the two together."""
import subprocess
import tempfile
import threading
import time
import wave

import numpy as np

FRAME_MS = 20


def envelope(path, gate=0.06, attack_ms=30, release_ms=90):
    """Loudness per 20 ms frame, 0..1, with a fast open and a slower close like a real jaw."""
    with wave.open(path, 'rb') as w:
        rate, ch, width, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    dtype = {1: np.uint8, 2: np.int16, 4: np.int32}[width]
    x = np.frombuffer(raw, dtype=dtype).astype(np.float64)
    if width == 1:
        x -= 128.0
    x = x.reshape(-1, ch).mean(axis=1) / float(2 ** (8 * width - 1))
    hop = int(rate * FRAME_MS / 1000)
    nfr = max(1, len(x) // hop)
    rms = np.sqrt((x[:nfr * hop].reshape(nfr, hop) ** 2).mean(axis=1))
    ref = np.percentile(rms, 95) or 1.0
    lvl = np.clip(rms / ref, 0.0, 1.0)
    lvl = np.where(lvl < gate, 0.0, (lvl - gate) / (1.0 - gate)) ** 0.7
    out = np.zeros(nfr)
    up, down = FRAME_MS / max(attack_ms, 1), FRAME_MS / max(release_ms, 1)
    v = 0.0
    for i, t in enumerate(lvl):
        v += (t - v) * min(1.0, up if t > v else down)
        out[i] = v
    return out, nfr * FRAME_MS / 1000.0


class Speaker:
    def __init__(self, rig):
        self.rig = rig
        self.cfg = rig.cfg['lipsync']
        self.proc = None
        self.busy = threading.Lock()

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()

    def play(self, wav, block=False):
        t = threading.Thread(target=self._run, args=(wav,), daemon=True)
        t.start()
        if block:
            t.join()
        return t

    def say(self, text, block=False):
        wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
        cmd = [a.format(wav=wav, text=text) for a in self.cfg['tts']]
        subprocess.run(cmd, check=True)
        return self.play(wav, block)

    def _run(self, wav):
        c = self.cfg
        env, dur = envelope(wav, c['gate'], c['attack_ms'], c['release_ms'])
        with self.busy:
            self.proc = subprocess.Popen(c['player'] + [wav])
            t0 = time.monotonic()
            lead = c['lead_ms'] / 1000.0          # the jaw starts early to cover servo travel time
            while self.proc.poll() is None:
                i = int((time.monotonic() - t0 + lead) * 1000 / FRAME_MS)
                if i >= len(env):
                    break
                self.rig.set('jaw', c['jaw_closed'] + env[i] * (c['jaw_open'] - c['jaw_closed']), direct=True)
                time.sleep(FRAME_MS / 2000.0)
            self.rig.set('jaw', c['jaw_closed'])
            self.proc.wait()
