(function () {
  'use strict';
  var cfg = window.RC_CFG || {};
  var root = document.getElementById('recondition-app');
  if (!root) return;

  /* ---------- state ---------- */
  var LS = 'rc_state_v1';
  var DEF = {
    v: 1, u: 0,
    set: { days: 3, machine: 'treadmill', cue: 'full', voice: '', rate: 1.05, vol: 1, units: 'kg', quick: false, beeps: true },
    sessions: [], lastW: {}
  };
  function merge(s) {
    var o = JSON.parse(JSON.stringify(DEF));
    if (!s) return o;
    for (var k in s) if (k !== 'set') o[k] = s[k];
    for (var j in (s.set || {})) o.set[j] = s.set[j];
    return o;
  }
  var state;
  try { state = merge(JSON.parse(localStorage.getItem(LS))); } catch (e) { state = merge(null); }
  var tab = 'today', saveTimer = null;

  function save() {
    state.u = Date.now();
    try { localStorage.setItem(LS, JSON.stringify(state)); } catch (e) {}
    if (!cfg.loggedIn) return;
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function () {
      fetch(cfg.rest, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-WP-Nonce': cfg.nonce }, body: JSON.stringify(state) }).catch(function () {});
    }, 800);
  }
  if (cfg.loggedIn) {
    fetch(cfg.rest, { headers: { 'X-WP-Nonce': cfg.nonce } }).then(function (r) { return r.json(); }).then(function (d) {
      if (d && d.v && d.u > state.u) { state = merge(d); try { localStorage.setItem(LS, JSON.stringify(state)); } catch (e) {} if (!run) render(); }
      else if (state.sessions.length) save();
    }).catch(function () {});
  }

  /* ---------- content ---------- */
  var MACH = {
    treadmill: { name: 'Treadmill', push: 'Walk faster, jog, or raise the incline.', easy: 'Comfortable walk. You can chat in full sentences.' },
    bike: { name: 'Exercise bike', push: 'Add resistance and spin a little faster.', easy: 'Light resistance, easy spin.' },
    cross: { name: 'Cross trainer', push: 'Add resistance and drive the handles.', easy: 'Light resistance, smooth stride.' },
    rower: { name: 'Rower', push: 'Drive hard through the legs.', easy: 'Easy strokes, relaxed shoulders.' }
  };

  var EX = {
    legpress: { id: 'legpress', name: 'Leg press', cue: 'Feet shoulder width. Lower until knees are about ninety degrees. Do not lock out.' },
    chest: { id: 'chest', name: 'Chest press', cue: 'Handles at mid chest. Push out smoothly, shoulders down.' },
    row: { id: 'row', name: 'Seated row', cue: 'Chest tall. Pull elbows back and squeeze your shoulder blades.' },
    curl: { id: 'curl', name: 'Leg curl', cue: 'Pull heels toward you slowly and control the return.' },
    shoulder: { id: 'shoulder', name: 'Shoulder press', cue: 'Press up without shrugging. Keep your ribs down.' },
    crunch: { id: 'crunch', name: 'Ab crunch machine', hi: 1, cue: 'Curl your ribs toward your hips. Exhale as you crunch.' },
    legext: { id: 'legext', name: 'Leg extension', cue: 'Extend smoothly, pause at the top, lower for a slow count of three.' },
    lat: { id: 'lat', name: 'Lat pulldown', cue: 'Pull the bar to your upper chest. Lead with your elbows.' },
    abduct: { id: 'abduct', name: 'Hip abductor', hi: 1, cue: 'Open the pads out with control. Do not swing.' },
    fly: { id: 'fly', name: 'Pec fly', cue: 'Soft elbows. Bring the handles together in a wide arc.' },
    calf: { id: 'calf', name: 'Calf raise', hi: 1, cue: 'Rise onto the balls of your feet, pause, lower slowly.' },
    back: { id: 'back', name: 'Back extension', cue: 'Hinge from the hips and stop when your body is in a straight line.' }
  };
  var DAYS = {
    A: [[EX.legpress, EX.chest], [EX.row, EX.curl], [EX.shoulder, EX.crunch]],
    B: [[EX.legext, EX.lat], [EX.abduct, EX.fly], [EX.calf, EX.back]]
  };

  var STRETCH = [
    { n: 'Standing quad stretch', sides: 1, cue: 'Heel to glute, knees together, chest tall. Hold a rail if you need it.' },
    { n: 'Calf stretch at the wall', sides: 1, cue: 'Back heel down, lean into the wall.' },
    { n: 'Figure four glute stretch', sides: 1, cue: 'Seated. Ankle on the opposite knee, sit back and lean forward.' },
    { n: 'Doorway chest stretch', cue: 'Forearms on the frame, step through gently.' },
    { n: 'Childs pose with reach', cue: 'Hands forward, sink your hips back toward your heels.' }
  ];

  /* Poses face right in a 200 x 120 box. L = limb lines, F = focus spots, B = blocks */
  var POSES = {
    lunge: {
      name: 'Low lunge', tip: 'Back knee down on a mat. Tuck your tailbone and let the hips drift forward until the front of the back hip opens.',
      L: [[[92, 58], [96, 24]], [[92, 58], [132, 62], [134, 100], [147, 100]], [[92, 58], [62, 98], [28, 98]], [[96, 28], [128, 60]]], H: [97, 14], F: [[86, 64]]
    },
    halfsplit: {
      name: 'Half split', tip: 'One leg straight, toes up. Hinge from the hips with a long spine and reach toward the foot. No rounding, no bouncing.',
      L: [[[80, 98], [165, 98], [165, 84]], [[80, 98], [48, 86], [68, 98]], [[80, 98], [118, 68]], [[116, 70], [158, 94]]], H: [127, 59], F: [[125, 98]]
    },
    butterfly: {
      name: 'Butterfly', tip: 'Soles together, heels a hand away from your body. Sit tall, then fold forward from the hips. Let the knees sink on each exhale.',
      L: [[[100, 96], [100, 52]], [[100, 96], [55, 102], [92, 100]], [[100, 96], [145, 102], [108, 100]], [[100, 58], [84, 94]], [[100, 58], [116, 94]]], H: [100, 42], F: [[62, 100], [138, 100]]
    },
    straddle: {
      name: 'Straddle', tip: 'Legs wide, toes up, knees pointing at the ceiling. Walk your hands forward with a long back. Stop where it is a firm stretch, never sharp.',
      L: [[[100, 92], [28, 104]], [[100, 92], [172, 104]], [[100, 92], [100, 66]], [[100, 68], [76, 100]], [[100, 68], [124, 100]]], H: [100, 56], F: [[70, 99], [130, 99]]
    },
    frontsplit: {
      name: 'Front split slide', tip: 'Hands on blocks either side. Slide the front heel forward only as far as you can keep the hips square. Stay light on your hands and breathe.',
      L: [[[100, 76], [166, 98]], [[100, 76], [34, 98]], [[100, 76], [100, 34]], [[100, 40], [110, 88]]], H: [100, 24], F: [[100, 82]], B: [[104, 88, 14, 14]]
    }
  };

  function fig(key, mirror) {
    var p = POSES[key], g = '';
    p.F.forEach(function (f) { g += '<circle class="fc" cx="' + f[0] + '" cy="' + f[1] + '" r="13"/>'; });
    (p.B || []).forEach(function (b) { g += '<rect class="bk" x="' + b[0] + '" y="' + b[1] + '" width="' + b[2] + '" height="' + b[3] + '" rx="2"/>'; });
    p.L.forEach(function (l) { g += '<polyline class="lm" points="' + l.map(function (q) { return q.join(','); }).join(' ') + '"/>'; });
    g += '<circle class="hd" cx="' + p.H[0] + '" cy="' + p.H[1] + '" r="9"/>';
    var t = mirror ? ' transform="translate(200,0) scale(-1,1)"' : '';
    return '<svg class="rc-fig" viewBox="0 0 200 120" role="img" aria-label="' + p.name + '"><line class="gd" x1="8" y1="104" x2="192" y2="104"/><g' + t + '>' + g + '</g></svg>';
  }
  function pose(key, mirror) {
    var ph = cfg.photos && cfg.photos[key];
    return ph ? '<img class="rc-photo" src="' + ph + '" alt="' + POSES[key].name + '">' : fig(key, mirror);
  }

  /* ---------- plan ---------- */
  function doneSessions() { return state.sessions.filter(function (s) { return !s.partial; }); }
  function ctx() {
    var n = doneSessions().length, d = +state.set.days;
    var wk = Math.floor(n / d) + 1;
    return { n: n, wk: wk, w: Math.min(wk, 12), type: n % 2 ? 'B' : 'A', steady: d >= 3 && n % d === d - 1, over: wk > 12 };
  }
  function weightsScheme(w) {
    if (w <= 2) return { sets: 2, reps: 12 };
    if (w <= 4) return { sets: 3, reps: 12 };
    if (w <= 8) return { sets: 3, reps: 10 };
    return { sets: 3, reps: 8 };
  }
  function intervalScheme(w) {
    if (w <= 3) return { r: 5, push: 60, easy: 120, e: 6 };
    if (w <= 6) return { r: 7, push: 60, easy: 90, e: 7 };
    if (w <= 9) return { r: 6, push: 90, easy: 90, e: 7 };
    return { r: 4, push: 180, easy: 120, e: 7 };
  }
  function steadyMins(w) { return [20, 20, 22, 22, 24, 24, 26, 26, 28, 28, 30, 30][w - 1]; }
  function holdSecs(w) { return 40 + 10 * Math.floor((w - 1) / 4); }

  function build(c) {
    var S = state.set, q = S.quick, m = MACH[S.machine], out = [], w = c.w;
    function add(o) { out.push(o); }

    add({ sec: 'Cardio', kind: 'timed', tone: 'easy', title: 'Warm up', sub: m.easy, secs: 180, say: 'Warm up. Easy pace for three minutes.', effort: 3 });
    if (c.steady) {
      var mins = Math.round(steadyMins(w) * (q ? 0.75 : 1)), secs = mins * 60, marks = [{ at: secs / 2, say: 'Halfway.' }];
      if (mins >= 16) marks.push({ at: 300, say: 'Five minutes to go.' });
      add({ sec: 'Cardio', kind: 'timed', tone: 'easy', title: 'Steady effort', sub: 'Short sentences only. Effort 5 out of 10.', secs: secs, say: 'Steady effort for ' + mins + ' minutes.', more: 'You should manage a few words at a time, not a full chat.', effort: 5, marks: marks });
    } else {
      var I = intervalScheme(w), r = q ? Math.max(3, I.r - 1) : I.r;
      for (var i = 1; i <= r; i++) {
        add({ sec: 'Cardio', kind: 'timed', tone: 'push', title: 'Push', sub: m.push, secs: I.push, say: 'Push. Round ' + i + ' of ' + r + '.', more: 'Effort ' + I.e + ' out of ten.', effort: I.e, marks: I.push > 40 ? [{ at: 10, say: 'Ten seconds.', full: 1 }] : [] });
        add({ sec: 'Cardio', kind: 'timed', tone: 'easy', title: 'Ease off', sub: m.easy, secs: I.easy, say: 'Ease off.', more: 'Recover and slow your breathing.', effort: 3 });
      }
    }
    add({ sec: 'Cardio', kind: 'timed', tone: 'easy', title: 'Cool down', sub: m.easy, secs: 120, say: 'Cool down. Easy pace.', effort: 2 });

    var W = weightsScheme(w), pairs = DAYS[c.type].slice(0, q ? 2 : 3), seq = [];
    pairs.forEach(function (pr, pi) {
      for (var s = 1; s <= W.sets; s++) pr.forEach(function (ex, ei) {
        seq.push({ ex: ex, s: s, last: (s === W.sets && ei === pr.length - 1), endPair: pi === pairs.length - 1 });
      });
    });
    seq.forEach(function (it, idx) {
      var reps = W.reps + (it.ex.hi ? 4 : 0);
      add({ sec: 'Weights', kind: 'set', ex: it.ex, set: it.s, sets: W.sets, reps: reps, title: it.ex.name, sub: 'Set ' + it.s + ' of ' + W.sets + ' · ' + reps + ' reps', say: it.ex.name + '. Set ' + it.s + ' of ' + W.sets + '. ' + reps + ' reps.', more: it.s === 1 ? it.ex.cue : '', tip: it.ex.cue });
      var nx = seq[idx + 1];
      if (nx) add({ sec: 'Weights', kind: 'rest', tone: 'easy', secs: it.last ? 60 : 40, title: 'Rest', sub: 'Next: ' + nx.ex.name, say: 'Rest. Next, ' + nx.ex.name + '.', marks: [] });
    });

    var hs = w <= 4 ? 30 : 40;
    STRETCH.forEach(function (st) {
      (st.sides ? ['Left', 'Right'] : ['']).forEach(function (sd) {
        add({ sec: 'Stretch', kind: 'timed', tone: 'easy', title: st.n + (sd ? ' · ' + sd : ''), sub: st.cue, secs: hs, say: st.n + '.' + (sd ? ' ' + sd + ' side.' : ''), more: 'Breathe slowly.', marks: [] });
      });
    });

    var H = holdSecs(w), list = [['lunge', 1], ['halfsplit', 1], ['butterfly', 0], ['straddle', 0]];
    if (w >= 5) list.push(['frontsplit', 1]);
    list.forEach(function (it) {
      var p = POSES[it[0]];
      (it[1] ? ['Left', 'Right'] : ['']).forEach(function (sd) {
        add({ sec: 'Splits', kind: 'timed', tone: 'easy', title: p.name + (sd ? ' · ' + sd : ''), sub: p.tip, secs: H, pose: it[0], mirror: sd === 'Right', say: p.name + '.' + (sd ? ' ' + sd + ' side.' : ''), more: 'Breathe out and sink a little deeper.', marks: [{ at: Math.round(H / 2), say: 'Breathe and sink.', full: 1 }] });
      });
    });

    var seen = {};
    out.forEach(function (s) { if (!seen[s.sec]) { s.first = true; seen[s.sec] = 1; } });
    return out;
  }
  var INTRO = { Weights: 'Weights.', Stretch: 'Stretch time.', Splits: 'Last block. Splits.' };

  function estMins(steps) {
    var t = 0;
    steps.forEach(function (s) { t += s.secs ? s.secs : 40; });
    return Math.round(t / 60);
  }
  function blockSummary(steps) {
    var o = {}, order = [];
    steps.forEach(function (s) { if (!o[s.sec]) { o[s.sec] = 0; order.push(s.sec); } o[s.sec] += s.secs ? s.secs : 40; });
    return order.map(function (k) { return '<span class="rc-chip c-' + k + '">' + k + ' ' + Math.round(o[k] / 60) + 'm</span>'; }).join(' ');
  }

  /* ---------- audio ---------- */
  var ac = null, wake = null;
  function speak(t) {
    if (state.set.cue === 'beeps' || !t || !('speechSynthesis' in window)) return;
    try {
      speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(t);
      u.rate = +state.set.rate; u.volume = +state.set.vol;
      var v = speechSynthesis.getVoices().filter(function (x) { return x.voiceURI === state.set.voice; })[0];
      if (v) { u.voice = v; u.lang = v.lang; }
      speechSynthesis.speak(u);
    } catch (e) {}
  }
  function beep(f, d, g) {
    if (!state.set.beeps) return;
    try {
      ac = ac || new (window.AudioContext || window.webkitAudioContext)();
      if (ac.state === 'suspended') ac.resume();
      var o = ac.createOscillator(), gn = ac.createGain(), t = ac.currentTime;
      o.type = 'sine'; o.frequency.value = f || 880;
      gn.gain.setValueAtTime((g || 0.18) * state.set.vol, t);
      gn.gain.exponentialRampToValueAtTime(0.0001, t + (d || 0.12));
      o.connect(gn); gn.connect(ac.destination); o.start(t); o.stop(t + (d || 0.12) + 0.03);
    } catch (e) {}
  }
  function lockScreen() {
    try { if (navigator.wakeLock) navigator.wakeLock.request('screen').then(function (l) { wake = l; }).catch(function () {}); } catch (e) {}
  }
  function unlock() {
    try { if (wake) { wake.release(); wake = null; } } catch (e) {}
  }
  document.addEventListener('visibilitychange', function () { if (run && !document.hidden) lockScreen(); });

  /* ---------- player ---------- */
  var run = null, ticker = null;
  function fmt(s) { s = Math.max(0, Math.ceil(s)); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }

  function startSession() {
    var c = ctx(), steps = build(c);
    run = { c: c, steps: steps, i: 0, paused: false, t0: Date.now(), logs: [], dlg: null, summary: null };
    beep(660, 0.1); lockScreen();
    try { if ('speechSynthesis' in window) speechSynthesis.speak(new SpeechSynthesisUtterance('')); } catch (e) {}
    enter(); clearInterval(ticker); ticker = setInterval(tick, 200);
  }
  function enter() {
    var st = run.steps[run.i];
    run.remain = (st.secs || 0) * 1000; run.last = performance.now(); run.fired = {}; run.lastBeep = null;
    var intro = st.first && INTRO[st.sec] ? INTRO[st.sec] + ' ' : '';
    var mode = state.set.cue, txt = '';
    if (mode !== 'beeps') txt = intro + st.say + (mode === 'full' && st.more ? ' ' + st.more : '');
    if (st.kind !== 'rest' || run.i > 0) beep(st.tone === 'push' ? 988 : 740, 0.14);
    if (txt) setTimeout(function () { speak(txt); }, 220);
    drawPlayer();
  }
  function tick() {
    if (!run || run.paused || run.summary || run.dlg) { if (run) run.last = performance.now(); return; }
    var st = run.steps[run.i], now = performance.now();
    run.remain -= now - run.last; run.last = now;
    var el = document.getElementById('rc-el');
    if (el) el.textContent = fmt((Date.now() - run.t0) / 1000);
    if (!st.secs) return;
    var sec = Math.ceil(run.remain / 1000), tm = document.getElementById('rc-time');
    if (tm) tm.textContent = fmt(sec);
    if (sec <= 3 && sec >= 1 && run.lastBeep !== sec) { run.lastBeep = sec; beep(sec === 1 ? 1100 : 800, 0.08, 0.12); }
    (st.marks || []).forEach(function (mk, idx) {
      if (!run.fired[idx] && sec <= mk.at && run.remain > 1500) {
        run.fired[idx] = 1;
        if (state.set.cue === 'full' || (state.set.cue === 'min' && !mk.full)) speak(mk.say);
      }
    });
    if (run.remain <= 0) next();
  }
  function next() {
    var st = run.steps[run.i];
    if (st.kind === 'set') logSet(st);
    if (run.i >= run.steps.length - 1) return finish(false);
    run.i++; enter();
  }
  function back() { if (run.i > 0) { run.i--; enter(); } }
  function logSet(st) {
    var w = document.getElementById('rc-w'), r = document.getElementById('rc-r');
    var wv = w && w.value !== '' ? parseFloat(w.value) : null, rv = r ? parseInt(r.value, 10) : st.reps;
    run.logs.push({ ex: st.ex.id, n: st.ex.name, s: st.set, w: wv, r: rv });
    if (wv != null) state.lastW[st.ex.id] = wv;
  }
  function finish(partial) {
    clearInterval(ticker); unlock();
    try { speechSynthesis.cancel(); } catch (e) {}
    var mins = Math.max(1, Math.round((Date.now() - run.t0) / 60000));
    var rec = { d: new Date().toISOString(), n: run.c.n, wk: run.c.wk, type: run.c.type, mins: mins, logs: run.logs, partial: !!partial };
    if (!partial || run.logs.length) { state.sessions.push(rec); save(); }
    if (!partial) {
      beep(660, 0.12); setTimeout(function () { beep(880, 0.12); }, 140); setTimeout(function () { beep(1100, 0.25); }, 280);
      if (state.set.cue !== 'beeps') speak('Session complete. Nice work.');
      run.summary = rec; drawPlayer();
    } else { run = null; closePlayer(); render(); }
  }

  function stepper(id, val, step, label) {
    return '<div><div class="rc-lab">' + label + '</div><div class="rc-step"><button data-a="adj" data-t="' + id + '" data-d="-' + step + '" aria-label="less">&minus;</button>' +
      '<input id="' + id + '" type="number" inputmode="decimal" step="' + step + '" value="' + (val == null ? '' : val) + '"><button data-a="adj" data-t="' + id + '" data-d="' + step + '" aria-label="more">+</button></div></div>';
  }

  function drawPlayer() {
    var host = document.getElementById('rc-play');
    if (!host) { host = document.createElement('div'); host.id = 'rc-play'; host.className = 'rc-play'; document.body.appendChild(host); document.body.style.overflow = 'hidden'; }
    host.innerHTML = '<div class="rc-pin">' + playerInner() + '</div>';
  }
  function closePlayer() {
    var h = document.getElementById('rc-play'); if (h) h.remove();
    document.body.style.overflow = '';
  }
  function playerInner() {
    if (run.summary) {
      var s = run.summary, tot = run.logs.length;
      return '<div class="rc-card" style="text-align:center;margin-top:30px"><h2>Session complete</h2><p class="rc-mut">' + s.mins + ' minutes · ' + tot + ' sets logged</p>' +
        '<p>Week ' + s.wk + ', day ' + s.type + ' done. Next up is day ' + (s.type === 'A' ? 'B' : 'A') + '.</p></div>' +
        '<button class="rc-btn pri big" data-a="close">Done</button>';
    }
    var st = run.steps[run.i], nx = run.steps[run.i + 1], pct = Math.round(run.i / run.steps.length * 100), body = '';
    var top = '<div class="rc-top"><span class="rc-chip c-' + st.sec + '">' + st.sec + '</span><span class="rc-mut rc-sm">Elapsed <b id="rc-el">' + fmt((Date.now() - run.t0) / 1000) + '</b></span><button class="rc-btn ghost" data-a="end">End</button></div>' +
      '<div class="rc-prog"><i style="width:' + pct + '%"></i></div>';
    if (run.dlg) {
      return top + '<div class="rc-dlg"><h3>End this session?</h3><p class="rc-mut">Saving keeps your logged weights. A partial session does not move your plan forward.</p>' +
        '<button class="rc-btn pri" data-a="save-end">Save and finish</button><button class="rc-btn" data-a="discard">Discard</button><button class="rc-btn ghost" data-a="keep">Keep going</button></div>';
    }
    body += '<h2 class="rc-title">' + st.title + '</h2>';
    if (st.kind === 'set') {
      body += '<p class="rc-mut" style="font-size:1.1rem;margin:0">' + st.sub + '</p>';
      body += stepper('rc-w', state.lastW[st.ex.id], state.set.units === 'kg' ? 2.5 : 5, 'Weight (' + state.set.units + ')');
      body += stepper('rc-r', st.reps, 1, 'Reps done');
      body += '<div class="rc-tip">' + st.tip + '</div>';
    } else {
      body += '<div id="rc-time" class="rc-time ' + (st.tone || '') + '">' + fmt(run.remain / 1000) + '</div>';
      if (st.pose) body += pose(st.pose, st.mirror);
      body += '<div class="rc-tip">' + st.sub + '</div>';
    }
    var nxt = nx ? '<div class="rc-next">Next: ' + (nx.kind === 'rest' ? (run.steps[run.i + 2] ? run.steps[run.i + 2].title : '') : nx.title) + '</div>' : '';
    var ctl = '<div class="rc-ctl"><button class="rc-btn" data-a="back">Back</button>';
    if (st.kind === 'set') ctl += '<button class="rc-btn ok" data-a="next">Set done</button>';
    else if (st.kind === 'rest') ctl += '<button class="rc-btn pri" data-a="next">Skip rest</button>';
    else ctl += '<button class="rc-btn" data-a="pause">' + (run.paused ? 'Resume' : 'Pause') + '</button>';
    ctl += '<button class="rc-btn" data-a="' + (st.kind === 'rest' ? 'add15' : 'next') + '">' + (st.kind === 'rest' ? '+15s' : 'Skip') + '</button></div>';
    return top + body + nxt + ctl;
  }

  /* ---------- views ---------- */
  function weekKey(d) { var x = new Date(d); x.setHours(0, 0, 0, 0); x.setDate(x.getDate() - ((x.getDay() + 6) % 7)); return x.getTime(); }

  function viewToday() {
    var c = ctx(), steps = build(c), d = +state.set.days;
    var wkStart = weekKey(Date.now()), thisWeek = doneSessions().filter(function (s) { return weekKey(s.d) === wkStart; }).length;
    var mins = 0; doneSessions().forEach(function (s) { mins += s.mins; });
    var exList = '';
    DAYS[c.type].slice(0, state.set.quick ? 2 : 3).forEach(function (pr) { exList += '<li><span>' + pr[0].name + '</span><span class="rc-mut">+ ' + pr[1].name + '</span></li>'; });
    var W = weightsScheme(c.w);
    var cardioTxt = c.steady ? 'Steady ' + Math.round(steadyMins(c.w) * (state.set.quick ? .75 : 1)) + ' min at a talking pace' : (function () { var I = intervalScheme(c.w); return (state.set.quick ? Math.max(3, I.r - 1) : I.r) + ' rounds of ' + I.push + 's push, ' + I.easy + 's easy'; })();
    return '<div class="rc-card"><div class="rc-row" style="justify-content:space-between"><h2 style="margin:0">Today</h2><span class="rc-chip">Week ' + c.wk + (c.over ? ' · repeating 12' : '') + ' · Day ' + c.type + '</span></div>' +
      '<p class="rc-mut" style="margin:6px 0 10px">About ' + estMins(steps) + ' minutes</p><p>' + blockSummary(steps) + '</p>' +
      '<h4>Cardio</h4><p class="rc-mut">' + MACH[state.set.machine].name + ': ' + cardioTxt + '.</p>' +
      '<h4>Weights · ' + W.sets + ' sets, alternating pairs</h4><ul class="rc-list">' + exList + '</ul>' +
      '<h4 style="margin-top:12px">Finish</h4><p class="rc-mut">Five stretches, then ' + holdSecs(c.w) + ' second splits holds.</p>' +
      '<button class="rc-btn pri big" data-a="start">Start session</button></div>' +
      '<div class="rc-grid"><div class="rc-stat"><b>' + thisWeek + '/' + d + '</b><span class="rc-sm rc-mut">This week</span></div><div class="rc-stat"><b>' + doneSessions().length + '</b><span class="rc-sm rc-mut">Sessions</span></div><div class="rc-stat"><b>' + mins + '</b><span class="rc-sm rc-mut">Minutes</span></div></div>' +
      '<p class="rc-sm rc-mut" style="margin-top:14px">Start every weight light. Pick a load you could move 15 times. When you finish every set at the top of the rep range, add a small step next time. If you get chest pain, dizziness or odd breathlessness, stop. After a year off it is worth a quick check with your doctor first.</p>';
  }

  function viewPlan() {
    var c = ctx(), rows = '';
    for (var w = 1; w <= 12; w++) {
      var I = intervalScheme(w), W = weightsScheme(w);
      rows += '<div class="rc-wk' + (w === c.w ? ' cur' : '') + '"><div class="n">' + w + '</div><div class="rc-sm"><b>Cardio</b> ' + I.r + ' x ' + I.push + 's push / ' + I.easy + 's easy, plus one steady ' + steadyMins(w) + ' min.<br><b>Weights</b> ' + W.sets + ' x ' + W.reps + '. <b>Splits</b> ' + holdSecs(w) + 's holds' + (w >= 5 ? ', front split slide added' : '') + '.</div></div>';
    }
    var figs = '';
    for (var k in POSES) figs += '<div class="rc-card" style="margin:0;padding:10px">' + fig(k) + '<h4 style="margin-top:8px">' + POSES[k].name + '</h4><p class="rc-sm rc-mut" style="margin:0">' + POSES[k].tip + '</p></div>';
    return '<div class="rc-card"><h2>12 week plan</h2><p class="rc-mut rc-sm">The plan moves on when you complete sessions, not on the calendar, so a missed week costs nothing. Days alternate A and B. The last session of each week is steady cardio.</p>' + rows + '</div>' +
      '<h3>Splits library</h3><p class="rc-mut rc-sm">The orange circle marks where you should feel it. Warm muscles only, never bounce, and keep discomfort around 6 out of 10.</p><div class="rc-figs">' + figs + '</div>';
  }

  function viewProgress() {
    var bars = '', now = weekKey(Date.now()), max = 1, counts = [];
    for (var i = 7; i >= 0; i--) {
      var k = now - i * 7 * 864e5, n = doneSessions().filter(function (s) { return Math.abs(weekKey(s.d) - k) < 36e5 * 3; }).length;
      counts.push([k, n]); if (n > max) max = n;
    }
    counts.forEach(function (c) { var dt = new Date(c[0]); bars += '<div style="height:' + Math.max(3, c[1] / max * 100) + '%" title="' + c[1] + ' sessions"><span>' + (dt.getDate() + '/' + (dt.getMonth() + 1)) + '</span></div>'; });
    var byEx = {};
    state.sessions.forEach(function (s) { (s.logs || []).forEach(function (l) { if (l.w == null) return; var e = byEx[l.ex] = byEx[l.ex] || { n: l.n, first: l.w, last: l.w, best: l.w }; e.last = l.w; if (l.w > e.best) e.best = l.w; }); });
    var strength = '';
    for (var id in byEx) { var e = byEx[id]; strength += '<li><span>' + e.n + '</span><span class="rc-mut">' + e.first + ' &rarr; <b style="color:var(--tx)">' + e.last + '</b> ' + state.set.units + ' (best ' + e.best + ')</span></li>'; }
    var hist = state.sessions.slice().reverse().slice(0, 12).map(function (s) {
      var dt = new Date(s.d);
      return '<li><span>' + dt.toLocaleDateString(undefined, { day: 'numeric', month: 'short' }) + ' · Week ' + s.wk + ' day ' + s.type + (s.partial ? ' (partial)' : '') + '</span><span class="rc-mut">' + s.mins + ' min</span></li>';
    }).join('');
    return '<div class="rc-card"><h3>Sessions per week</h3><div class="rc-bars-wrap"><div class="rc-bars">' + bars + '</div></div></div>' +
      '<div class="rc-card"><h3>Strength</h3>' + (strength ? '<ul class="rc-list">' + strength + '</ul>' : '<p class="rc-mut">Log weights during sets and your first, latest and best loads show here.</p>') + '</div>' +
      '<div class="rc-card"><h3>Recent sessions</h3>' + (hist ? '<ul class="rc-list">' + hist + '</ul>' : '<p class="rc-mut">Nothing yet.</p>') + '</div>';
  }

  function opts(map, cur) { var o = ''; for (var k in map) o += '<option value="' + k + '"' + (k === cur ? ' selected' : '') + '>' + map[k] + '</option>'; return o; }
  function viewSettings() {
    var S = state.set, mach = {}; for (var k in MACH) mach[k] = MACH[k].name;
    var voices = ('speechSynthesis' in window) ? speechSynthesis.getVoices() : [], vo = '<option value="">Device default</option>';
    voices.forEach(function (v) { vo += '<option value="' + v.voiceURI + '"' + (v.voiceURI === S.voice ? ' selected' : '') + '>' + v.name + ' (' + v.lang + ')</option>'; });
    function f(label, ctrl, hint) { return '<div class="rc-field"><div>' + label + (hint ? '<div class="rc-sm rc-mut">' + hint + '</div>' : '') + '</div>' + ctrl + '</div>'; }
    return '<div class="rc-card"><h3>Training</h3>' +
      f('Days per week', '<select data-s="days">' + opts({ 2: '2', 3: '3', 4: '4' }, String(S.days)) + '</select>') +
      f('Cardio machine', '<select data-s="machine">' + opts(mach, S.machine) + '</select>') +
      f('Time saver', '<input type="checkbox" data-s="quick"' + (S.quick ? ' checked' : '') + '>', 'One fewer weights pair and shorter cardio') +
      f('Units', '<select data-s="units">' + opts({ kg: 'kg', lb: 'lb' }, S.units) + '</select>') + '</div>' +
      '<div class="rc-card"><h3>Audio cues</h3>' +
      f('Voice style', '<select data-s="cue">' + opts({ full: 'Full coaching', min: 'Short cues only', beeps: 'Beeps only' }, S.cue) + '</select>', 'Short cues keep your podcast easy to follow') +
      f('Voice', '<select data-s="voice">' + vo + '</select>') +
      f('Speed', '<input type="number" step="0.05" min="0.7" max="1.5" data-s="rate" value="' + S.rate + '">') +
      f('Volume', '<input type="number" step="0.1" min="0.1" max="1" data-s="vol" value="' + S.vol + '">', 'Set your podcast a little lower than usual') +
      f('Beeps', '<input type="checkbox" data-s="beeps"' + (S.beeps ? ' checked' : '') + '>', '3 2 1 countdown and change tones') +
      '<div style="margin-top:10px"><button class="rc-btn" data-a="testvoice">Test cues</button></div></div>' +
      '<div class="rc-card"><h3>Data</h3><p class="rc-sm rc-mut">' + (cfg.loggedIn ? 'Saved to your account and this device.' : 'Saved on this device. Log in to the site to sync across devices.') + '</p>' +
      '<div class="rc-row"><button class="rc-btn" data-a="export">Download backup</button><button class="rc-btn ghost" data-a="reset">Reset everything</button></div></div>';
  }

  function render() {
    if (run) return;
    var tabs = { today: 'Today', plan: 'Plan', progress: 'Progress', settings: 'Settings' }, h = '<div class="rc-tabs">';
    for (var k in tabs) h += '<button class="rc-tab' + (k === tab ? ' on' : '') + '" data-a="tab" data-t="' + k + '">' + tabs[k] + '</button>';
    h += '</div>';
    h += ({ today: viewToday, plan: viewPlan, progress: viewProgress, settings: viewSettings })[tab]();
    root.innerHTML = h;
  }

  /* ---------- events ---------- */
  function onClick(e) {
    var b = e.target.closest('[data-a]'); if (!b) return;
    var a = b.getAttribute('data-a');
    if (a === 'tab') { tab = b.getAttribute('data-t'); render(); }
    else if (a === 'start') startSession();
    else if (a === 'adj') {
      var i = document.getElementById(b.getAttribute('data-t')), v = parseFloat(i.value || 0) + parseFloat(b.getAttribute('data-d'));
      i.value = Math.max(0, Math.round(v * 100) / 100);
    }
    else if (!run) {
      if (a === 'testvoice') { beep(880, 0.12); setTimeout(function () { speak('Push. Round two of five. Effort six out of ten.'); }, 200); }
      else if (a === 'export') {
        var l = document.createElement('a'); l.href = URL.createObjectURL(new Blob([JSON.stringify(state, null, 1)], { type: 'application/json' })); l.download = 'recondition-backup.json'; l.click();
      }
      else if (a === 'reset' && confirm('Delete all sessions and settings?')) { state = merge(null); save(); render(); }
    }
    else if (a === 'next') next();
    else if (a === 'back') back();
    else if (a === 'pause') { run.paused = !run.paused; if (run.paused) { try { speechSynthesis.cancel(); } catch (x) {} } run.last = performance.now(); drawPlayer(); }
    else if (a === 'add15') { run.remain += 15000; }
    else if (a === 'end') { run.dlg = true; drawPlayer(); }
    else if (a === 'keep') { run.dlg = null; run.last = performance.now(); drawPlayer(); }
    else if (a === 'save-end') { run.dlg = null; finish(true); }
    else if (a === 'discard') { clearInterval(ticker); unlock(); try { speechSynthesis.cancel(); } catch (x) {} run = null; closePlayer(); render(); }
    else if (a === 'close') { run = null; closePlayer(); tab = 'today'; render(); }
  }
  document.addEventListener('click', function (e) {
    var pl = document.getElementById('rc-play');
    if (root.contains(e.target) || (pl && pl.contains(e.target))) onClick(e);
  });
  root.addEventListener('change', function (e) {
    var k = e.target.getAttribute('data-s'); if (!k) return;
    var v = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    if (['days', 'rate', 'vol'].indexOf(k) > -1) v = parseFloat(v);
    state.set[k] = v; save(); render();
  });
  if ('speechSynthesis' in window) speechSynthesis.onvoiceschanged = function () { if (tab === 'settings' && !run) render(); };

  render();
})();
