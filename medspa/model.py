"""
Med-spa AI-automation agency — 24-month scaling scenario model.

Solo founder, GoHighLevel-based, med spas only.
  Entry tier:  $500/mo  (DB reactivation + review & referral automation), $0 setup.
  Full tier:   $1,500/mo (missed-call text-back, speed-to-lead, voice AI, ROI dash),
               offered ~2 months after close once the ROI dashboard shows $5k+ recovered.

This is the AUTHORITATIVE engine. Every assumption lives in ASSUMPTIONS or in the
per-scenario levers below and is editable in one place. Pure stdlib — run with:

    python3 medspa/model.py

It writes one CSV per scenario to medspa/outputs/, a machine-readable
medspa/outputs/all_scenarios.json (used by the HTML dashboard), and prints a
summary + the two sensitivity analyses.

The HTML dashboard (medspa/dashboard.html) mirrors these exact formulas in JS so
you can edit inputs live; this file is the ground truth to check it against.

WHEN YOU PASTE REAL DATA: overwrite the numbers in ASSUMPTIONS (cost_per_lead,
lead_to_booked, show_rate, close_0cs / close_3cs, churn, upsell take per scenario)
and rerun. Nothing else needs to change.
"""

from __future__ import annotations
import json
import csv
import os
import math
from dataclasses import dataclass, field, asdict

HORIZON = 24  # months; Month 1 = launch

# ─────────────────────────────────────────────────────────────────────────────
# EDITABLE ASSUMPTIONS  (state them BEFORE using them)
# ─────────────────────────────────────────────────────────────────────────────

ASSUMPTIONS = {
    # ---- FUNNEL (Meta lead ads -> booking funnel -> demo you close) ----
    # Defaults are honest cold-B2B numbers for selling TO med-spa owners (a narrow
    # audience). Replace with your mentor's student numbers or your first 2 weeks.
    "cost_per_lead":      25.0,   # $/lead, blended steady-state (pre learning/fatigue/saturation)
    "lead_to_booked":     0.25,   # lead -> booked demo
    "show_rate":          0.60,   # booked -> showed (5-min callback + reminders assumed)
    "close_0cs":          0.12,   # close rate on cold traffic with ZERO case studies
    "close_3cs":          0.28,   # close rate on cold traffic with 3+ case studies
    "close_social_bonus": 0.03,   # extra close-rate points earned from 3 -> 10 case studies

    # Launch algorithm learning phase (~first 2 weeks live; month 1 hit, month 2 partial):
    "learn_cpl_mult":   {1: 1.60, 2: 1.20},   # CPL multiplier while the pixel learns
    "learn_close_mult": {1: 0.60, 2: 0.85},   # close-rate multiplier while you're rusty / no proof

    # Creative fatigue / refresh cycle: CPL drifts up each month a creative ages,
    # resets on refresh. refresh_cycle (months) is set per funnel-optimization level below.
    "fatigue_rate": 0.05,         # +5% CPL per month a creative set ages between refreshes

    # Case studies: a fraction of matured clients (>=2 mo tenure) become usable proof assets.
    "case_study_yield": 0.40,     # 40% of matured clients yield a usable case study
    "case_study_cap":   12,       # you realistically feature at most ~12

    # Referrals (happens for everyone; the Hybrid scenario leverages it hard):
    "referral_yield_base": 0.020, # closed referrals per matured active client per month
    "referral_reward":     75.0,  # $ paid per referred client that closes

    # ---- FIXED BUSINESS ASSUMPTIONS ----
    "churn":            0.03,     # monthly logo churn (COMPOUNDS — see survival curve)
    "upsell_delay":     2,        # months after close that the upsell is offered/lands
    "price_entry":      500.0,
    "price_full":       1500.0,
    "tools_base":       300.0,    # $/mo GHL agency + stack, fixed floor
    "tools_per_client": 15.0,     # $/mo per active client (usage-based) -> ~$700 near 27 clients

    # Market / saturation (single metro):
    "metro_size":       300,      # addressable med spas per metro (range 200-400)
    "saturation_slope": 0.90,     # at 100% metro penetration, CPL is (1 + slope)x = 1.9x

    # Founder operating ceilings (why hires become MANDATORY, expressed as capacities):
    "solo_full_capacity":  15,    # full-tier installs one person can deliver
    "solo_support_cap":    28,    # total actives one person can support before churn rises
    "am_full_capacity":    20,    # extra full-tier installs each Account Manager adds
    "am_support_add":      10,    # extra total-support each AM adds
    "va_support_add":      25,    # extra total-support each VA adds
    "overload_churn_pen":  0.02,  # +2 pts/mo churn while over support capacity (no hire)
    "founder_spend_ceiling": 6000.0,  # $/mo ad spend a founder can manage before a media buyer

    # Team salaries ($/mo, fully loaded):
    "salary_va":          1800.0,
    "salary_media_buyer": 4000.0,
    "salary_account_mgr": 4500.0,
    "media_buyer_cpl_mult": 0.90,  # a real media buyer improves CPL ~10%
    "mb_manage_cap":      10000.0, # $/mo ad spend one media buyer can manage well

    # Setup fee (sensitivity toggle; base model = $0). A setup fee is NOT free money:
    # it removes the "$0 to start" closing weapon, so it drags the close rate.
    "setup_fee": 0.0,
    "setup_close_drag_at_297": 0.12,  # a $297 setup fee lowers close rate ~12% (scales w/ fee)
}

# Funnel-optimization level -> (steady CPL multiplier, creative refresh cycle in months)
FUNNEL_OPT = {
    "basic":     {"cpl_mult": 1.08, "refresh_cycle": 3},
    "good":      {"cpl_mult": 1.00, "refresh_cycle": 2},
    "optimized": {"cpl_mult": 0.92, "refresh_cycle": 1},
}


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIOS  — vary ONLY inputs the founder controls:
#   ad spend schedule, funnel-optimization level, hiring timing, expansion timing, pricing.
# Hire/expansion triggers are NUMBERS (client counts / spend), never dates.
# ─────────────────────────────────────────────────────────────────────────────

def spend_ramp(schedule):
    """schedule = list of (from_month, monthly_spend); fills 1..HORIZON."""
    out = {}
    cur = 0.0
    idx = 0
    sched = sorted(schedule)
    for m in range(1, HORIZON + 1):
        while idx < len(sched) and sched[idx][0] <= m:
            cur = sched[idx][1]
            idx += 1
        out[m] = cur
    return out


@dataclass
class Scenario:
    key: str
    name: str
    blurb: str
    ad_spend: dict                      # month -> $ ad spend
    funnel_opt: str = "good"
    upsell_take: float = 0.45
    referral_yield: float = 0.020       # per matured active client / month
    outreach_base: float = 0.0          # founder warm-outreach closes/mo when small (tapers)
    # hiring triggers (numeric); None = never
    va_trigger_active: float = 22       # hire VA when total actives >= this
    mb_trigger_spend: float = None      # hire media buyer when monthly spend >= this
    mb_trigger_active: float = None     # or when total actives >= this
    am_trigger_upsold: float = 13       # hire account manager when full-tier installs >= this
    # multi-metro expansion: open a new metro when active clients >= trigger (adds metro_size + spend)
    metro_expand_active: list = field(default_factory=list)   # e.g. [20, 40] -> metro 2 at 20, metro 3 at 40
    metro_expand_spend: float = 2500.0
    # premium pricing: when case studies >= trigger, raise prices
    price_raise_cs: float = None
    price_entry_new: float = None
    price_full_new: float = None
    price_close_haircut: float = 1.0    # close-rate multiplier once prices are raised


SCENARIOS = [
    Scenario(
        key="conservative",
        name="Ads-Only Conservative",
        blurb="Flat $2k/mo, stay solo as long as possible, basic funnel, low upsell push. Safe cash, slow ceiling.",
        ad_spend=spend_ramp([(1, 1500), (2, 2000)]),
        funnel_opt="basic",
        upsell_take=0.33,
        referral_yield=0.020,
        va_trigger_active=22, mb_trigger_spend=None, am_trigger_upsold=13,
    ),
    Scenario(
        key="aggressive",
        name="Ads-Only Aggressive",
        blurb="Ramp spend to $10k/mo, push volume, single metro. Fastest MRR, deepest drawdown, saturation bites.",
        ad_spend=spend_ramp([(1, 3000), (3, 5000), (6, 8000), (10, 10000)]),
        funnel_opt="good",
        upsell_take=0.45,
        referral_yield=0.020,
        va_trigger_active=16, mb_trigger_spend=6000, am_trigger_upsold=12,
    ),
    Scenario(
        key="hybrid",
        name="Hybrid (Ads + Referrals + Outreach)",
        blurb="Moderate $2.5k/mo ads + founder warm outreach + a real referral engine. Best blended CAC.",
        ad_spend=spend_ramp([(1, 2000), (2, 2500)]),
        funnel_opt="good",
        upsell_take=0.45,
        referral_yield=0.060,      # leveraged referral engine
        outreach_base=2.5,         # founder outreach closes/mo when small, tapers with load
        va_trigger_active=20, mb_trigger_spend=None, am_trigger_upsold=13,
    ),
    Scenario(
        key="team",
        name="Scale-With-Team",
        blurb="Hire early and deliberately (VA->media buyer->AM at MRR triggers) to break both ceilings. Highest ceiling, longest drawdown.",
        ad_spend=spend_ramp([(1, 3000), (3, 6000), (7, 9000), (12, 11000)]),
        funnel_opt="good",
        upsell_take=0.45,
        referral_yield=0.025,
        va_trigger_active=10, mb_trigger_active=15, am_trigger_upsold=11,
    ),
    Scenario(
        key="multimetro",
        name="Multi-Metro Expansion",
        blurb="Saturate metro 1, then open metros 2 & 3 at client-count triggers to reset CPL. Sidesteps saturation.",
        ad_spend=spend_ramp([(1, 2000), (2, 2500)]),
        funnel_opt="good",
        upsell_take=0.45,
        referral_yield=0.025,
        va_trigger_active=18, mb_trigger_active=30, am_trigger_upsold=12,
        metro_expand_active=[18, 36], metro_expand_spend=2500.0,
    ),
    Scenario(
        key="premium",
        name="Premium-Pricing Path",
        blurb="Build 10+ case studies at standard price, then raise entry->$750 & full->$2,000. Best margin & LTV, slower start.",
        ad_spend=spend_ramp([(1, 2000), (2, 2500), (8, 4000)]),
        funnel_opt="optimized",
        upsell_take=0.60,
        referral_yield=0.030,
        va_trigger_active=18, mb_trigger_spend=None, am_trigger_upsold=12,
        price_raise_cs=10, price_entry_new=750.0, price_full_new=2000.0, price_close_haircut=0.90,
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def simulate(sc: Scenario, A: dict) -> list[dict]:
    surv = 1.0 - A["churn"]
    opt = FUNNEL_OPT[sc.funnel_opt]
    refresh_cycle = opt["refresh_cycle"]

    rows = []
    closes_hist = []          # closes_hist[i] = new clients closed in month i+1 (entry tier)
    entry = 0.0               # active entry-tier clients (end of month)
    upsold = 0.0              # active full-tier clients (end of month)
    cum_cash = 0.0
    worst_draw = 0.0
    worst_draw_month = 0
    cum_booked = 0.0          # cumulative demos booked (proxy for metro penetration)
    metros = 1
    metro_capacity = A["metro_size"]
    va = mb = am = 0          # HEADCOUNT (sticky, non-decreasing) — set per month below

    for m in range(1, HORIZON + 1):
        total_active_prev = entry + upsold

        # ---- multi-metro expansion (numeric trigger on active clients) ----
        base_spend = sc.ad_spend[m]
        while len(sc.metro_expand_active) >= metros and total_active_prev >= sc.metro_expand_active[metros - 1]:
            metros += 1
            metro_capacity += A["metro_size"]
        opened_metro_spend = sc.metro_expand_spend * (metros - 1)
        ad_spend = base_spend + opened_metro_spend

        # ---- projected upsells this month (needed so AM capacity leads the book) ----
        j = m - A["upsell_delay"]
        desired_upsell = (closes_hist[j - 1] * (surv ** A["upsell_delay"]) * sc.upsell_take) if j >= 1 else 0.0
        proj_upsold = upsold + desired_upsell

        # ---- TEAM: scenario triggers set the PROACTIVE first hire; capacity makes
        #      further hires MANDATORY. Headcount is sticky (never fired here). ----
        trig_va = sc.va_trigger_active is not None and total_active_prev >= sc.va_trigger_active
        trig_am = sc.am_trigger_upsold is not None and upsold >= sc.am_trigger_upsold
        trig_mb = ((sc.mb_trigger_spend is not None and ad_spend >= sc.mb_trigger_spend)
                   or (sc.mb_trigger_active is not None and total_active_prev >= sc.mb_trigger_active)
                   or (metros >= 2 and total_active_prev >= 20))  # 2+ metros needs a buyer

        # Account managers: solo delivers 15 full installs; each AM adds am_full_capacity.
        req_am = math.ceil(max(0.0, proj_upsold - A["solo_full_capacity"]) / A["am_full_capacity"])
        am = max(am, req_am, 1 if trig_am else 0)
        # Support: solo supports solo_support_cap; each VA adds va_support_add, each AM helps too.
        support_room = A["solo_support_cap"] + A["am_support_add"] * am
        req_va = math.ceil(max(0.0, total_active_prev - support_room) / A["va_support_add"])
        va = max(va, req_va, 1 if trig_va else 0)
        # Media buyers: founder self-manages up to founder_spend_ceiling; each MB adds mb_manage_cap.
        req_mb = math.ceil(max(0.0, ad_spend - A["founder_spend_ceiling"]) / A["mb_manage_cap"])
        mb = max(mb, req_mb, 1 if trig_mb else 0)

        # ---- CPL this month: base * opt * learning * fatigue * saturation * mgmt ----
        cpl = A["cost_per_lead"] * opt["cpl_mult"]
        cpl *= A["learn_cpl_mult"].get(m, 1.0)
        months_since_refresh = (m - 1) % refresh_cycle
        cpl *= (1.0 + A["fatigue_rate"] * months_since_refresh)
        penetration = cum_booked / metro_capacity
        cpl *= (1.0 + A["saturation_slope"] * penetration)
        if mb:
            cpl *= A["media_buyer_cpl_mult"]
        # founder ad-management ceiling (diminishing returns above ceiling without a buyer)
        mgmt_pen = 1.0
        if not mb and ad_spend > A["founder_spend_ceiling"]:
            mgmt_pen = 1.0 + 0.30 * (ad_spend - A["founder_spend_ceiling"]) / A["founder_spend_ceiling"]
        cpl *= mgmt_pen

        # ---- case studies accrued (from clients matured >=2 months ago) ----
        cum_mature = sum(closes_hist[:max(0, m - 2)])   # closes in months 1..m-2
        case_studies = min(A["case_study_cap"], A["case_study_yield"] * cum_mature)

        # ---- pricing (premium path raises prices at a case-study trigger) ----
        price_entry = A["price_entry"]
        price_full = A["price_full"]
        close_haircut = 1.0
        prices_raised = False
        if sc.price_raise_cs is not None and case_studies >= sc.price_raise_cs:
            price_entry = sc.price_entry_new
            price_full = sc.price_full_new
            close_haircut = sc.price_close_haircut
            prices_raised = True

        # ---- close rate (ramps with case studies) * learning * price haircut ----
        t = min(1.0, case_studies / 3.0)
        close_rate = A["close_0cs"] + (A["close_3cs"] - A["close_0cs"]) * t
        if case_studies > 3:
            close_rate += min(1.0, (case_studies - 3) / 7.0) * A["close_social_bonus"]
        close_rate *= A["learn_close_mult"].get(m, 1.0)
        close_rate *= close_haircut
        if A["setup_fee"] > 0:   # a setup fee adds friction at the close
            close_rate *= (1.0 - A["setup_close_drag_at_297"] * A["setup_fee"] / 297.0)

        # ---- funnel -> paid closes ----
        leads = ad_spend / cpl if cpl > 0 else 0.0
        booked = leads * A["lead_to_booked"]
        shown = booked * A["show_rate"]
        paid_closes = shown * close_rate
        cum_booked += booked

        # ---- referral + outreach closes (near-zero cash CAC) ----
        matured_active = max(0.0, total_active_prev)  # clients that could refer
        referral_closes = sc.referral_yield * matured_active
        outreach_closes = 0.0
        if sc.outreach_base > 0:
            outreach_closes = max(0.0, sc.outreach_base - 0.05 * total_active_prev)  # founder time tapers
        new_closes = paid_closes + referral_closes + outreach_closes
        closes_hist.append(new_closes)

        # ---- churn (compounding) with overload penalty if over support capacity ----
        support_cap = A["solo_support_cap"] + A["va_support_add"] * va + A["am_support_add"] * am
        churn_eff = A["churn"]
        if total_active_prev > support_cap:
            churn_eff += A["overload_churn_pen"]
        s = 1.0 - churn_eff

        entry *= s
        upsold *= s

        # ---- new closes join entry tier this month ----
        entry += new_closes

        # ---- upsell: cohort from (m - upsell_delay), survivors * take, gated by delivery capacity ----
        new_upsells = 0.0
        j = m - A["upsell_delay"]
        if j >= 1:
            eligible = closes_hist[j - 1] * (surv ** A["upsell_delay"])
            desired = eligible * sc.upsell_take
            full_cap = A["solo_full_capacity"] + A["am_full_capacity"] * am
            room = max(0.0, full_cap - upsold)
            new_upsells = min(desired, room)   # can't deliver full installs you have no capacity for
            entry -= new_upsells
            upsold += new_upsells

        total_active = entry + upsold
        mrr = entry * price_entry + upsold * price_full

        # ---- costs & cash ----
        tools = A["tools_base"] + A["tools_per_client"] * total_active
        team = A["salary_va"] * va + A["salary_media_buyer"] * mb + A["salary_account_mgr"] * am
        referral_cost = referral_closes * A["referral_reward"]
        setup_rev = A["setup_fee"] * new_closes
        collections = mrr + setup_rev
        cash_flow = collections - ad_spend - tools - team - referral_cost
        cum_cash += cash_flow
        if cum_cash < worst_draw:
            worst_draw = cum_cash
            worst_draw_month = m

        # ---- CAC & payback ----
        cac_paid = ad_spend / paid_closes if paid_closes > 1e-9 else float("nan")
        cac_blended = (ad_spend + referral_cost) / new_closes if new_closes > 1e-9 else float("nan")
        # expected client contribution ramp for payback (uses THIS month's close economics)
        payback = expected_payback(cac_blended, sc.upsell_take, price_entry, price_full,
                                    A["tools_per_client"], A["upsell_delay"], surv)

        team_size = va + mb + am

        rows.append({
            "month": m,
            "ad_spend": round(ad_spend, 2),
            "cpl": round(cpl, 2),
            "penetration": round(penetration, 4),
            "metros": metros,
            "case_studies": round(case_studies, 2),
            "close_rate": round(close_rate, 4),
            "leads": round(leads, 2),
            "booked_demos": round(booked, 2),
            "demos_shown": round(shown, 2),
            "paid_closes": round(paid_closes, 3),
            "referral_closes": round(referral_closes, 3),
            "outreach_closes": round(outreach_closes, 3),
            "new_closes": round(new_closes, 3),
            "new_upsells": round(new_upsells, 3),
            "entry_active": round(entry, 2),
            "upsold_active": round(upsold, 2),
            "total_active": round(total_active, 2),
            "price_entry": price_entry,
            "price_full": price_full,
            "prices_raised": prices_raised,
            "mrr": round(mrr, 2),
            "tools": round(tools, 2),
            "team_cost": round(team, 2),
            "referral_cost": round(referral_cost, 2),
            "collections": round(collections, 2),
            "cash_flow": round(cash_flow, 2),
            "cum_cash": round(cum_cash, 2),
            "cac_paid": None if cac_paid != cac_paid else round(cac_paid, 2),
            "cac_blended": None if cac_blended != cac_blended else round(cac_blended, 2),
            "payback_months": None if payback != payback else round(payback, 2),
            "team_size": team_size,
            "va": va, "mb": mb, "am": am,
        })

    summary = {
        "worst_drawdown": round(worst_draw, 2),
        "worst_drawdown_month": worst_draw_month,
        "mrr_24": rows[-1]["mrr"],
        "active_24": rows[-1]["total_active"],
        "cum_cash_24": rows[-1]["cum_cash"],
    }
    return rows, summary


def expected_payback(cac, take, price_entry, price_full, tools_per_client, delay, surv):
    """Months until expected, survival-weighted client contribution recovers CAC."""
    if cac != cac or cac <= 0:
        return float("nan")
    cum = 0.0
    for k in range(0, 60):  # month 0 = close month
        price = price_entry if k < delay else (take * price_full + (1 - take) * price_entry)
        contribution = (price - tools_per_client) * (surv ** k)
        cum += contribution
        if cum >= cac:
            # linear interpolation within the month
            prev = cum - contribution
            return k + (cac - prev) / contribution
    return float("nan")


# ─────────────────────────────────────────────────────────────────────────────
# SENSITIVITY
# ─────────────────────────────────────────────────────────────────────────────

def month24_mrr(sc: Scenario, A: dict) -> float:
    rows, _ = simulate(sc, A)
    return rows[-1]["mrr"]


def sensitivity_tornado(base_scenario: Scenario, pct=0.20):
    """Perturb each single input +/- pct, measure change in month-24 MRR. Returns sorted list."""
    base_mrr = month24_mrr(base_scenario, ASSUMPTIONS)
    knobs = {
        "cost_per_lead":  "scalar",
        "lead_to_booked": "scalar",
        "show_rate":      "scalar",
        "close_3cs":      "scalar",
        "churn":          "scalar",
        "tools_per_client": "scalar",
    }
    results = []
    for knob in knobs:
        deltas = []
        for direction in (1 + pct, 1 - pct):
            A2 = dict(ASSUMPTIONS)
            A2[knob] = ASSUMPTIONS[knob] * direction
            deltas.append(month24_mrr(base_scenario, A2) - base_mrr)
        # also vary upsell take on the scenario itself and ad spend
        results.append({
            "input": knob,
            "low": round(min(deltas), 0),
            "high": round(max(deltas), 0),
            "swing": round(max(deltas) - min(deltas), 0),
        })
    # upsell take (scenario lever) +/- pct
    for direction, label in ((1 + pct, "up"), (1 - pct, "dn")):
        pass
    du = []
    for direction in (1 + pct, 1 - pct):
        sc2 = Scenario(**{**asdict_scenario(base_scenario), "upsell_take": base_scenario.upsell_take * direction})
        du.append(month24_mrr(sc2, ASSUMPTIONS) - base_mrr)
    results.append({"input": "upsell_take", "low": round(min(du), 0), "high": round(max(du), 0), "swing": round(max(du) - min(du), 0)})
    # ad spend +/- pct
    da = []
    for direction in (1 + pct, 1 - pct):
        sc2 = Scenario(**{**asdict_scenario(base_scenario), "ad_spend": {k: v * direction for k, v in base_scenario.ad_spend.items()}})
        da.append(month24_mrr(sc2, ASSUMPTIONS) - base_mrr)
    results.append({"input": "ad_spend", "low": round(min(da), 0), "high": round(max(da), 0), "swing": round(max(da) - min(da), 0)})

    results.sort(key=lambda r: r["swing"], reverse=True)
    return base_mrr, results


def asdict_scenario(sc: Scenario) -> dict:
    d = asdict(sc)
    return d


def setup_fee_sensitivity(sc: Scenario, fee_a=0.0, fee_b=297.0):
    """Compare worst drawdown & cumulative cash with $0 vs $fee_b setup fee."""
    out = {}
    for label, fee in (("setup_0", fee_a), ("setup_297", fee_b)):
        A2 = dict(ASSUMPTIONS)
        A2["setup_fee"] = fee
        rows, summ = simulate(sc, A2)
        out[label] = summ
    return out


# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────

CSV_COLS = ["month", "new_closes", "new_upsells", "entry_active", "upsold_active",
            "total_active", "mrr", "collections", "ad_spend", "tools", "team_cost",
            "cash_flow", "cum_cash", "cac_blended", "payback_months", "team_size",
            "cpl", "case_studies", "close_rate", "penetration", "metros"]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, "outputs")
    os.makedirs(out_dir, exist_ok=True)

    all_data = {"assumptions": ASSUMPTIONS, "horizon": HORIZON, "scenarios": {}}
    print(f"\n{'='*78}\nMED-SPA AGENCY — 24-MONTH SCENARIO MODEL\n{'='*78}")
    print(f"{'Scenario':<34}{'MRR m24':>11}{'Active m24':>11}{'Cum cash m24':>14}{'Worst draw':>13}")
    print("-" * 78)

    for sc in SCENARIOS:
        rows, summ = simulate(sc, ASSUMPTIONS)
        all_data["scenarios"][sc.key] = {
            "name": sc.name, "blurb": sc.blurb, "funnel_opt": sc.funnel_opt,
            "upsell_take": sc.upsell_take, "rows": rows, "summary": summ,
        }
        # CSV
        with open(os.path.join(out_dir, f"{sc.key}.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLS, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"{sc.name:<34}{summ['mrr_24']:>11,.0f}{summ['active_24']:>11,.1f}"
              f"{summ['cum_cash_24']:>14,.0f}{summ['worst_drawdown']:>13,.0f}")

    # Sensitivity (use Aggressive as the base for MRR sensitivity — most ad-driven)
    base = next(s for s in SCENARIOS if s.key == "aggressive")
    base_mrr, tornado = sensitivity_tornado(base)
    print(f"\n{'='*78}\nSENSITIVITY — which single input moves MONTH-24 MRR most  (base: {base.name}, ±20%)\n{'='*78}")
    print(f"base month-24 MRR: ${base_mrr:,.0f}")
    print(f"{'input':<20}{'MRR if -20%':>16}{'MRR if +20%':>16}{'swing':>14}")
    print("-" * 66)
    for r in tornado:
        print(f"{r['input']:<20}{base_mrr + r['low']:>16,.0f}{base_mrr + r['high']:>16,.0f}{r['swing']:>14,.0f}")

    # Setup fee sensitivity (Aggressive — deepest drawdown, so the fee matters most)
    print(f"\n{'='*78}\nSETUP-FEE SENSITIVITY — $0 vs $297  (base: {base.name})\n{'='*78}")
    sf = setup_fee_sensitivity(base)
    print(f"{'':<16}{'worst drawdown':>18}{'draw month':>12}{'cum cash m24':>16}")
    for label in ("setup_0", "setup_297"):
        s = sf[label]
        print(f"{label:<16}{s['worst_drawdown']:>18,.0f}{s['worst_drawdown_month']:>12}{s['cum_cash_24']:>16,.0f}")
    draw_relief = sf["setup_297"]["worst_drawdown"] - sf["setup_0"]["worst_drawdown"]
    cum_delta = sf["setup_297"]["cum_cash_24"] - sf["setup_0"]["cum_cash_24"]
    print(f"\n$297 setup fee reduces the worst drawdown by ${draw_relief:,.0f} "
          f"and changes month-24 cumulative cash by ${cum_delta:,.0f}.")
    # Break-even: the close-rate drag at which the $297 fee stops being net-negative on cum cash.
    breakeven_drag = None
    base_cum = sf["setup_0"]["cum_cash_24"]
    for i in range(0, 121):
        drag = i / 1000.0
        A3 = dict(ASSUMPTIONS); A3["setup_fee"] = 297.0; A3["setup_close_drag_at_297"] = drag
        _, s3 = simulate(base, A3)
        if s3["cum_cash_24"] < base_cum:
            breakeven_drag = drag
            break
    if breakeven_drag is not None:
        print(f"Break-even: a $297 setup fee is net-positive on 24-mo cash ONLY if it costs "
              f"< {breakeven_drag*100:.1f}% of your close rate. At the assumed 12% it is net-negative.")

    # Churn compounding: fraction of a cohort still paying after N months
    print(f"\n{'='*78}\nCHURN COMPOUNDS — % of a signed cohort still active after N months\n{'='*78}")
    print(f"{'churn/mo':>10}{'mo 6':>9}{'mo 12':>9}{'mo 18':>9}{'mo 24':>9}{'avg life':>11}")
    churn_curve = {}
    for c in (0.02, 0.03, 0.05):
        surv = 1 - c
        row = {n: round(surv ** n, 4) for n in range(0, 25)}
        churn_curve[f"{c:.2f}"] = row
        print(f"{c*100:>9.0f}%{surv**6:>9.1%}{surv**12:>9.1%}{surv**18:>9.1%}{surv**24:>9.1%}{1/c:>10.0f}mo")

    # Downside stress: what if real close rates are HALF of assumed?
    print(f"\n{'='*78}\nDOWNSIDE STRESS — real close rate = HALF of assumed (funnel is the risk, not cash)\n{'='*78}")
    A_stress = dict(ASSUMPTIONS)
    A_stress["close_0cs"] *= 0.5
    A_stress["close_3cs"] *= 0.5
    print(f"{'Scenario':<34}{'MRR m24 base':>14}{'MRR m24 half':>14}{'draw base':>12}{'draw half':>12}")
    stress = {}
    for sc in SCENARIOS:
        _, s_base = simulate(sc, ASSUMPTIONS)
        _, s_half = simulate(sc, A_stress)
        stress[sc.key] = {"mrr_base": s_base["mrr_24"], "mrr_half": s_half["mrr_24"],
                          "draw_base": s_base["worst_drawdown"], "draw_half": s_half["worst_drawdown"]}
        print(f"{sc.name:<34}{s_base['mrr_24']:>14,.0f}{s_half['mrr_24']:>14,.0f}"
              f"{s_base['worst_drawdown']:>12,.0f}{s_half['worst_drawdown']:>12,.0f}")

    all_data["sensitivity"] = {"base_scenario": base.key, "base_mrr": base_mrr, "tornado": tornado}
    all_data["setup_sensitivity"] = {"base_scenario": base.key, **sf,
                                     "drawdown_relief": round(draw_relief, 2)}
    all_data["setup_sensitivity"]["breakeven_drag"] = breakeven_drag
    all_data["setup_sensitivity"]["cum_delta"] = round(cum_delta, 2)
    all_data["churn_curve"] = churn_curve
    all_data["downside_stress"] = stress

    with open(os.path.join(out_dir, "all_scenarios.json"), "w") as f:
        json.dump(all_data, f, indent=None, separators=(",", ":"))
    print(f"\nWrote {len(SCENARIOS)} CSVs + all_scenarios.json to {out_dir}\n")


if __name__ == "__main__":
    main()
