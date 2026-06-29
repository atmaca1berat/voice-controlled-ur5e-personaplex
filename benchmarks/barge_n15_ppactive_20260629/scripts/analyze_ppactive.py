#!/usr/bin/env python3
# Barge-in n=15 PP-AKTIF: kalici stack loglarini parse edip CSV uretir.
# Kolonlar: trial, stop_to_halt_s, asr_s, controller_final_status,
#           travel_after_stop_rad, pp_cancelled, err8081
# Kullanim: analyze_ppactive.py [JIDX] [JSIGN]
#   JIDX  : onset tespiti icin kullanilacak eklem indeksi (varsayilan 0)
#   JSIGN : move 'a' yonu (+1 veya -1, varsayilan +1)
import re, math, statistics, sys, os

LOG = os.path.expanduser('~/test_logs/ppactive')
JCSV = os.path.join(LOG, 'joint.csv')
RLOG = os.path.join(LOG, 'runlog.txt')
BLOG = os.path.join(LOG, 'bridge.log')
ELOG = os.path.join(LOG, 'executor.log')
OUT  = os.path.join(LOG, 'barge_n15_ppactive.csv')

JIDX  = int(sys.argv[1]) if len(sys.argv) > 1 else 0
JSIGN = int(sys.argv[2]) if len(sys.argv) > 2 else 1

# Kullanici tarafindan HARIC tutulan (superseded/tekrar istenen) attempt numaralari
EXCL_FILE = os.path.expanduser('~/test_logs/ppactive/excluded.txt')
excluded = set()
if os.path.exists(EXCL_FILE):
    for _ln in open(EXCL_FILE):
        _ln = _ln.strip()
        if _ln.isdigit():
            excluded.add(int(_ln))

TS = re.compile(r'\[(\d+\.\d+)\]')

def rd(p):
    return open(p).read().splitlines() if os.path.exists(p) else []

# ---- run log: move/stop pub wall_time (move bytes_b64>100000) ----
pubs = []
for ln in rd(RLOG):
    m = re.search(r'PUBLISHED at wall_time=(\d+\.\d+).*bytes_b64=(\d+)', ln)
    if m:
        pubs.append((float(m.group(1)), int(m.group(2))))
moves = [w for w, b in pubs if b > 100000]
stops = [w for w, b in pubs if b < 100000]

# ---- executor: per move_to trial status/accept/halt/stopintent ----
el = rd(ELOG)
move_idx = [i for i, ln in enumerate(el) if 'Intent: motion.move_to' in ln]
trials = []
for k, mi in enumerate(move_idx):
    end = move_idx[k+1] if k+1 < len(move_idx) else len(el)
    accept = status = halt = stopintent = None
    for j in range(mi, end):
        ln = el[j]
        if accept is None and 'Goal accepted, executing' in ln:
            accept = float(TS.search(ln).group(1))
        if 'Trajectory controller goal preempted' in ln and status is None:
            status = 'CANCELED'; halt = float(TS.search(ln).group(1))
        if 'Goal completed successfully' in ln and status is None and accept is not None:
            status = 'SUCCEEDED'; halt = float(TS.search(ln).group(1))
        if 'Intent: safety.stop' in ln and stopintent is None:
            stopintent = float(TS.search(ln).group(1))
    trials.append(dict(accept=accept, status=status, halt=halt, stopintent=stopintent))

# ---- bridge: trial segmentlerine ayir (Audio chunk = move,stop,move,stop...) ----
bl = rd(BLOG)
recv = [i for i, ln in enumerate(bl) if 'Audio chunk received from Unity' in ln]
# her trial = 2 resepsiyon (move, stop)
n_btrials = len(recv) // 2
basr = []; bppc = []; berr = []; btimeout = []; bmove_recv = []
for k in range(n_btrials):
    seg_start = recv[2*k]
    seg_end = recv[2*k+2] if (2*k+2) < len(recv) else len(bl)
    seg = bl[seg_start:seg_end]
    mr = TS.search(bl[recv[2*k]])
    bmove_recv.append(float(mr.group(1)) if mr else float('nan'))
    # stop'un asr suresi: stop resepsiyonu sonrasi POST ASR -> Published text: Stop
    stop_local = recv[2*k+1] - seg_start
    stop_seg = '\n'.join(seg[stop_local:])
    post = txt = None
    for j in range(stop_local, len(seg)):
        if post is None and 'POST ASR' in seg[j]:
            post = float(TS.search(seg[j]).group(1))
        if 'Published /voice_command/text:' in seg[j] and 'Stop' in seg[j]:
            txt = float(TS.search(seg[j]).group(1)); break
    basr.append((txt - post) if (post and txt) else float('nan'))
    # stop ASR timeout: stop transcribe edilemedi (text yok) veya transcribe hatasi
    btimeout.append((txt is None) or ('transcribe_via_http error' in stop_seg))
    segtext = '\n'.join(seg)
    bppc.append(('Previous PP task cancelled' in segtext) or ('PP cancelled: safety intent detected' in segtext))
    berr.append(('Cannot connect to host' in segtext) or ('PP HTTP error' in segtext) or ('respond_via_http error' in segtext))

# ---- joint csv ----
st = []; pos = []
for ln in rd(JCSV):
    if not ln or not ln[0].isdigit():
        continue
    f = ln.split(',')
    if len(f) < 21:
        continue
    try:
        t = int(f[0]) + int(f[1]) / 1e9
        p = [float(x) for x in f[9:15]]
    except Exception:
        continue
    st.append(t); pos.append(p)
N = len(st)

import bisect
def nearest(simt):
    i = bisect.bisect_left(st, simt)
    if i <= 0: return 0
    if i >= N: return N - 1
    return i if abs(st[i]-simt) < abs(st[i-1]-simt) else i-1

def dvel(i, w=4):  # JIDX ekleminin yonlu hizi (JSIGN ile move 'a' yonu pozitif)
    a = max(0, i-w); b = min(N-1, i+w)
    if b <= a or st[b] <= st[a]: return 0.0
    return JSIGN * (pos[b][JIDX] - pos[a][JIDX]) / (st[b] - st[a])

# move 'a' yukselis burst'leri (go_home ters yonde -> elenir)
onsets = []
i = 1
while i < N:
    if dvel(i) > 0.12:
        s = i
        while s > 0 and dvel(s) > 0.03: s -= 1
        onsets.append(s+1)
        j = i
        while j < N and dvel(j) > 0.03: j += 1
        tend = st[min(j, N-1)]
        while i < N and st[i] < tend + 4: i += 1
    else:
        i += 1

def rise_end(idx):
    j = idx
    while j < N and dvel(j) > 0.03: j += 1
    return min(j, N-1)

# executor move'unu (accept zamani) dogru bridge attempt'i ile ZAMAN-tabanli esle
# (basarisiz attempt'ler -ASR down vb.- executor'a move gondermez ama bridge segmenti birakir;
#  indeks-tabanli esleme kayar, zaman-tabanli esleme saglamdir)
def match_attempt(A):
    if A is None:
        return None
    best = None
    for j in range(len(bmove_recv)):
        mr = bmove_recv[j]
        if not math.isnan(mr) and mr <= A and (A - mr) < 20:
            if best is None or mr > bmove_recv[best]:
                best = j
    return best

# ---- satirlari kur ----
rows = []
ntr = len(trials)
onset_ptr = 0   # her HAREKET EDEN trial bir onset tuketir; dejenere (hareketsiz) trial tuketmez
for k in range(ntr):
    tr = trials[k]
    j = match_attempt(tr.get('accept'))
    if j is None:
        j = k  # fallback
    s2h = (tr['halt'] - stops[j]) if (tr['halt'] and j < len(stops)) else float('nan')
    a = basr[j] if j < len(basr) else float('nan')
    status = tr['status'] or 'UNKNOWN'
    pc = 'yes' if (j < len(bppc) and bppc[j]) else 'no'
    err = 'yes' if (j < len(berr) and berr[j]) else 'no'
    # move yurutme suresi (accept->halt): cok kisa ise robot kipirdamadan iptal = dejenere
    move_exec = (tr['halt'] - tr['accept']) if (tr['halt'] and tr['accept']) else float('nan')
    degenerate = (not math.isnan(move_exec)) and move_exec < 0.5
    # hareket eden trial bir onset tuketir (dejenere = hareketsiz, tuketmez) -> hizalama saglam
    oi = None
    if (not degenerate) and onset_ptr < len(onsets):
        oi = onsets[onset_ptr]; onset_ptr += 1
    travel = float('nan')
    if status == 'CANCELED' and oi is not None and tr['accept']:
        loff = tr['accept'] - st[oi]
        stop_sim = stops[j] - loff if j < len(stops) else None
        if stop_sim is not None:
            si = max(oi, nearest(stop_sim))
            hi = rise_end(si)
            ps = pos[si]; ph = pos[hi]
            travel = math.sqrt(sum((ph[q]-ps[q])**2 for q in range(6)))
    # CANCELED ama hareket yok (dejenere veya onset bulunamadi) -> travel 0 (robot kipirdamadi)
    if status == 'CANCELED' and math.isnan(travel):
        travel = 0.0
    timeout = (j < len(btimeout) and btimeout[j])
    # GECERLILIK: err8081=0 VE CANCELED VE pp_cancelled=yes VE dejenere DEGIL VE timeout DEGIL
    reasons = []
    if err == 'yes': reasons.append('err8081')
    if status != 'CANCELED': reasons.append('status=' + status)
    if timeout: reasons.append('stop_ASR_timeout')
    if degenerate: reasons.append('dejenere')
    if pc != 'yes': reasons.append('pp_cancelled=no')
    valid = (len(reasons) == 0)
    reason = 'GECERLI' if valid else ('GECERSIZ: ' + ', '.join(reasons))
    if (k + 1) in excluded:
        valid = False
        reason = 'HARIC: superseded (tekrar istendi)'
    rows.append((k+1, s2h, a, status, travel, pc, err, degenerate, move_exec, timeout, valid, reason))

def deg(r):
    return 'yes' if r[7] else 'no'

def tofloat(x, p=4):
    return (("%." + str(p) + "f") % x) if not math.isnan(x) else ""

def tona(x, p=4):
    return (("%." + str(p) + "f") % x) if not math.isnan(x) else "NA"

def to(b):
    return 'e' if b else 'h'

# r: 0 trial,1 s2h,2 asr,3 status,4 travel,5 pc,6 err,7 deg,8 move_exec,9 timeout,10 valid,11 reason
# ---- CSV yaz (TUM denemeler, audit; gecerli sutunu dahil) ----
with open(OUT, 'w') as f:
    f.write("attempt,gecerli,sebep,stop_to_halt_s,asr_s,status,travel_after_stop_rad,pp_cancelled,err8081,stop_asr_timeout,degenerate,move_exec_s\n")
    for r in rows:
        f.write("%d,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
            r[0], ('evet' if r[10] else 'hayir'), r[11].replace(',', ';'),
            tofloat(r[1]), tofloat(r[2]), r[3], tofloat(r[4], 5),
            r[5], r[6], to(r[9]), deg(r), tofloat(r[8])))

def stats(name, xs):
    xs = [x for x in xs if not math.isnan(x)]
    n = len(xs)
    if n < 2:
        print("  %s: n=%d %s" % (name, n, ("%.4f" % xs[0]) if n == 1 else "")); return
    m = statistics.mean(xs); sd = statistics.stdev(xs)
    print("  %s: n=%d mean=%.4f SD=%.4f" % (name, n, m, sd))

print("=== parse: executor_trials=%d bridge_trials=%d joint_samples=%d onsets=%d ===" % (ntr, n_btrials, N, len(onsets)))
print("CSV: %s" % OUT)
print("attempt | gecerli | stop_to_halt | asr | status | travel | pp_canc | err8081 | stopASRtimeout | sebep")
for r in rows:
    print("%d | %s | %s | %s | %s | %s | %s | %s | %s | %s" % (
        r[0], ('EVET' if r[10] else 'hayir'),
        tona(r[1]), tona(r[2]), r[3], tona(r[4], 5), r[5], r[6], to(r[9]), r[11]))

# son deneme detayli (mesaj.txt rapor formati)
if rows:
    L = rows[-1]
    print("\n>>> SON DENEME (attempt %d):" % L[0])
    print("    GECERLI mi      : %s" % ('EVET' if L[10] else 'HAYIR'))
    print("    sebep           : %s" % L[11])
    print("    stop_to_halt_s  : %s" % tona(L[1]))
    print("    asr_s           : %s" % tona(L[2]))
    print("    status          : %s" % L[3])
    print("    travel_rad      : %s" % tona(L[4], 5))
    print("    pp_cancelled    : %s" % L[5])
    print("    err8081         : %s" % L[6])
    print("    stop ASR timeout: %s" % to(L[9]))

valid = [r for r in rows if r[10]]
print("\n=== GECERLI trial sayisi = %d / 15 ===" % len(valid))
if valid:
    print("  (gecerli trial'lar uzerinden)")
    stats("stop_to_halt_s", [r[1] for r in valid])
    stats("travel_after_stop_rad", [r[4] for r in valid])
    stats("asr_s", [r[2] for r in valid])
