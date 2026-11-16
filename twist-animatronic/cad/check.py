"""Collision check: every pair of parts, across a set of poses. Reports overlaps above 2 mm^3."""
import sys, itertools, time
import assembly

IGNORE = [('pinion', 'rack')]          # gear mesh phase is not modelled
POSES = {
    'rest': {},
    'head A': dict(head_yaw=80, head_roll=25, head_pitch=28, jaw=40),
    'head B': dict(head_yaw=-80, head_roll=-25, head_pitch=-28, jaw=40),
    'head C': dict(head_yaw=40, head_roll=25, head_pitch=-28, jaw=0),
    'head D': dict(head_yaw=-40, head_roll=-25, head_pitch=28, jaw=-3),
    'head E': dict(head_yaw=80, head_pitch=-28, jaw=20),
    'head F': dict(head_yaw=-80, head_roll=25, jaw=40),
    'lean A': dict(yaw=45, lean_roll=22, lean_pitch=22),
    'lean B': dict(yaw=-45, lean_roll=-22, lean_pitch=-22),
    'lean C': dict(lean_roll=22, lean_pitch=-22),
    'lean D': dict(lean_roll=-22, lean_pitch=22),
    'arms A': dict(pan_l=80, tilt_l=48, ext_l=60, pan_r=-80, tilt_r=-48, ext_r=-40),
    'arms B': dict(pan_l=-80, tilt_l=-48, ext_l=-40, pan_r=80, tilt_r=48, ext_r=60),
    'arms C': dict(pan_l=0, tilt_l=48, ext_l=-40, pan_r=0, tilt_r=-48, ext_r=60),
    'all A': dict(yaw=80, lean_roll=22, lean_pitch=22, head_yaw=80, head_roll=25, head_pitch=28, jaw=40,
                  pan_l=80, tilt_l=48, ext_l=58, pan_r=-80, tilt_r=-48, ext_r=-40),
    'all B': dict(yaw=-80, lean_roll=-22, lean_pitch=-22, head_yaw=-80, head_roll=-25, head_pitch=-28, jaw=40,
                  pan_l=-80, tilt_l=-48, ext_l=-40, pan_r=80, tilt_r=48, ext_r=58),
    'all C': dict(lean_roll=22, lean_pitch=-22, head_roll=-25, head_pitch=28, jaw=-3,
                  pan_l=80, tilt_l=-48, ext_l=58, pan_r=80, tilt_r=-48, ext_r=58),
    'all D': dict(lean_roll=-22, lean_pitch=22, head_roll=25, head_pitch=-28,
                  pan_l=-80, tilt_l=48, ext_l=-40, pan_r=-80, tilt_r=48, ext_r=-40),
}


def overlaps(items, only=None):
    bbs = [s.BoundingBox() for _, s, _, _ in items]
    bad = []
    for i, j in itertools.combinations(range(len(items)), 2):
        a, b = bbs[i], bbs[j]
        if (a.xmin > b.xmax or b.xmin > a.xmax or a.ymin > b.ymax or b.ymin > a.ymax
                or a.zmin > b.zmax or b.zmin > a.zmax):
            continue
        ni, nj = items[i][0], items[j][0]
        if any((x in ni and y in nj) or (x in nj and y in ni) for x, y in IGNORE):
            continue
        if only and not any(k in ni or k in nj for k in only):
            continue
        try:
            v = items[i][1].intersect(items[j][1]).Volume()
        except Exception:
            v = -1
        if v > 2 or v < 0:
            bad.append((ni, nj, v))
    return bad


if __name__ == '__main__':
    d = float(sys.argv[1]) if len(sys.argv) > 1 else 26.7
    names = sys.argv[2:] or list(POSES)
    total = 0
    for name in names:
        t = time.time()
        items = [it for it in assembly.build(d, POSES[name], extras=True) if 'arm_rod_' not in it[0]]
        bad = overlaps(items)
        total += len(bad)
        print(f'[{name}] {len(bad)} overlaps ({time.time() - t:.0f}s)')
        for a, b, v in bad:
            print(f'    {a:22s} x {b:22s} {v:9.1f} mm3')
    print('TOTAL', total)
