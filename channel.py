import random


def corrupt(data, kind, rate=0.0, bursts=0, burst_len=0, seed=None):
    """Return (corrupted_bytes, number_of_bytes_hit). Every hit byte really changes."""
    rng = random.Random(seed)
    buf = bytearray(data)
    n = len(buf)
    hits = 0
    if kind == "random":                       # independent byte errors
        hits = int(n * rate)
        for i in rng.sample(range(n), hits):
            buf[i] ^= rng.randint(1, 255)
    elif kind == "burst":                      # runs of consecutive bad bytes
        burst_len = min(burst_len, n)
        for _ in range(bursts):
            s = rng.randrange(0, n - burst_len + 1)
            for i in range(s, s + burst_len):
                buf[i] ^= rng.randint(1, 255)
            hits += burst_len
    return bytes(buf), hits