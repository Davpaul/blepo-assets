"""Exports every printable part as STL (already rotated into its print orientation) plus a STEP of the rig."""
import os, sys, json
import cadquery as cq
import parts as P
import assembly

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'print')
PIPES = {'26.7mm': 26.7, '25.0mm': 25.0}

RX = lambda a: ((1, 0, 0), a)
RY = lambda a: ((0, 1, 0), a)
# name: (builder, quantity, rotation into print orientation, supports?, note)
COMMON = {
    'tripod_base': (P.tripod_base, 1, RX(180), 'no', 'Flange on the bed. 5 walls, 40% infill: this carries everything.'),
    'yaw_hub': (P.yaw_hub, 1, None, 'no', ''),
    'bracket_L': (P.bracket_L, 4, RX(90), 'no', 'Plate on the bed. Top wall is a 36 mm bridge.'),
    'roll_yoke': (P.roll_yoke, 2, RX(-90), 'yes, bed only', 'Servo cage on the bed, arms pointing up.'),
    'pitch_yoke': (P.pitch_yoke, 2, RX(-90), 'no', 'Top plate on the bed, arms pointing up.'),
    'tilt_yoke': (lambda: P.pitch_yoke(P.H_TILT), 2, RX(-90), 'no', 'Tall version of pitch_yoke for the arm units.'),
    'head_frame': (P.head_frame, 1, RX(-90), 'no', 'Plate on the bed.'),
    'jaw_yoke': (P.jaw_yoke, 1, RX(90), 'no', 'Tongue on the bed.'),
    'paddle': (P.paddle, 2, None, 'no', 'Or cut from 3 mm plywood or acrylic.'),
    'servo_base': (P.servo_base, 2, RX(90), 'no', 'Teeth facing up.'),
    'slide_stage': (P.slide_stage, 2, RX(180), 'no', 'Shelf on the bed.'),
    'rack_guide': (P.rack_guide, 2, RX(90), 'no', 'Standing on end.'),
    'rack': (P.rack, 2, None, 'no', '180 mm long: place diagonally on small beds.'),
    'rod_cap': (P.rod_cap, 2, RX(180), 'no', ''),
    'pinion': (P.pinion, 2, None, 'no', '4 walls.'),
    'speaker_mount': (P.speaker_mount, 1, None, 'no', 'Teeth facing up.'),
    'accessory_mount': (P.accessory_mount, 1, None, 'no', 'Optional. Camera, mic, light.'),
}
PER_PIPE = {
    'knuckle': (P.knuckle, 10, RY(-90), 'no', 'Bore vertical. 5 walls. Print one first and test it on your pipe.'),
    'neck_base': (P.neck_base, 1, RX(-90), 'no', 'Leg on the bed, teeth up.'),
    'carriage': (P.carriage, 1, RX(90), 'no', 'Flange on the bed. 5 walls, 40% infill.'),
    'pipe_saddle': (P.pipe_saddle, 2, RY(-90), 'no', 'Bore vertical.'),
}


def oriented(wp, rot):
    s = wp.val()
    if rot:
        s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(*rot[0]), rot[1])
    bb = s.BoundingBox()
    return s.translate(cq.Vector(-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


def export(name, builder, qty, rot, sup, note, folder, rows):
    s = oriented(builder(), rot)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name + '.stl')
    s.exportStl(path, tolerance=0.02, angularTolerance=0.15)
    bb = s.BoundingBox()
    rows.append(dict(part=name, qty=qty, x=round(bb.xlen, 1), y=round(bb.ylen, 1), z=round(bb.zlen, 1),
                     volume_cm3=round(s.Volume() / 1000, 1), supports=sup, note=note,
                     file=os.path.relpath(path, OUT), valid=bool(s.isValid())))
    print(f'{name:16s} x{qty:<2d} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:6.1f}  {s.Volume() / 1000:6.1f} cm3')


if __name__ == '__main__':
    rows = []
    for name, (b, q, r, sup, note) in COMMON.items():
        export(name, b, q, r, sup, note, os.path.join(OUT, 'stl'), rows)
    for label, d in PIPES.items():
        for name, (b, q, r, sup, note) in PER_PIPE.items():
            export(name, (lambda b=b, d=d: b(d)), q, r, sup, note, os.path.join(OUT, 'stl', 'pipe_' + label), rows)
    json.dump(rows, open(os.path.join(OUT, 'parts.json'), 'w'), indent=1)
    if '--step' in sys.argv:
        asm = cq.Assembly()
        for name, shape, col, link in assembly.build():
            asm.add(shape, name=name, color=cq.Color(*col))
        asm.save(os.path.join(OUT, 'twist_core_assembly.step'))
        print('STEP written')
