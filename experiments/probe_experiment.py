"""적재율에 따른 탐색 비용 실험.

    python3 experiments/probe_experiment.py           # 6단계: 분리 연결, 적재율 0.25 ~ 4
    python3 experiments/probe_experiment.py compare   # 과제: 분리 연결 vs 선형 탐사, 0.1 ~ 0.9

테이블 크기 M = 4093 고정, max_load=None(늘리지 않음), 무작위 URL.
- 분리 연결: 비교한 노드 수.   이론  성공 ≈ 1 + α/2,  실패 ≈ α
- 선형 탐사: 살펴본 슬롯 수.   이론  성공 ≈ (1 + 1/(1-α))/2,  실패 ≈ (1 + 1/(1-α)²)/2
"""

import csv
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, HERE)

from hash_table import HashTable  # noqa: E402
from svg_plot import line_chart  # noqa: E402

M = 4093
MISSES = 4000
SEED = 2026
ALNUM = "abcdefghijklmnopqrstuvwxyz0123456789"


def random_url(rng):
    host = "".join(rng.choice(ALNUM) for _ in range(rng.randint(4, 12)))
    path = "".join(rng.choice(ALNUM) for _ in range(rng.randint(3, 20)))
    tld = rng.choice(["com", "net", "org", "kr", "io"])
    return f"https://{host}.{tld}/{path}"


def make_keys(n, misses, rng):
    """서로 다른 URL n개(넣을 것) + misses개(넣지 않을 것)."""
    seen = HashTable()  # 중복 검사도 직접 만든 테이블로
    keys = []
    while len(keys) < n + misses:
        u = random_url(rng)
        if u not in seen:
            seen.put(u, True)
            keys.append(u)
    return keys[:n], keys[n:]


def measure(table_class, keys, misses):
    t = table_class(capacity=M, max_load=None)
    for k in keys:
        t.put(k, 1)
    hit = sum(t.find(k)[2] for k in keys) / len(keys)
    miss = sum(t.find(k)[2] for k in misses) / len(misses)
    return hit, miss


def chain_theory(a):
    return 1 + a / 2, a


def linear_theory(a):
    return (1 + 1 / (1 - a)) / 2, (1 + 1 / (1 - a) ** 2) / 2


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([f"{v:.4f}" if isinstance(v, float) else v for v in r])


def write_md(path, header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        lines.append("| " + " | ".join(f"{v:.3f}" if isinstance(v, float) else str(v) for v in r) + " |")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def step6():
    rng = random.Random(SEED)
    loads = [i / 4 for i in range(1, 17)]  # 0.25 ~ 4.0
    rows = []
    for a in loads:
        keys, misses = make_keys(round(a * M), MISSES, rng)
        hit, miss = measure(HashTable, keys, misses)
        th, tm = chain_theory(a)
        rows.append([a, len(keys), hit, th, miss, tm])
    header = ["load", "n", "hit", "hit_theory", "miss", "miss_theory"]
    write_csv(os.path.join(HERE, "results.csv"), header, rows)
    write_md(os.path.join(HERE, "results.md"), header, rows)
    line_chart(os.path.join(HERE, "results.svg"),
               f"분리 연결: 적재율에 따른 평균 비교 횟수 (M={M})", "적재율 α", "평균 비교 노드 수",
               loads,
               [("성공 (측정)", [r[2] for r in rows], 0, False),
                ("성공 이론 1+α/2", [r[3] for r in rows], 0, True),
                ("실패 (측정)", [r[4] for r in rows], 1, False),
                ("실패 이론 α", [r[5] for r in rows], 1, True)])


def compare():
    from hash_table import LinearProbingHashTable
    rng = random.Random(SEED)
    loads = [i / 10 for i in range(1, 10)]  # 0.1 ~ 0.9
    rows = []
    for a in loads:
        keys, misses = make_keys(round(a * M), MISSES, rng)  # 두 방식에 같은 키
        ch, cm = measure(HashTable, keys, misses)
        lh, lm = measure(LinearProbingHashTable, keys, misses)
        cth, ctm = chain_theory(a)
        lth, ltm = linear_theory(a)
        rows.append([a, len(keys), ch, cth, cm, ctm, lh, lth, lm, ltm])
    header = ["load", "n", "chain_hit", "chain_hit_theory", "chain_miss", "chain_miss_theory",
              "linear_hit", "linear_hit_theory", "linear_miss", "linear_miss_theory"]
    write_csv(os.path.join(HERE, "compare.csv"), header, rows)
    write_md(os.path.join(HERE, "compare.md"), header, rows)
    col = lambda i: [r[i] for r in rows]  # noqa: E731
    line_chart(os.path.join(HERE, "compare_hit.svg"),
               f"성공 탐색: 분리 연결 vs 선형 탐사 (M={M})", "적재율 α", "평균 비교(탐사) 횟수",
               loads,
               [("분리 연결 (측정)", col(2), 0, False), ("분리 연결 이론", col(3), 0, True),
                ("선형 탐사 (측정)", col(6), 1, False), ("선형 탐사 이론", col(7), 1, True)])
    line_chart(os.path.join(HERE, "compare_miss.svg"),
               f"실패 탐색: 분리 연결 vs 선형 탐사 (M={M})", "적재율 α", "평균 비교(탐사) 횟수",
               loads,
               [("분리 연결 (측정)", col(4), 0, False), ("분리 연결 이론", col(5), 0, True),
                ("선형 탐사 (측정)", col(8), 1, False), ("선형 탐사 이론", col(9), 1, True)])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        compare()
    else:
        step6()
