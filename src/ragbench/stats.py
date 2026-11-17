"""Paired comparison statistics for per-query metric differences.

[EN]
- Role: confidence intervals for the mean of per-query differences (system A minus system B).
  Two resampling units are offered:
  - queries (iid): treats the questions as independent draws. Optimistic here, because several
    questions share the same primary evidence document (e.g. de_waelzlager).
  - clusters: resamples whole primary-evidence documents (all questions of a document move
    together), which respects that questions about one document are not independent.
- Both use the same seed convention as the earlier analyses (seed 42, 10000 draws, 95 % percentile
  interval) so the iid numbers reproduce the numbers already published in experiments/results.
- Also: an exact two-sided sign test on the questions that differ (ties dropped).

[KO]
- 역할: 질문별 차이(시스템 A - 시스템 B) 평균의 신뢰구간. 재표집 단위를 둘로 제공한다.
  - 질문(iid): 질문을 독립 표본으로 본다. 여러 질문이 같은 주 근거 문서(예: de_waelzlager)를 공유하므로
    여기서는 낙관적이다.
  - 군집: 주 근거 문서 단위로 재표집한다(한 문서의 모든 질문이 함께 움직임). 한 문서에 대한 질문들이
    독립이 아니라는 점을 반영한다.
- 둘 다 앞선 분석과 같은 규약(시드 42, 10000회, 95% 백분위 구간)이라 iid 결과는 experiments/results에
  이미 실린 숫자와 재현된다.
- 그 밖에 점수가 다른 질문에 대한 정확한 양측 부호 검정(동점 제외).
"""

from __future__ import annotations

import math

import numpy as np


def bootstrap_ci(diff: np.ndarray, clusters: list[str] | None = None, n: int = 10000, seed: int = 42) -> tuple[float, float]:
    """95 % interval of the mean of `diff`; `clusters` (one label per query) switches to cluster resampling."""
    diff = np.asarray(diff, dtype=float)
    rng = np.random.default_rng(seed)
    if clusters is None:
        means = diff[rng.integers(0, len(diff), size=(n, len(diff)))].mean(axis=1)
    else:
        labels = sorted(set(clusters))
        pos = {c: i for i, c in enumerate(labels)}
        sums = np.zeros(len(labels))
        counts = np.zeros(len(labels))
        for d, c in zip(diff, clusters):
            sums[pos[c]] += d
            counts[pos[c]] += 1
        pick = rng.integers(0, len(labels), size=(n, len(labels)))       # 문서 단위로 복원추출
        means = sums[pick].sum(axis=1) / counts[pick].sum(axis=1)         # 뽑힌 문서들의 질문 전체 평균
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def sign_test_p(diff: np.ndarray, eps: float = 1e-9) -> float:
    """Exact two-sided sign test on the non-tied questions (1.0 if everything ties)."""
    d = np.asarray(diff, dtype=float)
    better, worse = int((d > eps).sum()), int((d < -eps).sum())
    n = better + worse
    if n == 0:
        return 1.0
    k = max(better, worse)
    tail = sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def compare(diff: np.ndarray, clusters: list[str] | None = None) -> dict[str, float | int | tuple[float, float]]:
    """Mean difference, iid CI, cluster CI (if clusters given), win/loss/tie counts and the sign-test p."""
    d = np.asarray(diff, dtype=float)
    out: dict = {"mean": float(d.mean()), "ci_iid": bootstrap_ci(d), "better": int((d > 1e-9).sum()),
                 "worse": int((d < -1e-9).sum()), "tie": int((np.abs(d) <= 1e-9).sum()), "sign_p": sign_test_p(d)}
    if clusters is not None:
        out["ci_cluster"] = bootstrap_ci(d, clusters)
        out["n_clusters"] = len(set(clusters))
    return out


def cohen_kappa(a: list, b: list) -> float:
    """Cohen's kappa of two raters over any label set (nan when chance agreement is 1)."""
    if len(a) != len(b) or not a:
        raise ValueError("two non-empty rating lists of the same length are needed")
    n = len(a)
    labels = sorted(set(a) | set(b), key=str)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(lab) / n) * (b.count(lab) / n) for lab in labels)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def corrected_rate(observed_yes: float, sensitivity: float, specificity: float) -> float:
    """Rogan-Gladen estimate of the true YES rate from a judge's YES rate.

    [KO] 판정 모델의 YES 비율을, 사람 기준 dev 세트에서 잰 민감도(사람 YES를 YES로)와 특이도(사람 NO를 NO로)로 보정한다:
    p = (q + spec - 1) / (sens + spec - 1), [0, 1]로 자른다. sens + spec <= 1이면 판정이 우연 이하라 보정할 수 없다(nan).
    """
    j = sensitivity + specificity - 1
    if j <= 0:
        return float("nan")
    return float(min(1.0, max(0.0, (observed_yes + specificity - 1) / j)))


def corrected_rate_ci(judge_yes: np.ndarray, cal_human: np.ndarray, cal_judge: np.ndarray, n: int = 10000,
                      seed: int = 42) -> tuple[float, tuple[float, float]]:
    """Corrected YES rate with a 95 % bootstrap interval that resamples both the judged answers and the calibration set.

    judge_yes: judge verdicts (bool) on the answers being reported; cal_human / cal_judge: human and judge verdicts on
    the calibration (dev) items. Draws whose calibration has sens + spec <= 1 are dropped.
    """
    jy, ch, cj = (np.asarray(x, dtype=bool) for x in (judge_yes, cal_human, cal_judge))

    def est(jy_, ch_, cj_) -> float:
        pos, neg = ch_.sum(), (~ch_).sum()
        if pos == 0 or neg == 0:
            return float("nan")
        return corrected_rate(jy_.mean(), (cj_ & ch_).sum() / pos, (~cj_ & ~ch_).sum() / neg)

    point = est(jy, ch, cj)
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n):
        i = rng.integers(0, len(jy), len(jy))
        k = rng.integers(0, len(ch), len(ch))
        v = est(jy[i], ch[k], cj[k])
        if not math.isnan(v):
            draws.append(v)
    if not draws:
        return point, (float("nan"), float("nan"))
    return point, (float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)))
