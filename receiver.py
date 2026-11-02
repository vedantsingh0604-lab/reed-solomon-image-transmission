import argparse, os, socket, struct
from PIL import Image, ImageDraw, ImageFont
from rs_codec import *

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=5001)
ap.add_argument("--no-pause", action="store_true", help="don't wait for Enter between stages")
a = ap.parse_args()
os.makedirs("output", exist_ok=True)

SCALE = 2       # enlarge images so noise is visible on a projector


def recv_exact(conn, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = conn.recv(min(65536, n - len(buf)))
        if not chunk:
            raise ConnectionError("connection closed early")
        buf += chunk
    return bytes(buf)


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:                       # very old Pillow
        return ImageFont.load_default()


def labelled(img, text):
    big = img.resize((img.width * SCALE, img.height * SCALE), Image.Resampling.NEAREST)
    canvas = Image.new("RGB", (big.width, big.height + 40), (20, 20, 20))
    canvas.paste(big, (0, 40))
    ImageDraw.Draw(canvas).text((10, 8), text, fill="white", font=font(20))
    return canvas


def side_by_side(panels):
    w = sum(p.width for p in panels) + 10 * (len(panels) + 1)
    h = max(p.height for p in panels) + 20
    canvas = Image.new("RGB", (w, h), (20, 20, 20))
    x = 10
    for p in panels:
        canvas.paste(p, (x, 10))
        x += p.width + 10
    return canvas


def count_wrong(x, y):
    return sum(p != q for p, q in zip(x, y))


def pause(msg):
    if not a.no_pause:
        try:
            input(msg)
        except EOFError:                    # stdin closed: just carry on
            pass


def handle(conn):
    mode, w, h, payload_len, raw_len = struct.unpack(HEADER_FMT, recv_exact(conn, HEADER_SIZE))
    payload = recv_exact(conn, payload_len)
    name = MODE_NAMES[mode]
    il = (mode == MODE_RS_IL)
    print(f"\nReceived mode={name} | {w}x{h} | {payload_len:,} B")

    original, orig_bytes = None, None
    if os.path.exists("output/original.png"):
        original = Image.open("output/original.png").convert("RGB")
        orig_bytes = original.tobytes()

    # ---------- Stage 1: the original image ----------
    panels = []
    if original:
        p1 = labelled(original, "1. Original image (sent)")
        panels.append(p1)
        p1.show()
        pause("\n[Stage 1] Original image. Press Enter to send it through the NOISY CHANNEL... ")

    # ---------- Stage 2: what comes out of the noisy channel ----------
    noisy_bytes = payload if mode == MODE_RAW else rs_extract_data(payload, raw_len, il)
    noisy_img = Image.frombytes("RGB", (w, h), noisy_bytes)
    p2 = labelled(noisy_img, "2. After noisy channel (damaged, not yet repaired)")
    panels.append(p2)
    p2.show()
    if orig_bytes:
        bad = count_wrong(orig_bytes, noisy_bytes)
        print(f"[Stage 2] Noisy channel output: {bad:,} / {len(orig_bytes):,} pixel bytes wrong ({bad/len(orig_bytes):.2%})")

    if mode == MODE_RAW:
        print("(raw mode: no Reed-Solomon, so there is nothing to repair)")
        side_by_side(panels).save(f"output/pipeline_{name}.png")
        return

    pause("\n[Stage 2] Damaged image. Press Enter to apply REED-SOLOMON DECODING... ")

    # ---------- Stage 3: Reed-Solomon repair ----------
    data, stats = rs_decode(payload, raw_len, il)
    repaired = Image.frombytes("RGB", (w, h), data)
    p3 = labelled(repaired, "3. After Reed-Solomon repair")
    panels.append(p3)
    p3.show()
    print(f"[Stage 3] Codewords: {stats['codewords']} | corrected: {stats['corrected']} | "
          f"failed: {stats['failed']} | byte errors fixed: {stats['byte_errors_fixed']:,}")
    if orig_bytes:
        bad = count_wrong(orig_bytes, data)
        print(f"[Stage 3] Pixel bytes wrong vs original: {bad:,} / {len(orig_bytes):,} ({bad/len(orig_bytes):.2%})")

    repaired.save(f"output/received_{name}.png")
    side_by_side(panels).save(f"output/pipeline_{name}.png")
    print(f"Saved output/pipeline_{name}.png (all stages side by side)")


with socket.socket() as srv:
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", a.port))
    srv.listen(1)
    print(f"Receiver listening on port {a.port} (Ctrl+C to stop)")
    while True:
        conn, _ = srv.accept()
        with conn:
            try:
                handle(conn)
            except Exception as e:          # keep the receiver alive for the next run
                print(f"Error while handling this transfer: {e!r}")
