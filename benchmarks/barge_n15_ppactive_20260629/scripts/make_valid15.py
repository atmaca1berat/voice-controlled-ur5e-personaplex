#!/usr/bin/env python3
# Gecerli 15 trial icin: gecerli_15.csv (yeniden numarali) + bridge/executor log segmentleri.
import re, os, sys

LOG = os.path.expanduser('~/test_logs/ppactive')
CSV = os.path.join(LOG, 'barge_n15_ppactive.csv')
OUTDIR = sys.argv[1]  # hedef klasor (gecerli 15)
TS = re.compile(r'\[(\d+\.\d+)\]')

# 1) CSV'den gecerli attempt numaralari (sirayla)
rows = open(CSV).read().splitlines()
hdr = rows[0]
valid_attempts = []   # ham attempt no (executor move_to index +1)
valid_rows = []
for ln in rows[1:]:
    f = ln.split(',')
    if len(f) < 9:
        continue
    if f[1] == 'evet':
        valid_attempts.append(int(f[0]))
        valid_rows.append(f)

# gecerli_15.csv (yeniden numarali 1..15)
with open(os.path.join(OUTDIR, 'gecerli_15.csv'), 'w') as o:
    o.write("trial,stop_to_halt_s,asr_s,status,travel_after_stop_rad,pp_cancelled,err8081\n")
    for i, f in enumerate(valid_rows, 1):
        # f: attempt,gecerli,sebep,stop_to_halt,asr,status,travel,pp_canc,err8081,...
        o.write("%d,%s,%s,%s,%s,%s,%s\n" % (i, f[3], f[4], f[5], f[6], f[7], f[8]))

# 2) executor: move_to bloklari (go_home -> move -> terminal), sirayla = attempt 1..23
el = open(os.path.join(LOG, 'executor.log')).read().splitlines()
gh_idx = [i for i, l in enumerate(el) if 'Intent: motion.go_home' in l]
mv_idx = [i for i, l in enumerate(el) if 'Intent: motion.move_to' in l]
def exec_block(k):  # k = 1-based attempt no
    mi = mv_idx[k-1]
    gh = max([g for g in gh_idx if g < mi], default=mi)
    nxt = min([g for g in gh_idx if g > mi], default=len(el))
    return el[gh:nxt], el[mi]
def exec_accept(k):
    mi = mv_idx[k-1]
    for j in range(mi, min(mi+8, len(el))):
        if 'Goal accepted, executing' in el[j]:
            m = TS.search(el[j]);  return float(m.group(1)) if m else None
    return None

# 3) bridge: resepsiyon ciftleri; her ciftin move_recv ts'i
bl = open(os.path.join(LOG, 'bridge.log')).read().splitlines()
recv = [i for i, l in enumerate(bl) if 'Audio chunk received from Unity' in l]
pairs = []  # (move_recv_ts, start_idx, end_idx)
for p in range(len(recv)//2):
    s = recv[2*p]
    e = recv[2*p+2] if (2*p+2) < len(recv) else len(bl)
    m = TS.search(bl[s]); mr = float(m.group(1)) if m else None
    pairs.append((mr, s, e))
def bridge_block(accept):
    if accept is None: return None
    best = None
    for (mr, s, e) in pairs:
        if mr is not None and mr <= accept and (accept-mr) < 20:
            if best is None or mr > best[0]: best = (mr, s, e)
    if best is None: return None
    return bl[best[1]:best[2]]

# 4) segment loglari yaz
with open(os.path.join(OUTDIR, 'executor_gecerli15.log'), 'w') as oe, \
     open(os.path.join(OUTDIR, 'bridge_gecerli15.log'), 'w') as ob:
    for i, k in enumerate(valid_attempts, 1):
        eb, _ = exec_block(k)
        acc = exec_accept(k)
        bb = bridge_block(acc)
        oe.write("===== GECERLI TRIAL %d (ham attempt %d) =====\n" % (i, k))
        oe.write('\n'.join(eb) + '\n\n')
        ob.write("===== GECERLI TRIAL %d (ham attempt %d) =====\n" % (i, k))
        ob.write(('\n'.join(bb) if bb else '(bridge segment bulunamadi)') + '\n\n')

print("gecerli attempts:", valid_attempts)
print("yazildi: gecerli_15.csv, executor_gecerli15.log, bridge_gecerli15.log ->", OUTDIR)
