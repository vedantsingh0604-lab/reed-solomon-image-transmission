import os
from rs_codec import rs_encode, rs_decode
from channel import corrupt

data = os.urandom(50_000)
tests = [("random 2%", "random", dict(rate=0.02)),
         ("10 bursts x 100 B", "burst", dict(bursts=10, burst_len=100))]

for name, kind, kw in tests:
    for il in (False, True):
        coded = rs_encode(data, il)
        noisy, _ = corrupt(coded, kind, seed=1, **kw)
        out, st = rs_decode(noisy, len(data), il)
        print(f"{name:18s} interleave={il!s:5s} recovered={out == data!s:5s} {st}")