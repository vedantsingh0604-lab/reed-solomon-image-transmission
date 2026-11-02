import argparse, os, socket, struct
from PIL import Image
from rs_codec import *
from channel import corrupt

MAX_SIDE = 256   # lower to 160 if decoding feels slow

ap = argparse.ArgumentParser()
ap.add_argument("image")
ap.add_argument("--mode", choices=["raw", "rs", "rs-il"], default="rs-il")
ap.add_argument("--noise", choices=["random", "burst"], default="random")
ap.add_argument("--rate", type=float, default=0.02)
ap.add_argument("--bursts", type=int, default=12)
ap.add_argument("--burst-len", type=int, default=400)
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--host", default="127.0.0.1")
ap.add_argument("--port", type=int, default=5001)
a = ap.parse_args()

os.makedirs("output", exist_ok=True)
img = Image.open(a.image).convert("RGB")
img.thumbnail((MAX_SIDE, MAX_SIDE))
img.save("output/original.png")
w, h = img.size
raw = img.tobytes()                      # uncompressed pixels -> damage is visible

mode = {"raw": MODE_RAW, "rs": MODE_RS, "rs-il": MODE_RS_IL}[a.mode]
payload = raw if mode == MODE_RAW else rs_encode(raw, interleave=(mode == MODE_RS_IL))

noisy, hits = corrupt(payload, a.noise, a.rate, a.bursts, a.burst_len, a.seed)
header = struct.pack(HEADER_FMT, mode, w, h, len(noisy), len(raw))

print(f"Image {w}x{h} | mode={a.mode} | raw {len(raw):,} B -> sent {len(noisy):,} B "
      f"(overhead {len(noisy)/len(raw)-1:.1%})")
print(f"Channel ({a.noise}) corrupted {hits:,} bytes")

with socket.create_connection((a.host, a.port)) as s:
    s.sendall(header + noisy)
print("Sent.")