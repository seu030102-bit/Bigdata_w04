#!/usr/bin/env python3
"""Week 4 · Task 3 — Same memory, fewer mistakes.

Textbook §4.4 (Bloom filters), §4.5 (counting distinct).

`NaiveFilter` is a membership filter in a fixed number of bits. It works. It
also makes far more mistakes than it has to with the memory it was given, and
it does so for a reason you can find by reading §4.4.2 and doing one derivative.

You get **exactly the same number of bits**. Make fewer mistakes.

    python3 bench.py
    python3 bench.py --yours

The rule that makes this interesting: a false negative is not allowed. Ever.
The whole point of this structure is that "no" means no. A filter that gets a
better score by occasionally forgetting something it was given has not improved
anything, it has broken the contract.
"""
import hashlib


class NaiveFilter:
    """One hash function, and the bits it was given."""

    def __init__(self, n_bits, seed=246):
        self.n_bits = n_bits
        self.seed = seed
        self.bits = bytearray(n_bits)

    def _index(self, item):
        d = hashlib.blake2b(str(item).encode(), digest_size=8,
                            key=str(self.seed).encode()).digest()
        return int.from_bytes(d, "big") % self.n_bits

    def add(self, item):
        self.bits[self._index(item)] = 1

    def __contains__(self, item):
        return bool(self.bits[self._index(item)])

    def memory_bits(self):
        return self.n_bits


class YourFilter:
    """Bloom filter with the k that §4.4.2 says is optimal.

    m/n = 80_000/8_000 = 10, so k* = (m/n) ln 2 ≈ 6.93 → k = 7.
    Floor: (1/2)^k ≈ 0.78%, or (1 - exp(-k n/m))^k ≈ 0.82%.
    """

    # Known insert count from the harness (bench.N_INSERT).
    N_EXPECTED = 8_000

    def __init__(self, n_bits, seed=246):
        import math
        self.n_bits = n_bits
        self.seed = seed
        # k = (m/n) ln 2, rounded to the nearest integer ≥ 1.
        self.k = max(1, round((n_bits / self.N_EXPECTED) * math.log(2)))
        self.bits = bytearray((n_bits + 7) // 8)

    def _indexes(self, item):
        raw = hashlib.blake2b(
            str(item).encode(), digest_size=16,
            key=str(self.seed).encode()
        ).digest()
        h1 = int.from_bytes(raw[:8], "little")
        h2 = int.from_bytes(raw[8:], "little") or 1
        m = self.n_bits
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

    def memory_bits(self):
        return self.n_bits
