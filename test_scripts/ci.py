#!/usr/bin/env python3
import sys, statistics as st, math

xs = [float(a) for a in sys.argv[1:]]
n = len(xs)
m = st.mean(xs)
sd = st.stdev(xs)
t = {10: 2.262, 12: 2.201, 15: 2.145, 20: 2.093, 30: 2.045}.get(n, 2.131)
half = t * sd / math.sqrt(n)
print(f"n={n}  mean={m:.3f}  sd={sd:.3f}  95% CI=[{m-half:.3f}, {m+half:.3f}]  (±{half:.3f})")
