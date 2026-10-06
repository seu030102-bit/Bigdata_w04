# Task 2 · where exact stops fitting (this machine)

**Machine:** AMD Ryzen 7 6800H, 16 GB RAM, Windows 11, Python 3.14.2.
Cursor and a browser were open. Nothing else heavy.

`distinct_ratio=0.4`. Exact holds every distinct string in a `set`. FM keeps 32 hash maxima.

## A3 · memory against n

| n | distinct | exact time | exact peak | FM time | FM peak | FM ratio |
|---:|---:|---:|---:|---:|---:|---:|
| 100,000 | 36,702 | 0.33 s | 3.9 MB | 5.13 s | 692 B | 1.27× |
| 400,000 | 146,970 | 2.40 s | 11.6 MB | 27.70 s | 692 B | 1.94× |
| 1,600,000 | 587,625 | 9.82 s | 46.6 MB | 112.19 s | 692 B | 2.83× |
| 6,400,000 | 2,349,909 | 37.17 s | 188.3 MB | 332.55 s | 692 B | 2.61× |
| 25,000,000 | 9,179,304 | 87.10 s | 744.8 MB | — | — | — |

Five sizes, 250× range (100k → 25M). FM was not re-run at 25M: at 6.4M it already cost 5.5 minutes of hashing, and the question at that size is the exact set.

## A2 · where exact became unbearable

**n = 25,000,000. Time ran out first** (87 s, over a minute). Peak RAM was 745 MB of 16 GB — uncomfortable, not an OOM. I stopped there.

## A4 · growth rates

Exact memory when n ×4: 3.9 → 11.6 → 46.6 → 188.3 MB, ratios **2.97×, 4.02×, 4.04×**. Then 6.4M → 25M (×3.91) → 744.8 MB (**3.96×**). So exact memory is **linear in n** (about 80 bytes per distinct key, or 30 bytes per stream item).

FM retained memory is **692 bytes at every n** we measured. Growth rate **0**. It is set by the 32 hash counters, not by the stream.

## A5 · FM accuracy vs n

Ratios: 1.27×, 1.94×, 2.83×, 2.61×. It does **not** get better as n grows. One stream even left the factor-of-two band. That is the method, not a bug: `2^R` is a coarse estimator, and HyperLogLog exists because of it.

## A6 · machine

AMD Ryzen 7 6800H, 16 GB, Windows 11, Python 3.14.2. Cursor + browser.
