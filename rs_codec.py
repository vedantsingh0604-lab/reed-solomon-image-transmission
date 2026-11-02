import struct
from reedsolo import RSCodec, ReedSolomonError

NSYM = 32               # parity bytes per codeword -> corrects up to 16 byte errors
N = 255                 # codeword length
K = N - NSYM            # 223 data bytes per codeword
rsc = RSCodec(NSYM)

# Wire header: mode, width, height, payload_len, raw_len
HEADER_FMT = ">BHHII"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
MODE_RAW, MODE_RS, MODE_RS_IL = 0, 1, 2
MODE_NAMES = {MODE_RAW: "raw", MODE_RS: "rs", MODE_RS_IL: "rs-il"}


def rs_encode(data, interleave):
    data = data + bytes(-len(data) % K)                      # pad to multiple of K
    words = [bytes(rsc.encode(data[i:i + K])) for i in range(0, len(data), K)]
    if interleave:   # transmit column by column
        return b"".join(bytes(w[j] for w in words) for j in range(N))
    return b"".join(words)


def _split_words(coded, interleave):
    """Undo interleaving (if used) and return the list of 255-byte codewords."""
    n_words = len(coded) // N
    if interleave:
        return [bytes(coded[j * n_words + i] for j in range(N)) for i in range(n_words)]
    return [coded[i * N:(i + 1) * N] for i in range(n_words)]


def rs_extract_data(coded, raw_len, interleave):
    """Data bytes of every codeword WITHOUT any error correction.
    This is what the image looks like coming out of the noisy channel, before RS decoding."""
    words = _split_words(coded, interleave)
    return b"".join(w[:K] for w in words)[:raw_len]


def rs_decode(coded, raw_len, interleave):
    words = _split_words(coded, interleave)
    out = bytearray()
    stats = {"codewords": len(words), "corrected": 0, "failed": 0, "byte_errors_fixed": 0}
    for w in words:
        try:
            res = rsc.decode(w)
            msg, errata = (res[0], res[2]) if isinstance(res, tuple) else (res, [])
            out += msg
            if len(errata):
                stats["corrected"] += 1
                stats["byte_errors_fixed"] += len(errata)
        except ReedSolomonError:      # too many errors in this codeword
            out += w[:K]              # keep the damaged data and move on
            stats["failed"] += 1
    return bytes(out[:raw_len]), stats
