#!/usr/bin/env python3
"""Week 4 · Task 1 — Answer questions about a stream you cannot store.

Textbook §4.3 (sampling), §4.4 (Bloom filter), §4.5 (Flajolet-Martin).

The premise of the whole chapter: the stream is longer than your memory, it
goes past once, and you still have to answer. Every method here trades an exact
answer for a bounded amount of space, and the job is to know exactly what you
traded.

You build three, and the harness checks each against the truth it is
approximating.

    python3 task1_sketches.py --verify
"""
import argparse, hashlib, math, random


def _item_bytes(item):
    if isinstance(item, bytes):
        return item
    if isinstance(item, str):
        return item.encode()
    return str(item).encode()


def _trailing_zeros(h):
    if h == 0:
        return 64
    return (h & -h).bit_length() - 1


class BloomFilter:
    """Membership, with one-sided error.

    A Bloom filter never says "no" about something you inserted. It sometimes
    says "yes" about something you did not. That asymmetry is the entire design
    and it is why it is useful for "have I seen this before" and useless for
    "is this definitely in the set".

    `m` bits, `k` hash functions.
    """

    def __init__(self, m, k, seed=246):
        self.m = m
        self.k = k
        self.seed = seed
        self.bits = bytearray((m + 7) // 8)

    def _indexes(self, item):
        raw = hashlib.blake2b(
            _item_bytes(item), digest_size=16,
            key=str(self.seed).encode()
        ).digest()
        h1 = int.from_bytes(raw[:8], "little")
        h2 = int.from_bytes(raw[8:], "little") or 1
        m = self.m
        for i in range(self.k):
            yield (h1 + i * h2) % m

    def add(self, item):
        bits = self.bits
        for idx in self._indexes(item):
            bits[idx >> 3] |= 1 << (idx & 7)

    def __contains__(self, item):
        bits = self.bits
        for idx in self._indexes(item):
            if not (bits[idx >> 3] >> (idx & 7)) & 1:
                return False
        return True

    def expected_fp_rate(self, n_inserted):
        """The textbook's predicted false-positive rate after n insertions.

        §4.4.2: (1 - exp(-k n / m))^k
        """
        if self.m <= 0:
            return 1.0
        return (1.0 - math.exp(-self.k * n_inserted / self.m)) ** self.k


def _splitmix64(x):
    mask = 0xFFFFFFFFFFFFFFFF
    x = (x + 0x9E3779B97F4A7C15) & mask
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & mask
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & mask
    return x ^ (x >> 31)


def flajolet_martin(stream, n_hashes=32, seed=246):
    """Estimate how many DISTINCT items went past, in almost no memory.

    Combines hashes the §4.5.3 way: mean of 2^R inside small groups, then
    the median of those group means. A plain average of 2^R is wrecked by
    one lucky hash; a plain median can only be a power of two.
    """
    max_r = [0] * n_hashes
    seed64 = _splitmix64(seed & 0xFFFFFFFFFFFFFFFF)
    fnv = 0x100000001B3
    for item in stream:
        data = _item_bytes(item)
        base = seed64 ^ (len(data) * 0x9E3779B97F4A7C15)
        for b in data:
            base = ((base ^ b) * fnv) & 0xFFFFFFFFFFFFFFFF
        x = base
        for i in range(n_hashes):
            x = _splitmix64(x + i)
            tz = _trailing_zeros(x)
            if tz > max_r[i]:
                max_r[i] = tz

    estimates = [2.0 ** r for r in max_r]
    group = 4
    means = []
    for g in range(0, n_hashes, group):
        chunk = estimates[g:g + group]
        means.append(sum(chunk) / len(chunk))
    means.sort()
    mid = len(means) // 2
    if len(means) % 2:
        est = float(means[mid])
    else:
        est = (means[mid - 1] + means[mid]) / 2.0
    # Averaging 2^R is biased high; φ ≈ 0.77351 is the usual correction.
    return est * 0.77351


def reservoir_sample(stream, k, seed=246):
    """Keep k items uniformly at random from a stream of unknown length.

    Algorithm R: after seeing i+1 items, the newest one replaces a random
    slot with probability k/(i+1). That is where uniformity happens without
    ever knowing n in advance. The reservoir never holds more than k items.
    """
    rng = random.Random(seed)
    sample = []
    for i, item in enumerate(stream):
        if i < k:
            sample.append(item)
        else:
            j = rng.randint(0, i)
            if j < k:
                sample[j] = item
    return sample


# ------------------------------------------------------------------- harness
def verify():
    fails = 0
    rng = random.Random(246)

    def check(label, ok, detail=""):
        nonlocal fails
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<46} {detail}")
        fails += not ok

    # --- Bloom: no false negatives, ever
    try:
        bf = BloomFilter(m=8192, k=5)
    except NotImplementedError:
        print("  BloomFilter is still a stub"); return 1
    inserted = [f"item-{i}" for i in range(800)]
    for x in inserted:
        bf.add(x)
    check("no false negatives", all(x in bf for x in inserted))

    absent = [f"other-{i}" for i in range(20_000)]
    fp = sum(1 for x in absent if x in bf) / len(absent)
    predicted = bf.expected_fp_rate(len(inserted))
    close = abs(fp - predicted) < max(0.02, predicted * 0.5)
    check("measured false-positive rate matches theory", close,
          f"measured {fp:.3%}, predicted {predicted:.3%}")

    # --- Flajolet-Martin: a factor of two is what this method gives you
    try:
        distinct = 20_000
        stream = [f"k{rng.randrange(distinct)}" for _ in range(120_000)]
        est = flajolet_martin(stream)
    except NotImplementedError:
        print("  flajolet_martin is still a stub"); return 1
    true_distinct = len(set(stream))
    ratio = est / true_distinct
    check("distinct estimate within a factor of 2", 0.5 <= ratio <= 2.0,
          f"estimated {est:,.0f}, true {true_distinct:,} ({ratio:.2f}x)")

    # --- Reservoir: uniform over many trials
    try:
        counts = [0] * 20
        trials = 4000
        for t in range(trials):
            s = reservoir_sample(range(20), 5, seed=t)
            for i in s:
                counts[i] += 1
    except NotImplementedError:
        print("  reservoir_sample is still a stub"); return 1
    expected = trials * 5 / 20
    spread = (max(counts) - min(counts)) / expected
    check("reservoir is uniform across items", spread < 0.15,
          f"spread {spread:.1%} around {expected:.0f}")

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
