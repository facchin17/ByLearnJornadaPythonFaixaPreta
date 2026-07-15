#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MED SPA AI-AUTOMATION AGENCY — 24-MONTH SCENARIO MODEL
======================================================
Solo founder, GoHighLevel-based, med spas only.
Entry tier $500/mo (no setup fee) -> upsell to $1,500/mo full system ~2 months
after close, once the ROI dashboard shows $5k+ recovered.

Everything you control lives in the ASSUMPTIONS block and the SCENARIOS block.
Change a number, rerun `python3 model.py`, and every table + chart + the HTML
report regenerate. When you paste real funnel data, overwrite the funnel dict.

Cohort engine: each month's closes form a cohort; churn compounds monthly on
every surviving cohort; the upsell fires on the survivors at cohort age 2.
No within-month circularity — case studies, saturation, and fatigue all read
last month's state.
"""
import csv, json, base64, io, os, math
from copy import deepcopy

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data");   os.makedirs(DATA, exist_ok=True)
CHARTS = os.path.join(HERE, "charts"); os.makedirs(CHARTS, exist_ok=True)

MONTHS = 24

# ----------------------------------------------------------------------------
# PALETTE (dataviz reference instance — light surface)
# ----------------------------------------------------------------------------
SURFACE   = "#fcfcfb"
INK       = "#0b0b0b"
INK2      = "#52514e"
MUTED     = "#898781"
GRID      = "#e1e0d9"
BASELINE  = "#c3c2b7"
GOOD      = "#0ca30c"
CRIT      = "#d03b3b"
# categorical slots in fixed order
CAT = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a", "#eb6834", "#4a3aa7", "#e34948"]

# ============================================================================
# 1. EDITABLE ASSUMPTIONS
# ============================================================================
A = {
    # ---- Pricing (monthly recurring) ----
    "price_entry":      500,    # database reactivation + review & referral
    "price_full":     1500,     # full system (missed-call, speed-to-lead, voice AI, ROI dash)
    "setup_fee":         0,     # baseline $0; setup-fee sensitivity flips this to 297

    # ---- Funnel (BASELINE = "level 2" optimization; scenarios shift by level) ----
    "cpl_base":         25.0,   # cost per Meta lead ($)
    "lead_to_booked":   0.32,   # lead -> booked demo
    "show_rate":        0.70,   # booked -> showed up
    "close_0cs":        0.20,   # close rate, cold traffic, 0 case studies
    "close_3cs":        0.35,   # close rate, cold traffic, 3+ case studies
    "cs_needed":        3,      # case studies to reach the top close rate
    "cs_capture":       0.50,   # share of survivable clients that become a usable case study
    "learning_mult":    1.40,   # month-1 CPL penalty (2-week algo learning phase)
    "fatigue_rate":     0.06,   # CPL creep per month since last creative refresh
    "sat_k":            2.50,   # CPL multiplier span as you fill the winnable metro
                                # (CPL ~1x empty -> ~3.5x at the cap; the hard cap does the rest)
    "pen_max":          0.35,   # realistic max share of a metro's med spas you can win
                                # over the horizon (~105 of 300). You will NOT sign 90%
                                # of a metro; competitors/DIY/no-budget/not-ready take the rest.

    # ---- Fixed business assumptions ----
    "churn":            0.03,   # monthly logo churn (compounds)
    "overwhelm_churn":  0.02,   # extra churn when actives exceed support capacity
    "upsell_lag":       2,      # months after close that the upsell offer lands
    "tools_base":       400.0,  # fixed tool floor ($/mo)
    "tools_per_client":  30.0,  # variable tool cost per active client ($/mo)  -> ~$700 at 10 clients

    # ---- Capacity ceilings ----
    "demo_cap_solo":    88,     # founder CLOSES personally; ~4 demos/day x 22 days
    "demo_cap_va":      22,     # VA owns booking/reminders -> founder does a few more closes
    "demo_cap_am":      22,     # AM owns fulfillment -> founder freed for a few more closes
    #  NOTE: the founder is the only closer in this model. Extra AMs add SUPPORT
    #  capacity, never closing capacity — so total demo throughput caps at
    #  88+22+22 = 132/mo. Past that you must hire a 2nd closer (not modeled;
    #  flagged as the bottleneck).
    "support_solo":     28,     # actives a solo founder can support before quality drops
    "support_per_am":   30,     # extra supported actives per account manager
    "fulfill_ceiling":  15,     # full-tier installs a solo founder can build/maintain

    # ---- Team costs ($/mo, fully loaded) ----
    "cost_va":         1200.0,
    "cost_media":      2800.0,
    "cost_am":         4500.0,

    # ---- Market ----
    "metro_size":       300,    # addressable med spas per metro (mid of 200-400)
}

# Optimization levels shift the funnel. Level 2 == the baseline above.
OPT = {
    1: {"book": 0.28, "show": 0.65, "cpl_factor": 1.00, "refresh": 4},  # sloppy: slow refresh
    2: {"book": 0.32, "show": 0.70, "cpl_factor": 1.12, "refresh": 2},  # disciplined
    3: {"book": 0.36, "show": 0.75, "cpl_factor": 1.22, "refresh": 2},  # dialed-in creative + targeting
}

# ============================================================================
# 2. SCENARIOS  (vary ONLY founder-controllable inputs)
# ============================================================================
def ramp(schedule):
    """schedule = list of (start_month, monthly_spend); returns f(month)->spend."""
    def f(m, state):
        s = 0.0
        for start, val in schedule:
            if m >= start:
                s = val
        return s
    return f

SCENARIOS = [
    {   # 1
        "name": "Ads-Only Conservative",
        "short": "Conservative",
        "color": CAT[0],
        "opt": 1,
        "spend": ramp([(1, 2000)]),
        "hire": {"va": False, "media": False, "am": False},
        "warm_per_mo": 0, "referral_rate": 0.0,
        "metros": {2: 1},            # month -> metros open (never expands)
        "premium_at_cs": None,
    },
    {   # 2
        "name": "Ads-Only Aggressive",
        "short": "Aggressive",
        "color": CAT[1],
        "opt": 2,
        "spend": ramp([(1, 3000), (4, 5000), (7, 8000), (13, 10000)]),
        "hire": {"va": True, "media": True, "am": True},
        "warm_per_mo": 0, "referral_rate": 0.0,
        "metros": {2: 1},
        "premium_at_cs": None,
    },
    {   # 3
        "name": "Hybrid (Ads + Warm + Referrals)",
        "short": "Hybrid",
        "color": CAT[2],
        "opt": 2,
        "spend": ramp([(1, 2500)]),
        "hire": {"va": True, "media": False, "am": True},
        "warm_per_mo": 2, "referral_rate": 0.08,   # 8% of actives refer a signed client/mo
        "metros": {2: 1},
        "premium_at_cs": None,
    },
    {   # 4
        "name": "Scale-With-Team",
        "short": "Team",
        "color": CAT[3],
        "opt": 2,
        "spend": ramp([(1, 3000), (5, 6000), (10, 9000)]),
        "hire": {"va": True, "media": True, "am": True},
        "warm_per_mo": 0, "referral_rate": 0.04,
        "metros": {2: 1},
        "premium_at_cs": None,
    },
    {   # 5
        "name": "Multi-Metro Expansion",
        "short": "Multi-Metro",
        "color": CAT[4],
        "opt": 2,
        "spend": ramp([(1, 4000), (9, 8000), (16, 12000)]),  # spend rises as metros open
        "hire": {"va": True, "media": True, "am": True},
        "warm_per_mo": 0, "referral_rate": 0.04,
        "metros": {2: 1, 9: 2, 16: 3},   # open metro 2 at m9, metro 3 at m16
        "premium_at_cs": None,
    },
    {   # 6
        "name": "Premium-Pricing (after 10+ case studies)",
        "short": "Premium",
        "color": CAT[5],
        "opt": 3,
        "spend": ramp([(1, 3000), (5, 5000), (11, 6000)]),
        "hire": {"va": True, "media": True, "am": True},
        "warm_per_mo": 0, "referral_rate": 0.05,
        "metros": {2: 1},
        "premium_at_cs": 10,               # raise both tiers once cumulative case studies >= 10
        "premium_entry": 750, "premium_full": 2000, "premium_close_mult": 0.85,
    },
    {   # 7
        "name": "Lean Cash-First (Bootstrap)",
        "short": "Lean",
        "color": CAT[6],
        "opt": 2,
        # spend is capped at 35% of last month's collections (reinvest profit only)
        "spend": None, "lean": True, "lean_start": 1000, "lean_reinvest": 0.35,
        "hire": {"va": True, "media": False, "am": True},
        "warm_per_mo": 1, "referral_rate": 0.06,
        "metros": {2: 1},
        "premium_at_cs": None,
    },
]

# ============================================================================
# 3. SIMULATION ENGINE
# ============================================================================
def simulate(scn, A=A, setup_fee=None):
    a = A
    opt = OPT[scn["opt"]]
    setup_fee = a["setup_fee"] if setup_fee is None else setup_fee

    cohorts = []            # each: {"entry": x, "upsold": y, "age": n}
    cum_signed = 0          # ever-signed (for penetration)
    case_studies = 0.0
    last_collections = 0.0
    premium_on = False
    fatigue_month = 0       # months since last refresh

    rows = []
    prev_active = 0
    for m in range(1, MONTHS + 1):
        # --- team state (triggers are NUMBERS) ---
        has_va = scn["hire"]["va"] and prev_active >= 12
        has_media = scn["hire"]["media"] and (
            (scn["spend"] and scn["spend"](m, None) >= 6000) or prev_active >= 20)
        # AM triggers at support ceiling OR fulfillment ceiling, then AMs scale
        # with the client load (one AM per `support_per_am` actives over the
        # solo ceiling) — supporting 150+ clients is not a one-AM job.
        prev_upsold = sum(c["upsold"] for c in cohorts)
        metros_open = _metros(scn, m)
        am_triggered = scn["hire"]["am"] and (
            prev_active >= 25 or prev_upsold >= a["fulfill_ceiling"] or metros_open > 1)
        if am_triggered:
            load_am = math.ceil(max(0.0, prev_active - a["support_solo"]) / a["support_per_am"])
            n_am = max(1, metros_open - 1, load_am)
        else:
            n_am = 0
        has_am = n_am >= 1

        # --- ad spend ---
        if scn.get("lean"):
            spend = scn["lean_start"] if m == 1 else min(
                scn["lean_start"] * 3, max(scn["lean_start"], scn["lean_reinvest"] * last_collections))
        else:
            spend = scn["spend"](m, None)

        # media buyer sharpens CPL
        cpl_factor = opt["cpl_factor"] + (0.10 if has_media else 0.0)

        # --- effective CPL ---
        # Saturation tracks CURRENT market share (active clients / addressable),
        # not gross cumulative signs — a churned med spa re-enters the prospect
        # pool, so the audience you advertise against is "med spas not currently
        # mine". As you hold more of the metro, remaining prospects cost more.
        learn = a["learning_mult"] if m == 1 else 1.0
        winnable = a["pen_max"] * a["metro_size"] * metros_open
        frac = min(0.999, prev_active / max(1.0, winnable))   # share of WINNABLE captured
        penetration = prev_active / max(1, a["metro_size"] * metros_open)
        sat = 1.0 + a["sat_k"] * frac        # CPL climbs linearly as the winnable metro fills
        refresh = opt["refresh"]
        fatigue_month = 0 if (m == 1 or fatigue_month + 1 > refresh) else fatigue_month + 1
        fatigue = 1.0 + a["fatigue_rate"] * fatigue_month
        cpl_eff = a["cpl_base"] * learn * sat * fatigue / cpl_factor

        # --- funnel to closes ---
        leads = spend / cpl_eff if cpl_eff > 0 else 0.0
        book = opt["book"]
        show = opt["show"] + (0.03 if has_va else 0.0)
        booked = leads * book
        demo_cap = a["demo_cap_solo"] + (a["demo_cap_va"] if has_va else 0) + \
                   (a["demo_cap_am"] if has_am else 0)
        demo_demand = booked * show
        demos_shown = min(demo_demand, demo_cap)
        closer_capped = demo_demand > demo_cap + 1e-6

        close = a["close_0cs"] + (a["close_3cs"] - a["close_0cs"]) * min(case_studies / a["cs_needed"], 1.0)
        if premium_on:
            close *= scn.get("premium_close_mult", 1.0)
        demand_ads = demos_shown * close        # closes the scheduled budget could buy

        # --- warm outreach + referrals (near-zero CAC) ---
        warm = scn.get("warm_per_mo", 0) if m <= 12 else scn.get("warm_per_mo", 0) * 0.5
        referrals = scn.get("referral_rate", 0.0) * prev_active

        # --- churn (needed by the spend governor below) ---
        support_cap = a["support_solo"] + n_am * a["support_per_am"]
        churn = a["churn"] + (a["overwhelm_churn"] if prev_active > support_cap else 0.0)

        # --- SPEND GOVERNOR (rational founder) ---------------------------------
        # You only pay for as many closes as the winnable market can still absorb
        # (refill to the cap + replace this month's churn). Past that you pause ads
        # instead of burning full budget to replace churn at an absurd CAC.
        remaining = max(0.0, winnable - prev_active)
        target = remaining + churn * prev_active            # gross adds to refill to cap
        free = min(warm + referrals, target)                # free adds (warm+referrals) first
        if warm + referrals > 1e-9:
            fscale = free / (warm + referrals)
            warm *= fscale; referrals *= fscale
        needed_ad = max(0.0, target - free)
        actual_ad = min(demand_ads, needed_ad)
        util = (actual_ad / demand_ads) if demand_ads > 1e-9 else 0.0
        spend *= util                                       # ads paused once quota filled
        leads *= util; booked *= util; demos_shown *= util
        new_from_ads = actual_ad
        new_total = new_from_ads + warm + referrals

        # --- pricing (premium switch) ---
        if scn.get("premium_at_cs") and not premium_on and case_studies >= scn["premium_at_cs"]:
            premium_on = True
        p_entry = scn.get("premium_entry", a["price_entry"]) if premium_on else a["price_entry"]
        p_full  = scn.get("premium_full",  a["price_full"])  if premium_on else a["price_full"]

        # === cohort update ===
        for c in cohorts:                     # 1) churn compounds
            c["entry"] *= (1 - churn)
            c["upsold"] *= (1 - churn)
            c["age"] += 1
        for c in cohorts:                     # 2) upsell fires at age == lag
            if c["age"] == a["upsell_lag"]:
                conv = c["entry"] * scn["_upsell_rate"]
                c["entry"] -= conv
                c["upsold"] += conv
        cohorts.append({"entry": new_total, "upsold": 0.0, "age": 0})  # 3) new cohort

        entry_active = sum(c["entry"] for c in cohorts)
        upsold_active = sum(c["upsold"] for c in cohorts)
        active = entry_active + upsold_active
        cum_signed += new_total

        # --- case studies accrue from clients that reached the upsell milestone ---
        matured = sum(c["entry"] + c["upsold"] for c in cohorts if c["age"] == a["upsell_lag"])
        case_studies += matured * a["cs_capture"]

        # --- economics ---
        mrr = entry_active * p_entry + upsold_active * p_full
        collections = mrr + new_total * setup_fee
        tools = a["tools_base"] + a["tools_per_client"] * active
        team = (a["cost_va"] if has_va else 0) + (a["cost_media"] if has_media else 0) + \
               n_am * a["cost_am"]
        cash_flow = collections - spend - tools - team

        cac_ads = spend / new_from_ads if new_from_ads > 0 else float("nan")
        cac_blended = spend / new_total if new_total > 0 else float("nan")
        gross_margin_client = p_entry - a["tools_per_client"]
        payback = cac_blended / gross_margin_client if new_total > 0 else float("nan")

        rows.append({
            "month": m, "spend": spend, "cpl_eff": cpl_eff, "leads": leads,
            "demos": demos_shown, "demo_cap": demo_cap, "closer_capped": closer_capped,
            "new_ads": new_from_ads, "warm": warm, "referrals": referrals, "new": new_total,
            "entry": entry_active, "upsold": upsold_active, "active": active,
            "case_studies": case_studies, "penetration": penetration,
            "mrr": mrr, "collections": collections, "tools": tools, "team": team,
            "cash_flow": cash_flow, "cac_ads": cac_ads, "cac": cac_blended, "payback": payback,
            "team_size": (1 if has_va else 0) + (1 if has_media else 0) + n_am,
            "has_va": has_va, "has_media": has_media, "n_am": n_am,
            "churn": churn, "close": close, "metros": metros_open,
            "p_entry": p_entry, "p_full": p_full, "premium_on": premium_on,
        })
        prev_active = active
        last_collections = collections

    # cumulative cash + drawdown
    cum = 0.0; worst = 0.0; worst_m = 0
    for r in rows:
        cum += r["cash_flow"]; r["cum_cash"] = cum
        if cum < worst:
            worst = cum; worst_m = r["month"]
    return {"rows": rows, "worst": worst, "worst_m": worst_m,
            "final_mrr": rows[-1]["mrr"], "final_active": rows[-1]["active"],
            "cum_cash_24": rows[-1]["cum_cash"]}


def _metros(scn, m):
    open_n = 1
    for mm, n in sorted(scn["metros"].items()):
        if m >= mm:
            open_n = n
    return open_n


# ============================================================================
# 4. RUN — three upsell-rate variants (33 / 45 / 60 %)
# ============================================================================
UPSELL_VARIANTS = {"low": 0.33, "mid": 0.45, "high": 0.60}

def run_all(upsell_key="mid", A=A, setup_fee=None):
    rate = UPSELL_VARIANTS[upsell_key]
    out = {}
    for scn in SCENARIOS:
        s = deepcopy(scn)
        s["_upsell_rate"] = rate
        out[scn["name"]] = simulate(s, A=A, setup_fee=setup_fee)
    return out


if __name__ == "__main__":
    results = {k: run_all(k) for k in UPSELL_VARIANTS}
    # write CSVs for the mid variant
    for name, res in results["mid"].items():
        slug = name.split(" (")[0].replace(" ", "_").replace("-", "").lower()
        with open(os.path.join(DATA, f"{slug}.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(res["rows"][0].keys()))
            w.writeheader()
            for r in res["rows"]:
                w.writerow(r)
    with open(os.path.join(DATA, "summary.json"), "w") as f:
        json.dump({k: {n: {"rows": r["rows"], "worst": r["worst"], "worst_m": r["worst_m"]}
                       for n, r in v.items()} for k, v in results.items()}, f, default=float)
    print("mid-variant month-24 snapshot")
    print(f"{'scenario':38} {'MRR':>9} {'active':>7} {'worst$':>10} {'@m':>3}")
    for scn in SCENARIOS:
        r = results["mid"][scn["name"]]
        print(f"{scn['short']:38} {r['final_mrr']:>9,.0f} {r['final_active']:>7.1f} "
              f"{r['worst']:>10,.0f} {r['worst_m']:>3}")
