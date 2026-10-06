# Observations · Week 4

## Task 1

A Bloom filter never has a false negative because bits are only ever set, never cleared: if any of the k bits is 0, that item was never inserted. Predicted FP 0.860% vs measured 0.855%. For FM I used §4.5.3 (mean of `2^R` in groups of 4, then median, times φ≈0.77351): on the verify stream that was 1.43×; a raw mean of `2^R` was 8.76× (one lucky hash) and a plain median was 1.64× but stuck on a power of two. Reservoir uniformity happens in the `else` branch: item i is kept with probability `k/(i+1)` without ever knowing n.

블룸 필터에 거짓 음성이 없는 이유는 비트를 켜기만 하고 끄지 않기 때문이다. k개 비트 중 하나라도 0이면 그 원소는 넣은 적이 없다. 예측 FP 0.860%, 실측 0.855%. FM은 §4.5.3대로 그룹 평균 뒤 중앙값에 φ를 곱했고 검증 스트림에서 1.43배였다. `2^R`을 그냥 평균하면 8.76배(운 좋은 해시 하나), 중앙값만 쓰면 1.64배지만 2의 거듭제곱에 묶인다. 리저버가 n을 몰라도 되는 지점은 `else`: i번째 원소를 확률 `k/(i+1)`로 넣는 부분이다.

## Task 2

Exact became unbearable at **n=25,000,000**: 87 s (time first), 745 MB of 16 GB. Exact memory grew linearly (~4× when n ×4; ~80 B per distinct key). FM stayed at **692 bytes** at every n — growth rate 0. FM ratios 1.27×–2.83× did not improve with n. A factor of two is fine for “roughly how many distinct users today” on a dashboard; it is not fine if that count bills someone or decides whether you crossed one million.

정확 답이 버거워진 크기는 **n=25,000,000**, 87초라 **시간이 먼저** 달렸다(16 GB 중 745 MB). 정확 집합 메모리는 n에 선형(~n이 4배면 메모리도 4배, distinct 하나당 ~80 B). FM은 모든 n에서 **692바이트**, 증가율 0. 비율 1.27–2.83배는 n이 커져도 나아지지 않았다. 대시보드의 “오늘 순 이용자 대략 얼마”에는 2배 오차로 충분하고, 그 숫자로 과금하거나 100만 돌파를 판정하면 부족하다.

## Task 3

Changed k from 1 to **k = (m/n) ln 2 ≈ 6.93 → 7** (§4.4.2). Floor at 10 bits/item is `(1-e^{-k n/m})^k ≈ 0.819%`, or `(1/2)^k ≈ 0.781%`. We measured **0.811%** (1,622 / 200,000), at the floor → strong. If n is unknown: guessing too low over-fits k, fills the bits, FP collapses toward 1; guessing too high uses too few hashes and wastes the budget. A scalable / dynamic Bloom (grow a new filter when the fill ratio passes ~1/2) is the usual way out.

바꾼 값은 해시 개수 k. §4.4.2에서 k=(m/n)ln 2 ≈ 6.93 → **7**. 10비트/원소의 하한은 약 **0.82%**이고 실측 **0.811%**로 바닥에 닿았다. n을 모르면 너무 작게 짐작하면 k가 커져 비트가 차고 FP가 1로 가고, 너무 크게 짐작하면 k가 작아져 비트를 낭비한다. 채워지는 비율이 약 1/2를 넘을 때 필터를 하나 더 여는 scalable Bloom이 흔한 대응이다.
