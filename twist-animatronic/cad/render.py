"""Documentation renders (run with: xvfb-run -a python3 render.py)."""
import json, math, os
import cadquery as cq
import vtk
import assembly
import parts as P

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'img')


def polydata(shape, tol=0.25):
    verts, tris = shape.tessellate(tol, 0.25)
    pts = vtk.vtkPoints()
    for v in verts:
        pts.InsertNextPoint(v.x, v.y, v.z)
    cells = vtk.vtkCellArray()
    for t in tris:
        cells.InsertNextCell(3, t)
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetPolys(cells)
    n = vtk.vtkPolyDataNormals()
    n.SetInputData(pd)
    n.SetFeatureAngle(40)
    n.Update()
    return n.GetOutput()


def render(items, name, view, size=(1800, 1400), zoom=1.0, labels=(), scale=1.0, auto=False):
    """items: (name, shape, colour[, opacity]); labels: (text, item name or xyz, text offset xyz)."""
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    centres = {}
    for it in items:
        nm, shape, col = it[0], it[1], it[2]
        op = it[4] if len(it) > 4 else 1.0
        bb = shape.BoundingBox()
        centres[nm] = ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)
        pd = polydata(shape)
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(pd)
        a = vtk.vtkActor()
        a.SetMapper(m)
        p = a.GetProperty()
        p.SetColor(*col); p.SetAmbient(0.3); p.SetDiffuse(0.7); p.SetOpacity(op)
        ren.AddActor(a)
        if op < 1:
            continue
        e = vtk.vtkFeatureEdges()
        e.SetInputData(pd)
        e.BoundaryEdgesOff(); e.NonManifoldEdgesOff(); e.ManifoldEdgesOff(); e.FeatureEdgesOn()
        e.SetFeatureAngle(35)
        em = vtk.vtkPolyDataMapper()
        em.SetInputConnection(e.GetOutputPort())
        em.ScalarVisibilityOff()
        ea = vtk.vtkActor()
        ea.SetMapper(em)
        ea.GetProperty().SetColor(0.12, 0.12, 0.12)
        ea.GetProperty().SetLineWidth(1.3)
        ren.AddActor(ea)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(*size)
    win.SetMultiSamples(8)
    win.AddRenderer(ren)
    cam = ren.GetActiveCamera()
    cam.SetPosition(*view); cam.SetFocalPoint(0, 0, 0); cam.SetViewUp(0, 0, 1)
    cam.ParallelProjectionOn()
    ren.ResetCamera()
    cam.Zoom(zoom)
    ren.ResetCameraClippingRange()
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.Update()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + '.png')
    wr = vtk.vtkPNGWriter()
    wr.SetFileName(path)
    wr.SetInputConnection(w2i.GetOutputPort())
    wr.Write()

    def px(p):
        c = vtk.vtkCoordinate()
        c.SetCoordinateSystemToWorld()
        c.SetValue(*p)
        x, y = c.GetComputedDisplayValue(ren)
        return x, size[1] - y

    pts = []
    if auto:
        anc = [(t, px(centres[a] if isinstance(a, str) else a)) for t, a, _ in labels]
        mid = sorted(p[0] for _, p in anc)[len(anc) // 2]
        xs = [p[0] for _, p in anc]
        for col, x in ((0, min(xs) - 330), (1, max(xs) + 330)):
            grp = sorted([a for a in anc if (a[1][0] >= mid) == bool(col)], key=lambda a: a[1][1])
            for i, (t, p) in enumerate(grp):
                pts.append((t, p, (x, size[1] * (0.12 + 0.76 * (i + 0.5) / len(grp)))))
    else:
        for text, anchor, off in labels:
            a0 = px(centres[anchor] if isinstance(anchor, str) else anchor)
            pts.append((text, a0, (min(size[0] - 150, max(150, a0[0] + off[0])), min(size[1] - 40, max(40, a0[1] + off[1])))))
    annotate(path, pts, int(30 * scale))
    print('wrote', name)


def annotate(path, pts, fs=30):
    from PIL import Image, ImageDraw, ImageFont
    import matplotlib
    font = ImageFont.truetype(os.path.join(matplotlib.get_data_path(), 'fonts/ttf/DejaVuSans-Bold.ttf'), fs)
    im = Image.open(path).convert('RGB')
    d = ImageDraw.Draw(im)
    for text, a, t in pts:
        d.line([a, t], fill=(0, 0, 0), width=3)
        d.ellipse([a[0] - 6, a[1] - 6, a[0] + 6, a[1] + 6], fill=(0, 0, 0))
    for text, a, t in pts:
        box = d.multiline_textbbox(t, text, font=font, anchor='mm', align='center')
        d.rectangle([box[0] - 8, box[1] - 6, box[2] + 8, box[3] + 6], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        d.multiline_text(t, text, font=font, fill=(0, 0, 0), anchor='mm', align='center')
    # crop to content
    from PIL import ImageChops
    bg = Image.new('RGB', im.size, (255, 255, 255))
    bb = ImageChops.difference(im, bg).getbbox()
    if bb:
        im = im.crop((max(0, bb[0] - 30), max(0, bb[1] - 30), min(im.size[0], bb[2] + 30), min(im.size[1], bb[3] + 30)))
    im.save(path, optimize=True)


def render_sheet(sheet, labels):
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    for i, (nm, pd, pos) in enumerate(sheet):
        n = vtk.vtkPolyDataNormals()
        n.SetInputData(pd); n.SetFeatureAngle(40); n.Update()
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(n.GetOutput())
        a = vtk.vtkActor()
        a.SetMapper(m); a.SetPosition(*pos)
        a.GetProperty().SetColor(*(assembly.PRINT if i % 2 == 0 else assembly.PRINT2)); a.GetProperty().SetAmbient(0.3)
        ren.AddActor(a)
        e = vtk.vtkFeatureEdges()
        e.SetInputData(pd)
        e.BoundaryEdgesOff(); e.NonManifoldEdgesOff(); e.ManifoldEdgesOff(); e.FeatureEdgesOn(); e.SetFeatureAngle(35)
        em = vtk.vtkPolyDataMapper()
        em.SetInputConnection(e.GetOutputPort()); em.ScalarVisibilityOff()
        ea = vtk.vtkActor()
        ea.SetMapper(em); ea.SetPosition(*pos); ea.GetProperty().SetColor(0.12, 0.12, 0.12)
        ren.AddActor(ea)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1); win.SetSize(2000, 1500); win.SetMultiSamples(8); win.AddRenderer(ren)
    cam = ren.GetActiveCamera()
    cam.SetPosition(0, -600, 1000); cam.SetFocalPoint(0, 0, 0); cam.SetViewUp(0, 0, 1); cam.ParallelProjectionOn()
    ren.ResetCamera(); cam.Zoom(1.5); ren.ResetCameraClippingRange()
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win); w2i.Update()
    wr = vtk.vtkPNGWriter()
    path = os.path.join(OUT, 'printed_parts.png')
    wr.SetFileName(path); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()
    pts = []
    for text, p, _ in labels:
        c = vtk.vtkCoordinate()
        c.SetCoordinateSystemToWorld(); c.SetValue(*p)
        x, y = c.GetComputedDisplayValue(ren)
        pts.append((text, (x, 1500 - y), (x, 1500 - y)))
    annotate(path, pts, 24)
    print('wrote printed_parts')


def ghost_puppet(items):
    """Very rough stand-in for the puppet so the overview shows where he sits."""
    c = {n: s.BoundingBox() for n, s, *_ in items}
    hf, nb = c['head_frame2'], c['neck_fork']
    head = (cq.Workplane().sphere(1).val().scale(1.0)
            .transformGeometry(cq.Matrix([[95, 0, 0, 0], [0, 125, 0, hf.ymax - 95], [0, 0, 85, hf.zmax - 10]])))
    body = (cq.Workplane().circle(105).workplane(offset=250).circle(70).loft()
            .translate((0, (nb.ymin + nb.ymax) / 2 - 15, nb.zmin - 235)).val())
    return [('ghost_head', head, (0.55, 0.3, 0.75), 'g', 0.13), ('ghost_body', body, (0.55, 0.3, 0.75), 'g', 0.13)]


def pick(items, *keys, exclude=()):
    return [it for it in items if any(k in it[0] for k in keys) and not any(x in it[0] for x in exclude)]


if __name__ == '__main__':
    pose = dict(jaw=22, head_yaw=-20, head_roll=6, tilt_r=10, ext_r=30, ext_l=-10, pan_l=10)
    items = assembly.build(26.7, pose)
    g = ghost_puppet(items)
    render(items + g, 'overview', (1000, 1100, 600), size=(2000, 2000), zoom=1.15, labels=[
        ('tripod base\n+ body twist', 'tripod_base', (330, 60)),
        ('body lean\n(2 servos)', 'lean_roll_yoke', (420, -40)),
        ('boom', 'pipe_boom', (-330, 200)),
        ('mast', 'pipe_mast', (-420, 330)),
        ('entry pipe\n(goes in the back hole)', 'pipe_entry', (-560, 160)),
        ('cable neck:\nnod and tilt', 'neck_top', (-560, -40)),
        ('head twist servo', 'head_frame2', (-420, -200)),
        ('3 pull units\n(nod, tilt, jaw)', 'pull_unit_nod', (-330, -150)),
        ('mouth paddles', 'paddle_upper', (330, -200)),
        ('arm unit', 'arm_tilt_yoke_l', (380, 60)),
        ('arm unit', 'arm_tilt_yoke_r', (-420, 330)),
        ('arm rod', 'arm_rod_l', (300, -60)),
        ('electronics board', 'electronics_board', (-330, -130)),
        ('speaker', 'speaker_mount', (-350, 90)),
        ('outrigger', 'pipe_outrigger', (430, 200)),
    ])
    render(items + g, 'overview_side', (2000, 0, 0), size=(1800, 1500), zoom=1.2)
    render(assembly.build(26.7, dict(yaw=35, lean_roll=-15, lean_pitch=15, head_yaw=40, head_pitch=-15, head_roll=-15,
                                      jaw=35, tilt_l=-35, ext_l=60, pan_r=-40, tilt_r=30, ext_r=80)),
           'overview_posed', (1000, 1100, 600), size=(1800, 1800), zoom=1.25)
    rest = assembly.build(26.7)
    base = pick(rest, 'tripod_base', 'servo_yaw', 'deck', 'lazy', 'yaw_hub', 'lean_', 'carriage', 'pipe_boom')
    base = [(n, s, c, l, 0.35) if 'deck' in n else (n, s, c, l) for n, s, c, l in base]
    render(base, 'base', (900, 1200, 500), zoom=0.8, auto=True, labels=[
        ('tripod_base', 'tripod_base', (380, 120)), ('fixed plywood deck', 'deck_fixed', (520, 60)),
        ('lazy susan bearing', 'lazy_susan', (-560, 60)), ('yaw_hub', 'yaw_hub', (-520, 160)),
        ('turntable deck', 'deck_turntable', (-560, -40)), ('bracket_L', 'lean_bracket_L', (-480, -60)),
        ('roll_yoke', 'lean_roll_yoke', (430, 30)), ('pitch_yoke', 'lean_pitch_yoke', (-430, -60)),
        ('carriage', 'carriage', (400, -120)), ('boom pipe', 'pipe_boom', (-380, -230))])
    head = pick(assembly.build(26.7, dict(jaw=30)), 'neck_', 'head', 'jaw_lever', 'paddle', 'knuckle_5', 'pipe_entry')
    render(head, 'head', (1300, 800, 350), zoom=0.8, auto=True, labels=[
        ('neck_leg', 'neck_leg', 0), ('knuckle', 'knuckle_5', 0), ('neck_fork\n(4 sheath sockets under)', 'neck_fork', 0),
        ('neck_cross', 'neck_cross', 0), ('neck_top\n(4 lines tie off here)', 'neck_top', 0),
        ('head_frame2', 'head_frame2', 0), ('head twist servo', 'servo_head_twist', 0),
        ('jaw_lever', 'jaw_lever', 0), ('upper paddle\n(fixed)', 'paddle_upper', 0),
        ('lower paddle\n(jaw)', 'paddle_lower', 0), ('entry pipe', 'pipe_entry', 0)])
    render(head, 'head_side', (2000, 0, 0), zoom=0.9)
    pu = pick(rest, 'pull_unit_tilt', 'servo_tilt', 'drum_tilt')
    pu = [it for it in pu if '_l' not in it[0][-2:] and '_r' not in it[0][-2:]]
    render(pu, 'pull_unit', (700, -1300, 900), zoom=0.8, auto=True, labels=[
        ('pull_unit', 'pull_unit_tilt', 0), ('drum', 'drum_tilt', 0), ('servo', 'servo_tilt', 0)])
    arm = [it for it in assembly.build(26.7, dict(ext_r=20)) if it[0].endswith('_r') and 'rod_r' not in it[0]]
    render(arm, 'arm_unit', (900, 1100, 500), zoom=0.8, auto=True, labels=[
        ('knuckle', 'knuckle_arm_r', (330, -160)), ('servo_base\n(pan servo)', 'arm_base_r', (420, 40)),
        ('bracket_L\n(tilt servo)', 'arm_bracket_L_r', (330, 230)), ('tilt_yoke', 'arm_tilt_yoke_r', (-60, 330)),
        ('slide_stage\n(piston servo)', 'arm_slide_stage_r', (-420, 230)), ('pinion', 'arm_pinion_r', (-420, 0)),
        ('rack', 'arm_rack_r', (-380, 60)), ('rack_guide', 'arm_rack_guide_r', (-430, 110)),
        ('rod_cap\n(clamps the arm rod)', 'arm_rod_cap_r', (-330, -30))])
    frm = pick(rest, 'pipe', 'knuckle', 'carriage', 'electronics', 'raspberry', 'driver', 'buck', 'amp', 'speaker',
               'neck_leg', 'arm_base', 'saddle', 'pull_unit', 'drum')
    render(frm, 'frame', (1000, -1100, 600), size=(1800, 1600), zoom=0.8, auto=True, labels=[
        ('boom', 'pipe_boom', (200, 230)), ('mast', 'pipe_mast', (330, -60)),
        ('entry pipe', 'pipe_entry', (-60, -260)), ('outrigger', 'pipe_outrigger', (-200, 260)),
        ('knuckle pair', 'knuckle_2', (380, 120)), ('knuckle pair', 'knuckle_4', (330, -160)),
        ('pipe_saddle x2', 'pipe_saddle_2', (420, 0)), ('speaker_mount', 'speaker_mount', (430, 60)),
        ('carriage', 'carriage', (-60, 300)), ('neck_leg', 'neck_leg', (-380, -60)), ('pull_unit x3', 'pull_unit_jaw', 0),
        ('servo_base', 'arm_base_r', (330, 200)), ('servo_base', 'arm_base_l', (-380, 60)),
        ('electronics board', 'electronics_board', (330, -330))])
    # contact sheet of every printed part, in print orientation
    rows = json.load(open(os.path.join(OUT, '..', '..', 'print', 'parts.json')))
    rows = [r for r in rows if '25.0mm' not in r['file']]
    sheet, labels, x, y, rowh = [], [], 0.0, 0.0, 0.0
    for r in rows:
        rd = vtk.vtkSTLReader()
        rd.SetFileName(os.path.join(OUT, '..', '..', 'print', r['file']))
        rd.Update()
        if x + r['x'] > 620:
            x, y, rowh = 0.0, y - rowh - 55, 0.0
        sheet.append((r['part'], rd.GetOutput(), (x + r['x'] / 2, y - r['y'] / 2, 0)))
        labels.append(('%s  x%d' % (r['part'], r['qty']), (x + r['x'] / 2, y - r['y'] - 16, 0), (0, 0, 0)))
        x += r['x'] + 35
        rowh = max(rowh, r['y'])
    render_sheet(sheet, labels)
