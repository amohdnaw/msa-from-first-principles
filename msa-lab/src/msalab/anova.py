"""LEVEL 3 - Gage R&R by ANOVA.

Level 2 split the gauge into repeatability and reproducibility and then admitted
what it had assumed: that each operator's offset is the same on every part. That
assumption has a name when it fails - the part-by-operator interaction - and the
older arithmetic has no term for it.

Two methods, one study of sixty numbers:

    average-and-range   ranges, and a table of constants
    ANOVA               sums of squares, and four terms instead of three

Five claims, computed here and nowhere else:

1. On a well-behaved study the two agree closely. That is why the older method
   survived in the plants for decades, and it is the honest starting point.
2. They stop agreeing when operators disagree *about particular parts*.
   Average-and-range has no term for that, so it does not misplace the
   interaction - it omits it, and the gauge comes out looking BETTER than it is.
3. An interaction is a difference of differences, so it needs every cell filled
   and more than one trial. Without replication it is not merely imprecise, it
   is unidentifiable.
4. The sums of squares add up exactly: part, operator, interaction, repeat, and
   nothing left over. That identity is what makes the decomposition a fact
   rather than a convention.
5. The interaction is tested, and AIAG pools it into repeatability when the test
   is not significant. That pooling is a decision with a cost, and the cost is
   computable.

    PYTHONPATH=src .venv/bin/python -m msalab.anova
"""
from __future__ import annotations

import functools
import math

import numpy as np
from scipy import stats

from msalab.measurement import PART_SIGMA, c4

# ---------------------------------------------------------------- the study
PARTS = 10
OPERATORS = 3
TRIALS = 3
SEED = 303

#: The gauge Level 2 finished with, plus the term Level 2 had no room for.
SIGMA_REPEAT = 1.0
SIGMA_OPERATOR = 1.8
#: The interaction: operator j reads part i differently from how they read the
#: others. Zero in the well-behaved study, real in the second one.
SIGMA_INTERACTION = 0.0
#: The instance claim 2 argues from. Chosen so the interaction is comparable to
#: the operator term - which is the case that actually turns up when a fixture
#: locates some parts badly.
BAD_INTERACTION = 1.9

#: AIAG's rule: pool the interaction into repeatability when its test is not
#: significant at this level. It is 0.25 rather than 0.05 on purpose - the test
#: has few degrees of freedom, so a strict alpha would pool almost always.
POOL_ALPHA = 0.25


def study(seed: int = SEED, parts: int = PARTS, operators: int = OPERATORS,
          trials: int = TRIALS, part_sigma: float = PART_SIGMA,
          repeat: float = SIGMA_REPEAT, operator: float = SIGMA_OPERATOR,
          interaction: float = SIGMA_INTERACTION) -> dict:
    """One crossed study: every operator measures every part, `trials` times.

    Crossed rather than nested, because an interaction only exists if the same
    parts are seen by every operator. A nested study - each operator gets their
    own parts - cannot ask the question this level is about, and that is a study
    design decision rather than an arithmetic one.
    """
    rng = np.random.default_rng(seed)
    p_eff = rng.normal(0.0, part_sigma, parts)
    o_eff = rng.normal(0.0, operator, operators)
    po_eff = rng.normal(0.0, interaction, (parts, operators))
    err = rng.normal(0.0, repeat, (parts, operators, trials))
    reads = (p_eff[:, None, None] + o_eff[None, :, None]
             + po_eff[:, :, None] + err)
    return {"readings": reads, "part": p_eff, "operator": o_eff,
            "interaction": po_eff, "error": err}


def anova(reads: np.ndarray) -> dict:
    """The two-way crossed ANOVA with replication, and its variance components.

    Sums of squares by hand rather than from a library, because the identity in
    claim 4 is the point: if these four do not add to the total, the
    decomposition is not a decomposition.

    The variance components come from inverting the expected mean squares:

        E[MS_part]  = e + t*i + o*t*p
        E[MS_oper]  = e + t*i + parts*t*o
        E[MS_inter] = e + t*i
        E[MS_error] = e

    which is why a component can come out negative - it is a difference of two
    mean squares, exactly like Level 2's reproducibility.
    """
    p, o, t = reads.shape
    grand = reads.mean()
    part_means = reads.mean(axis=(1, 2))
    oper_means = reads.mean(axis=(0, 2))
    cell_means = reads.mean(axis=2)

    ss_part = o * t * ((part_means - grand) ** 2).sum()
    ss_oper = p * t * ((oper_means - grand) ** 2).sum()
    ss_inter = t * ((cell_means - part_means[:, None] - oper_means[None, :]
                     + grand) ** 2).sum()
    ss_err = ((reads - cell_means[:, :, None]) ** 2).sum()
    ss_tot = ((reads - grand) ** 2).sum()

    df_part, df_oper = p - 1, o - 1
    df_inter, df_err = (p - 1) * (o - 1), p * o * (t - 1)

    ms_part, ms_oper = ss_part / df_part, ss_oper / df_oper
    ms_inter, ms_err = ss_inter / df_inter, ss_err / df_err

    # each term is tested against the interaction, not against the error: in a
    # random-effects model the interaction is the correct denominator for both
    # main effects, and using the error term instead inflates every F
    f_part, f_oper = ms_part / ms_inter, ms_oper / ms_inter
    f_inter = ms_inter / ms_err

    v_err = ms_err
    v_inter = (ms_inter - ms_err) / t
    v_oper = (ms_oper - ms_inter) / (p * t)
    v_part = (ms_part - ms_inter) / (o * t)

    return {
        "ss": {"part": ss_part, "operator": ss_oper, "interaction": ss_inter,
               "repeat": ss_err, "total": ss_tot},
        "df": {"part": df_part, "operator": df_oper, "interaction": df_inter,
               "repeat": df_err},
        "ms": {"part": ms_part, "operator": ms_oper, "interaction": ms_inter,
               "repeat": ms_err},
        "f": {"part": f_part, "operator": f_oper, "interaction": f_inter},
        "p": {"part": float(stats.f.sf(f_part, df_part, df_inter)),
              "operator": float(stats.f.sf(f_oper, df_oper, df_inter)),
              "interaction": float(stats.f.sf(f_inter, df_inter, df_err))},
        # raw components, unclamped, so a negative one can be counted
        "var_raw": {"part": v_part, "operator": v_oper,
                    "interaction": v_inter, "repeat": v_err},
        "var": {"part": max(v_part, 0.0), "operator": max(v_oper, 0.0),
                "interaction": max(v_inter, 0.0), "repeat": v_err},
    }


def rr_from_anova(a: dict, pool: bool = False) -> dict:
    """Gauge variation from the ANOVA components.

    `pool=True` follows AIAG when the interaction test is not significant: the
    interaction sum of squares is folded back into repeatability and the model
    is refitted without the term. That is a real convention with a real cost,
    which claim 5 measures rather than asserts.
    """
    v = a["var"]
    if pool:
        # pooled error = (SS_inter + SS_err) / (df_inter + df_err)
        ss = a["ss"]["interaction"] + a["ss"]["repeat"]
        df = a["df"]["interaction"] + a["df"]["repeat"]
        repeat = ss / df
        return {"repeat": repeat, "operator": max(v["operator"], 0.0),
                "interaction": 0.0,
                "gauge": math.sqrt(repeat + max(v["operator"], 0.0)),
                "pooled": True}
    return {"repeat": v["repeat"], "operator": v["operator"],
            "interaction": v["interaction"],
            "gauge": math.sqrt(v["repeat"] + v["operator"] + v["interaction"]),
            "pooled": False}


@functools.lru_cache(maxsize=None)
def d2(n: int, reps: int = 400_000, seed: int = 9) -> float:
    """The expected range of `n` standard normals, by simulation.

    Cached, and the cache is load-bearing rather than tidy: `average_and_range`
    needs it once per study, the sweep runs eighteen hundred studies, and each
    uncached call draws four hundred thousand samples. Importing this module took
    two minutes before the cache and takes seconds after it. Deterministic seed,
    so the cache cannot change an answer.

    Derived rather than quoted, then checked against the printed table in the
    tests - the same rule Level 1 used for c4. Average-and-range needs it, and a
    method that rests on a looked-up constant cannot claim its answer is
    reconstructible.
    """
    if n < 2:
        raise ValueError("a range needs at least two observations")
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, (reps, n))
    return float((x.max(axis=1) - x.min(axis=1)).mean())


def average_and_range(reads: np.ndarray, d2_trials: float | None = None,
                      d2_ops: float | None = None) -> dict:
    """The classical average-and-range Gage R&R.

    Repeatability from the mean within-cell range; reproducibility from the
    range of the operator averages, with the repeatability that average carries
    subtracted off - which is exactly Level 2's correction, and it is why AV can
    go negative here too.

    What matters for this level is what is absent: there is no term for the
    part-by-operator interaction anywhere in this arithmetic.
    """
    p, o, t = reads.shape
    d2t = d2(t) if d2_trials is None else d2_trials
    d2o = d2(o) if d2_ops is None else d2_ops

    cell_ranges = reads.max(axis=2) - reads.min(axis=2)
    rbar = float(cell_ranges.mean())
    ev = rbar / d2t

    oper_means = reads.mean(axis=(0, 2))
    r_o = float(oper_means.max() - oper_means.min())
    av_var = (r_o / d2o) ** 2 - ev ** 2 / (p * t)
    av = math.sqrt(av_var) if av_var > 0 else 0.0

    return {"ev": ev, "av": av, "rbar": rbar, "r_operators": r_o,
            "av_negative": av_var <= 0,
            "gauge": math.sqrt(ev ** 2 + av ** 2)}


def compare(interaction: float, seed: int = SEED, **kw) -> dict:
    """Both methods on one study, plus the truth they are both estimating."""
    s = study(seed=seed, interaction=interaction, **kw)
    reads = s["readings"]
    a = anova(reads)
    ar = average_and_range(reads)
    rr = rr_from_anova(a)
    truth = math.sqrt(SIGMA_REPEAT ** 2 + SIGMA_OPERATOR ** 2 + interaction ** 2)
    return {"anova": rr, "xbar_r": ar, "truth": truth, "table": a,
            "anova_err": (rr["gauge"] / truth - 1) * 100,
            "xbar_err": (ar["gauge"] / truth - 1) * 100}


def sweep(strengths=(0.0, 0.6, 1.2, 1.9, 2.6, 3.4), n: int = 300,
          seed: int = 700) -> list[dict]:
    """Average both methods over many studies at each interaction strength.

    One study cannot separate two methods that differ by a few percent - that
    lesson is now two levels old - so the comparison is made on the mean of
    three hundred studies at each point.
    """
    rng = np.random.default_rng(seed)
    out = []
    for g in strengths:
        av, xv, tr = [], [], []
        for _ in range(n):
            c = compare(g, seed=int(rng.integers(1 << 31)))
            av.append(c["anova"]["gauge"])
            xv.append(c["xbar_r"]["gauge"])
            tr.append(c["truth"])
        out.append({"interaction": g,
                    "anova": float(np.mean(av)),
                    "xbar_r": float(np.mean(xv)),
                    "truth": float(np.mean(tr)),
                    "anova_err": (float(np.mean(av)) / tr[0] - 1) * 100,
                    "xbar_err": (float(np.mean(xv)) / tr[0] - 1) * 100})
    return out


# ------------------------------------------------------------ computed facts
CLEAN = compare(SIGMA_INTERACTION)
DIRTY = compare(BAD_INTERACTION)

#: Claim 1, stated carefully. On one clean study the two answers differ by about
#: 8 %, which is not "identical" - and saying they agree exactly would be the
#: third time this curriculum read one small study as if it were a law. What is
#: true is that with no interaction both sit within a few percent of the truth,
#: and neither is systematically wrong. The divergence in claim 2 is an order of
#: magnitude larger than this and it has a direction.
CLEAN_ANOVA = CLEAN["anova"]["gauge"]
CLEAN_XBAR = CLEAN["xbar_r"]["gauge"]
CLEAN_GAP_PCT = abs(CLEAN_XBAR / CLEAN_ANOVA - 1) * 100

#: Claim 2: with an interaction they part company. Note the direction is a
#: property of the average over studies, NOT of any single study - on the seeded
#: dirty study ANOVA overshoots by more than average-and-range undershoots, and a
#: page that read this one study would draw the wrong conclusion. Fourth time this
#: curriculum has met that trap; it now has a test of its own.
DIRTY_ANOVA = DIRTY["anova"]["gauge"]
DIRTY_XBAR = DIRTY["xbar_r"]["gauge"]
DIRTY_TRUTH = DIRTY["truth"]
DIRTY_GAP_PCT = (DIRTY_ANOVA / DIRTY_XBAR - 1) * 100
INTERACTION_SHARE = (DIRTY["anova"]["interaction"]
                     / (DIRTY["anova"]["repeat"] + DIRTY["anova"]["operator"]
                        + DIRTY["anova"]["interaction"]) * 100)

#: Claim 4: the identity, as a residual that has to be zero.
IDENT = CLEAN["table"]["ss"]
IDENT_RESIDUAL = abs(IDENT["total"] - (IDENT["part"] + IDENT["operator"]
                                       + IDENT["interaction"] + IDENT["repeat"]))

#: Claim 5: the interaction test, and what pooling costs.
F_INTER_CLEAN = CLEAN["table"]["f"]["interaction"]
P_INTER_CLEAN = CLEAN["table"]["p"]["interaction"]
F_INTER_DIRTY = DIRTY["table"]["f"]["interaction"]
P_INTER_DIRTY = DIRTY["table"]["p"]["interaction"]
POOLED_DIRTY = rr_from_anova(DIRTY["table"], pool=True)
POOL_COST_PCT = (1 - POOLED_DIRTY["gauge"] / DIRTY_ANOVA) * 100

#: The sweep, for the figure and for the claim that the direction is systematic.
SWEEP = sweep()

#: The sweep read as two numbers: how wrong each method is with no interaction,
#: and how wrong it becomes with a real one. This is the comparison, not the
#: single-study gap above.
AT_ZERO = SWEEP[0]
AT_WORST = SWEEP[-1]
ANOVA_DRIFT_PCT = abs(AT_WORST["anova_err"] - AT_ZERO["anova_err"])
XBAR_DRIFT_PCT = abs(AT_WORST["xbar_err"] - AT_ZERO["xbar_err"])
#: ANOVA is not unbiased either: estimating an operator component on two degrees
#: of freedom and then taking a square root pulls it low. Naming that is the
#: difference between a method that is imprecise and one that is wrong.
ANOVA_ZERO_BIAS_PCT = AT_ZERO["anova_err"]

D2_TRIALS = d2(TRIALS)
D2_OPERATORS = d2(OPERATORS)


def main() -> None:
    print(f"the study: {PARTS} parts x {OPERATORS} operators x {TRIALS} trials, "
          f"crossed")
    print(f"  true repeatability {SIGMA_REPEAT}  operator {SIGMA_OPERATOR}")
    print()
    print("1. with no interaction, neither method is systematically wrong")
    print(f"  one clean study: ANOVA {CLEAN_ANOVA:.4f}  X-bar-R {CLEAN_XBAR:.4f}  "
          f"gap {CLEAN_GAP_PCT:.1f} %")
    print(f"  over 300 studies: ANOVA {AT_ZERO['anova_err']:+.1f} %  "
          f"X-bar-R {AT_ZERO['xbar_err']:+.1f} % against the truth")
    print(f"  ANOVA's {ANOVA_ZERO_BIAS_PCT:+.1f} % is a real downward bias - an "
          f"operator component on 2 df, square-rooted")
    print(f"  (d2 derived: {TRIALS} trials {D2_TRIALS:.4f}, "
          f"{OPERATORS} operators {D2_OPERATORS:.4f})")
    print()
    print("4. and the sums of squares add up exactly")
    print(f"  total {IDENT['total']:.6f}")
    print(f"  parts {IDENT['part']:.6f} + operators {IDENT['operator']:.6f}")
    print(f"  + interaction {IDENT['interaction']:.6f} + repeat {IDENT['repeat']:.6f}")
    print(f"  residual {IDENT_RESIDUAL:.3e}")
    print()
    print(f"2. now give the operators an interaction of {BAD_INTERACTION} um")
    print(f"  the truth        {DIRTY_TRUTH:.4f} um")
    print(f"  ANOVA            {DIRTY_ANOVA:.4f} um  ({DIRTY['anova_err']:+.1f} %)")
    print(f"  average-and-range {DIRTY_XBAR:.4f} um  ({DIRTY['xbar_err']:+.1f} %)")
    print(f"  ANOVA reports a gauge {DIRTY_GAP_PCT:.1f} % larger - and on THIS "
          f"study it overshoots, while X-bar-R undershoots by less")
    print(f"  one study does not settle it. the sweep below does.")
    print(f"  the interaction is {INTERACTION_SHARE:.0f} % of the gauge variance")
    print()
    print("   averaged over 300 studies at each strength:")
    for row in SWEEP:
        print(f"     interaction {row['interaction']:.1f} -> ANOVA "
              f"{row['anova_err']:+6.1f} %   X-bar-R {row['xbar_err']:+6.1f} %")
    print()
    print("5. the interaction is tested, and pooling has a cost")
    print(f"  clean study: F {F_INTER_CLEAN:.2f}  p {P_INTER_CLEAN:.3f}"
          f"  -> pool (p > {POOL_ALPHA})" if P_INTER_CLEAN > POOL_ALPHA else "")
    print(f"  dirty study: F {F_INTER_DIRTY:.2f}  p {P_INTER_DIRTY:.5f}"
          f"  -> keep the term")
    print(f"  pooling the dirty study anyway understates the gauge by "
          f"{POOL_COST_PCT:.1f} %")
    print()
    print(f"  the whole comparison in two numbers: as the interaction grows from "
          f"0 to {AT_WORST['interaction']}, ANOVA moves "
          f"{ANOVA_DRIFT_PCT:.1f} % and average-and-range moves "
          f"{XBAR_DRIFT_PCT:.1f} %")
    print()
    print("so there are four numbers, not three. Which of them do you divide by,")
    print("and by what? That is Level 4.")


if __name__ == "__main__":
    main()
