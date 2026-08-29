"""LEVEL 7 - The handshake back.

Six levels have described a measurement system. None of them said what it is
for. A gauge exists because somebody is watching a process, and everything the
first six levels computed has to be handed to that person in a form they can
use - which turns out to have its own arithmetic, and one exact identity.

The identity is the whole level:

    Cpk_max = 100 / %GRR_tol

A gauge whose spread is a given fraction of the tolerance caps the capability
you can ever demonstrate, no matter how good the process becomes. AIAG's 10 %
guideline is a Cpk ceiling of 10. Its 30 % reject line is a ceiling of 3.33. The
number the MSA side computes and the number the SPC side reports are the same
number, and nobody writes it down that way.

Seven claims:

1. A control chart computed from readings has limits inflated by the gauge, by
   exactly sqrt(1 + (sigma_g/sigma_p)^2). The chart is wider than the process it
   is watching, and it was never told.
2. So measurement error is paid for in detection. A real shift is standardised
   against the inflated spread, so the average run length to catch it grows.
   With our own gauge a 1.5-sigma shift takes noticeably longer to find.
3. Capability is hit in the same direction and cannot be argued with: observed
   Cpk is true Cpk divided by that same inflation factor.
4. And it has a ceiling. Let the process become perfect and the observed Cpk
   stops at 100/%GRR_tol. This is exact, it is the seam between the two
   curricula, and it means an MSA verdict is a capability verdict already.
5. The chart cannot separate the two by itself. R-bar over d2 estimates the
   within-subgroup spread, and gauge repeatability is inside it by construction.
   No amount of charting decomposes that - which is why a gauge study is a
   separate study, and why this site exists beside the other one.
6. What the chart is entitled to assume is exactly Level 5: that the gauge is
   stable. A drifting gauge puts a trend on the chart that no process caused.
7. And what the study owes the chart is its own structure: a gauge study run on
   a different subgroup size answers a question the chart is not asking.

    PYTHONPATH=src .venv/bin/python -m msalab.handshake
"""
from __future__ import annotations

import math

import numpy as np

from msalab.accuracy import GAUGE_SIGMA, _Phi
from msalab.against_what import TOLERANCE, tolerance_ratio
from msalab.measurement import PART_SIGMA
from msalab.reproducibility import SIGMA_REPEAT

#: The chart the process owner is running: subgroups of this size, 3-sigma
#: limits. Both are the near-universal defaults, and both matter below.
SUBGROUP = 5
LIMIT_SIGMAS = 3.0

#: Shifts to price, in true part standard deviations.
SHIFTS = (0.5, 1.0, 1.5, 2.0, 3.0)

#: The published %GRR gates, so the ceiling can be quoted against them.
AIAG_GATES = (10.0, 20.0, 30.0)


# ----------------------------------------------------------- claim 1: the width
def inflation(part: float = PART_SIGMA, gauge: float = GAUGE_SIGMA) -> float:
    """How much wider the observed spread is than the true one.

    This is Level 1's identity with the square root taken, and it is the single
    number the rest of this level is built from.
    """
    return math.sqrt(1.0 + (gauge / part) ** 2)


def chart_limits(part: float = PART_SIGMA, gauge: float = GAUGE_SIGMA,
                 n: int = SUBGROUP, k: float = LIMIT_SIGMAS) -> dict:
    """The limits a chart draws from readings, against the limits the process
    would have earned if it could be seen directly."""
    obs = math.hypot(part, gauge)
    true_half = k * part / math.sqrt(n)
    obs_half = k * obs / math.sqrt(n)
    return {"true_half_width": true_half, "observed_half_width": obs_half,
            "inflation": obs_half / true_half,
            "wider_pct": (obs_half / true_half - 1.0) * 100.0}


# ------------------------------------------------------ claim 2: the detection
def arl(shift: float, part: float = PART_SIGMA, gauge: float = GAUGE_SIGMA,
        n: int = SUBGROUP, k: float = LIMIT_SIGMAS) -> dict:
    """Average run length to catch a shift of `shift` true part sigmas.

    The chart's limits come from the observed data, so they are set at k times
    the observed subgroup standard error. A real shift moves the observed mean by
    the same physical amount either way - so the shift the chart sees, in units
    of its own limits, is divided by the inflation factor. That is the entire
    mechanism, and it is why a noisy gauge costs detection rather than just
    precision.
    """
    obs = math.hypot(part, gauge)
    # standardised shift against the chart's own scale
    d_true = shift * math.sqrt(n)
    d_obs = shift * math.sqrt(n) * (part / obs)

    def p_signal(d: float) -> float:
        return (1.0 - _Phi(k - d)) + _Phi(-k - d)

    p_t, p_o = p_signal(d_true), p_signal(d_obs)
    return {"shift": shift,
            "arl_if_gauge_were_perfect": 1.0 / p_t if p_t > 0 else float("inf"),
            "arl_as_charted": 1.0 / p_o if p_o > 0 else float("inf"),
            "subgroups_lost": (1.0 / p_o - 1.0 / p_t) if p_t > 0 and p_o > 0
                              else float("inf"),
            "penalty_ratio": (p_t / p_o) if p_o > 0 else float("inf")}


# ----------------------------------------------------- claims 3 and 4: the ceiling
def capability(part: float = PART_SIGMA, gauge: float = GAUGE_SIGMA,
               tolerance: float = TOLERANCE) -> dict:
    """Observed capability against true, and the ceiling the gauge imposes.

    For a centred process Cpk is (T/2)/(3 sigma). Substituting the observed
    sigma gives the number that gets reported, and letting the process become
    perfect gives the largest number that could ever be reported with this gauge:

        Cpk_max = T / (6 sigma_gauge) = 100 / %GRR_tol

    The second equality is not an approximation. %GRR against tolerance is
    defined as 6 sigma_gauge / T, so the two are reciprocals scaled by a
    hundred, which makes an MSA verdict a capability verdict in disguise.
    """
    obs = math.hypot(part, gauge)
    true_cpk = (tolerance / 2.0) / (3.0 * part)
    obs_cpk = (tolerance / 2.0) / (3.0 * obs)
    ceiling = tolerance / (6.0 * gauge)
    grr_tol = tolerance_ratio(gauge, tolerance)
    return {"true_cpk": true_cpk, "observed_cpk": obs_cpk,
            "cpk_lost": true_cpk - obs_cpk,
            "ceiling": ceiling,
            "grr_tolerance_pct": grr_tol,
            "ceiling_from_grr": 100.0 / grr_tol,
            "identity_holds": abs(ceiling - 100.0 / grr_tol) < 1e-12}


def ceiling_table(gates: tuple[float, ...] = AIAG_GATES) -> list[dict]:
    """The published %GRR gates, restated as the Cpk they permit.

    This is the table that should be printed next to the gates and never is.
    """
    return [{"grr_tolerance_pct": g, "cpk_ceiling": 100.0 / g} for g in gates]


def grr_for_cpk(target_cpk: float, part: float = PART_SIGMA,
                tolerance: float = TOLERANCE) -> dict:
    """Read the identity backwards, and then check it against a real process.

    The ceiling is a *necessary* condition and a weak one: it says what the gauge
    alone permits with a perfect process. The binding question is what this
    process can report once the parts are underneath the gauge, and that answer
    is often "not this target at any gauge at all" - which the ceiling on its own
    would never tell you.

    Reporting only the ceiling was this module's first version, and it produced
    the reassuring and useless statement that Cpk 1.33 needs a gauge under 75 %
    of tolerance. On this process 1.33 is unreachable with a perfect gauge.
    """
    budget = tolerance / (6.0 * target_cpk)     # the whole observed sigma allowed
    ceiling_grr = 100.0 / target_cpk            # gauge-only, perfect process
    feasible = budget > part
    needed = math.sqrt(budget ** 2 - part ** 2) if feasible else float("nan")
    return {"target_cpk": target_cpk,
            "observed_sigma_budget": budget,
            "max_grr_tolerance_pct": ceiling_grr,
            "gauge_only_sigma": ceiling_grr / 100.0 * tolerance / 6.0,
            "reachable_on_this_process": feasible,
            "gauge_sigma_required": needed,
            "grr_required_pct": (6.0 * needed / tolerance * 100.0) if feasible
                                else float("nan")}


# -------------------------------------------- claim 5: the chart cannot separate
def within_subgroup_content(part: float = PART_SIGMA,
                            repeat: float = SIGMA_REPEAT,
                            n: int = SUBGROUP) -> dict:
    """What the chart's own within-subgroup estimate is actually made of.

    Consecutive parts in a subgroup differ by real part-to-part variation and by
    the gauge repeating itself badly. The estimate sees their sum.
    """
    within = math.hypot(part, repeat)
    return {"part": part, "repeat": repeat, "within_estimate": within,
            "gauge_share_of_variance": repeat ** 2 / within ** 2 * 100.0,
            "gauge_share_of_sigma": (within - part) / within * 100.0}


def indistinguishable_pairs(within: float | None = None,
                            fractions: tuple[float, ...] = (0.0, 0.2, 0.4, 0.6,
                                                            0.8)) -> list[dict]:
    """Different processes and different gauges, one identical chart.

    Inseparability is worth demonstrating rather than asserting. Fix the
    within-subgroup spread the chart estimates, then split it between part
    variation and gauge repeatability every way the arithmetic allows. Every row
    produces the *same* number on the chart, so no chart can tell them apart -
    including the row where the gauge is most of the width.

    Which is the structural reason the two curricula cannot be one curriculum: a
    gauge study is not a nicety alongside charting, it is the only thing that can
    answer a question charting cannot pose.
    """
    if within is None:
        within = math.hypot(PART_SIGMA, SIGMA_REPEAT)
    rows = []
    for f in fractions:
        rep = math.sqrt(f) * within
        prt = math.sqrt(within ** 2 - rep ** 2)
        rows.append({"gauge_share_of_variance": f * 100.0,
                     "part": prt, "repeat": rep,
                     "within_estimate": math.hypot(prt, rep),
                     "true_cpk": (TOLERANCE / 2.0) / (3.0 * prt)
                                 if prt > 1e-12 else float("inf")})
    return rows


# ---------------------------------------- claim 6: what the chart may assume
def drift_on_the_chart(drift_per_subgroup: float = 0.18,
                       subgroups: int = 25, part: float = PART_SIGMA,
                       gauge: float = GAUGE_SIGMA, n: int = SUBGROUP,
                       k: float = LIMIT_SIGMAS) -> dict:
    """A gauge drifting slowly puts a trend on the chart that no process caused.

    Level 5 showed a drift is invisible to any single gauge study. Here is where
    it becomes visible - on somebody else's chart, as a process problem, and it
    will be investigated as one.
    """
    obs = math.hypot(part, gauge)
    half = k * obs / math.sqrt(n)
    means = np.array([drift_per_subgroup * i for i in range(subgroups)])
    outside = int(np.sum(np.abs(means) > half))
    # seven in a row on one side of centre: the classic run rule
    run = 0
    first_run = None
    for i, m in enumerate(means):
        run = run + 1 if m > 0 else 0
        if run >= 7 and first_run is None:
            first_run = i
    return {"drift_per_subgroup": drift_per_subgroup,
            "subgroups": subgroups,
            "total_drift": float(means[-1]),
            "limit_half_width": half,
            "points_outside": outside,
            "first_run_of_seven": first_run,
            "signals_before_it_leaves_the_limits": first_run is not None
                                                   and (outside == 0
                                                        or first_run <
                                                        int(np.argmax(
                                                            np.abs(means)
                                                            > half)))}


# ------------------------------- claim 7: the study owes the chart its structure
def wrong_subgroup(part: float = PART_SIGMA, gauge: float = GAUGE_SIGMA,
                   study_n: int = 3, chart_n: int = SUBGROUP,
                   k: float = LIMIT_SIGMAS) -> dict:
    """A gauge study averaging `study_n` readings, handed to a chart of `chart_n`.

    Level 1 showed averaging divides the gauge term by the root of the count and
    never touches the parts. So a study that reports the gauge as an average of
    three readings has reported a gauge the chart is not using, and the chart's
    limits will be wider than the study predicted.
    """
    as_studied = math.hypot(part, gauge / math.sqrt(study_n))
    as_charted = math.hypot(part, gauge)
    return {"study_averages": study_n, "chart_averages": 1,
            "gauge_as_studied": gauge / math.sqrt(study_n),
            "gauge_as_used": gauge,
            "spread_as_studied": as_studied,
            "spread_as_charted": as_charted,
            "limits_understated_pct": (as_charted / as_studied - 1.0) * 100.0}


# ------------------------------------------------------------ computed facts
INFLATION = inflation()
LIMITS = chart_limits()
ARLS = [arl(s) for s in SHIFTS]
CAP = capability()
CEILINGS = ceiling_table()
WITHIN = within_subgroup_content()
SAME_CHART = indistinguishable_pairs()
DRIFT_CHART = drift_on_the_chart()
WRONG_N = wrong_subgroup()

CEILING = CAP["ceiling"]
IDENTITY_HOLDS = CAP["identity_holds"]
WIDER_PCT = LIMITS["wider_pct"]
ARL_15 = next(a for a in ARLS if a["shift"] == 1.5)


def main() -> None:
    print(f"the gauge: {GAUGE_SIGMA:.4f} um   the parts: {PART_SIGMA} um   "
          f"tolerance {TOLERANCE:.0f} um")
    print(f"the chart: subgroups of {SUBGROUP}, "
          f"+/-{LIMIT_SIGMAS:.0f} sigma limits")
    print()

    print("1. the chart's limits already contain the gauge")
    print(f"  inflation factor sqrt(1 + (sg/sp)^2)      {INFLATION:.4f}")
    print(f"  limits the process earned    +/-{LIMITS['true_half_width']:.4f} um")
    print(f"  limits the chart draws       "
          f"+/-{LIMITS['observed_half_width']:.4f} um")
    print(f"  so the chart is             {WIDER_PCT:6.2f} % wider than "
          f"the process it watches")
    print()

    print("2. and pays for it in detection - worst where it matters most")
    print("     shift    if perfect    as charted    lost    slower by")
    for a in ARLS:
        print(f"    {a['shift']:5.1f}σ  {a['arl_if_gauge_were_perfect']:10.2f}  "
              f"{a['arl_as_charted']:12.2f}  {a['subgroups_lost']:6.2f}  "
              f"{(a['penalty_ratio'] - 1) * 100:8.1f} %")
    small = ARLS[0]
    print(f"  a big shift is found by anybody; the cost lands on the small ones.")
    print(f"  at {small['shift']}σ the wait grows "
          f"{small['arl_if_gauge_were_perfect']:.1f} -> "
          f"{small['arl_as_charted']:.1f} subgroups, "
          f"{(small['penalty_ratio'] - 1) * 100:.0f} % longer")
    print()

    print("3. capability moves the same way")
    print(f"  true Cpk        {CAP['true_cpk']:.4f}")
    print(f"  observed Cpk    {CAP['observed_cpk']:.4f}")
    print(f"  lost to the gauge alone  {CAP['cpk_lost']:.4f}")
    print()

    print("4. and there is a ceiling, and it is an identity")
    print(f"  T / (6 sigma_gauge)   {CAP['ceiling']:.6f}")
    print(f"  100 / %GRR_tol        {CAP['ceiling_from_grr']:.6f}")
    print(f"  identical             {CAP['identity_holds']}")
    print(f"  (%GRR against tolerance is {CAP['grr_tolerance_pct']:.4f} %)")
    print()
    print("  which restates the published gates as capability limits:")
    for c in CEILINGS:
        print(f"    %GRR_tol {c['grr_tolerance_pct']:5.1f} %  ->  "
              f"Cpk can never exceed {c['cpk_ceiling']:6.3f}")
    print()
    print("  read backwards, against this actual process:")
    for target in (1.00, 1.33, 1.67, 2.00):
        r = grr_for_cpk(target)
        if r["reachable_on_this_process"]:
            print(f"    Cpk {target:.2f}: needs the gauge under "
                  f"{r['grr_required_pct']:5.1f} % of tolerance "
                  f"(sigma < {r['gauge_sigma_required']:.3f} um)")
        else:
            print(f"    Cpk {target:.2f}: UNREACHABLE on this process - the whole "
                  f"sigma budget is {r['observed_sigma_budget']:.3f} um and the "
                  f"parts alone are {PART_SIGMA}")
    print()

    print("5. and the chart cannot take the gauge back out")
    print(f"  the within-subgroup spread it estimates: "
          f"{WITHIN['within_estimate']:.4f} um, of which "
          f"{WITHIN['gauge_share_of_variance']:.2f} % of the variance is the gauge")
    print("  every one of these produces the identical number on the chart:")
    print("     gauge share    parts      gauge      what the chart sees   true Cpk")
    for r in SAME_CHART:
        cpk = ("      inf" if math.isinf(r["true_cpk"])
               else f"{r['true_cpk']:9.3f}")
        print(f"    {r['gauge_share_of_variance']:9.0f} %  "
              f"{r['part']:9.4f}  {r['repeat']:9.4f}  "
              f"{r['within_estimate']:19.4f}  {cpk}")
    print("  so a chart cannot pose the question, let alone answer it.")
    print()

    print("6. what the chart is entitled to assume: a stable gauge")
    print(f"  a gauge drifting {DRIFT_CHART['drift_per_subgroup']} um per "
          f"subgroup over {DRIFT_CHART['subgroups']} subgroups")
    print(f"  reaches {DRIFT_CHART['total_drift']:.2f} um against limits at "
          f"+/-{DRIFT_CHART['limit_half_width']:.2f}")
    print(f"  points outside the limits: {DRIFT_CHART['points_outside']}")
    print(f"  first run of seven above centre: subgroup "
          f"{DRIFT_CHART['first_run_of_seven']}")
    print("  and it will be investigated as a process problem")
    print()

    print("7. what the study owes the chart: its own structure")
    print(f"  a study reporting the gauge as an average of "
          f"{WRONG_N['study_averages']} readings")
    print(f"    calls the gauge {WRONG_N['gauge_as_studied']:.4f} um; "
          f"the chart uses {WRONG_N['gauge_as_used']:.4f}")
    print(f"    so the limits come out {WRONG_N['limits_understated_pct']:.2f} % "
          f"wider than the study predicted")
    print()
    print("  seven levels. The arc closes where the other one starts.")


if __name__ == "__main__":
    main()
