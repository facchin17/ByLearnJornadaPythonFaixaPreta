#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Builds all charts (PNG + base64) and a single self-contained report.html
from model.py. Run:  python3 report.py
"""
import io, base64, os, math, html
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import model as M

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts"); os.makedirs(CHARTS, exist_ok=True)

# palette
SURFACE, INK, INK2, MUTED = M.SURFACE, M.INK, M.INK2, M.MUTED
GRID, BASELINE, GOOD, CRIT = M.GRID, M.BASELINE, M.GOOD, M.CRIT
CAT = M.CAT
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 11,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": BASELINE, "axes.linewidth": 1.0, "grid.color": GRID, "grid.linewidth": 1.0,
    "text.parse_math": False,   # render literal '$' in titles/labels, never math-mode
})

SCN = M.SCENARIOS
NAMES = [s["name"] for s in SCN]
SHORTS = [s["short"] for s in SCN]
COLORS = [s["color"] for s in SCN]
MONTHS = list(range(1, M.MONTHS + 1))

RESULTS = {k: M.run_all(k) for k in M.UPSELL_VARIANTS}
MID = RESULTS["mid"]


def b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def savepng(fig, name):
    fig.savefig(os.path.join(CHARTS, name), dpi=150, bbox_inches="tight")


def money(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    a = abs(v)
    if a >= 1_000_000:
        return f"${v/1e6:.2f}M"
    if a >= 1000:
        return f"${v/1e3:.1f}k"
    return f"${v:,.0f}"


# ---------------------------------------------------------------------------
# CHART A — 3D surface: X=month, Y=scenario, Z=MRR
# ---------------------------------------------------------------------------
def chart_3d():
    fig = plt.figure(figsize=(11, 7))
    ax = fig.add_subplot(111, projection="3d")
    Z = np.array([[MID[n]["rows"][m]["mrr"] for m in range(M.MONTHS)] for n in NAMES])
    X, Y = np.meshgrid(np.array(MONTHS), np.arange(len(NAMES)))
    surf = ax.plot_surface(X, Y, Z, cmap="Blues", edgecolor=INK2, linewidth=0.25,
                           rstride=1, cstride=1, antialiased=True, alpha=0.96)
    # overlay each scenario ridge in its categorical color
    for i, n in enumerate(NAMES):
        z = [MID[n]["rows"][m]["mrr"] for m in range(M.MONTHS)]
        ax.plot(MONTHS, [i]*M.MONTHS, z, color=COLORS[i], lw=2.2)
    ax.set_xlabel("Month", labelpad=10, color=INK2)
    ax.set_ylabel("")
    ax.set_zlabel("MRR", labelpad=14, color=INK2)
    ax.set_yticks(np.arange(len(NAMES)))
    ax.set_yticklabels(SHORTS, fontsize=9)
    ax.zaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v/1000:.0f}k"))
    ax.set_xticks([1, 6, 12, 18, 24])
    ax.view_init(elev=24, azim=-56)
    ax.set_title("MRR surface — month × scenario × MRR  (45% upsell)", color=INK, pad=8, fontsize=13)
    ax.xaxis.pane.set_facecolor(SURFACE); ax.yaxis.pane.set_facecolor(SURFACE); ax.zaxis.pane.set_facecolor(SURFACE)
    ax.xaxis.pane.set_edgecolor(GRID); ax.yaxis.pane.set_edgecolor(GRID); ax.zaxis.pane.set_edgecolor(GRID)
    ax.grid(True)
    savepng(fig, "chart_3d_mrr.png")
    return b64(fig)


# ---------------------------------------------------------------------------
# generic multi-line chart
# ---------------------------------------------------------------------------
def line_chart(getter, title, ylabel, yfmt, fname, hline=None, hlabel=None, converge_note=None):
    fig, ax = plt.subplots(figsize=(11.2, 5.6))
    handles = []
    for i, n in enumerate(NAMES):
        y = [getter(MID[n]["rows"][m]) for m in range(M.MONTHS)]
        ax.plot(MONTHS, y, color=COLORS[i], lw=2.2, solid_capstyle="round")
        ax.plot(MONTHS[-1], y[-1], "o", color=COLORS[i], ms=6,
                markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=5)
        handles.append(plt.Line2D([0], [0], color=COLORS[i], lw=2.6, label=SHORTS[i]))
    if hline is not None:
        ax.axhline(hline, color=BASELINE, lw=1.2, ls=(0, (4, 3)))
        ax.annotate(hlabel, (1, hline), color=MUTED, fontsize=8.5, va="bottom")
    if converge_note:
        yv, txt = converge_note
        ax.annotate(txt, (12.5, yv), color=INK2, fontsize=8.2, va="center", ha="center",
                    bbox=dict(boxstyle="round,pad=0.3", fc=SURFACE, ec=GRID, lw=0.8))
    ax.set_title(title, color=INK, fontsize=13, pad=8, loc="left")
    ax.set_xlabel("Month", color=INK2); ax.set_ylabel(ylabel, color=INK2)
    ax.set_xticks([1, 3, 6, 9, 12, 15, 18, 21, 24]); ax.set_xlim(1, 24.6)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(yfmt))
    ax.grid(True, axis="y"); ax.grid(False, axis="x")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(handles=handles, fontsize=8.6, frameon=False, loc="upper left",
              bbox_to_anchor=(1.01, 1.0), handlelength=1.4, labelspacing=0.6)
    savepng(fig, fname)
    return b64(fig)


# ---------------------------------------------------------------------------
# CHART D — cumulative cash with worst-drawdown markers
# ---------------------------------------------------------------------------
def chart_cumcash():
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    handles = []
    for i, n in enumerate(NAMES):
        y = [MID[n]["rows"][m]["cum_cash"] for m in range(M.MONTHS)]
        ax.plot(MONTHS, y, color=COLORS[i], lw=2.2)
        ax.plot(MONTHS[-1], y[-1], "o", color=COLORS[i], ms=6,
                markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=5)
        handles.append(plt.Line2D([0], [0], color=COLORS[i], lw=2.6, label=SHORTS[i]))
    ax.axhline(0, color=BASELINE, lw=1.2)
    ax.set_title("Cumulative cash (founder take-home before pay)  —  45% upsell",
                 color=INK, fontsize=13, pad=8, loc="left")
    ax.set_xlabel("Month", color=INK2); ax.set_ylabel("Cumulative $", color=INK2)
    ax.set_xticks([1, 3, 6, 9, 12, 15, 18, 21, 24]); ax.set_xlim(1, 24.6)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v/1e6:.1f}M" if abs(v) >= 1e6 else f"${v/1e3:.0f}k"))
    ax.grid(True, axis="y"); ax.grid(False, axis="x")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(handles=handles, fontsize=8.6, frameon=False, loc="upper left",
              bbox_to_anchor=(1.01, 1.0), handlelength=1.4, labelspacing=0.6)
    fig.set_size_inches(11.2, 5.6)
    savepng(fig, "chart_cumcash.png")
    return b64(fig)


# ---------------------------------------------------------------------------
# CHART — worst drawdown zoom (the honest cash-valley picture, m1-6)
# ---------------------------------------------------------------------------
def chart_valley():
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    for i, n in enumerate(NAMES):
        y = [MID[n]["rows"][m]["cum_cash"] for m in range(6)]
        ax.plot(range(1, 7), y, color=COLORS[i], lw=2.2, marker="o", ms=4,
                markeredgecolor=SURFACE, markeredgewidth=1)
    ax.axhline(0, color=BASELINE, lw=1.2)
    worst = min(MID[n]["worst"] for n in NAMES)
    ax.set_title(f"The cash valley is shallow — months 1–6 cumulative cash "
                 f"(deepest hole ≈ {money(worst)})", color=INK, fontsize=12.5, pad=8, loc="left")
    ax.set_xlabel("Month", color=INK2); ax.set_ylabel("Cumulative $", color=INK2)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v/1e3:.0f}k"))
    ax.grid(True, axis="y"); ax.grid(False, axis="x")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    lg = [plt.Line2D([0], [0], color=COLORS[i], lw=2.4, label=SHORTS[i]) for i in range(len(NAMES))]
    ax.legend(handles=lg, fontsize=8.5, ncol=4, frameon=False, loc="lower right")
    savepng(fig, "chart_valley.png")
    return b64(fig)


# ---------------------------------------------------------------------------
# SENSITIVITY — tornado on month-24 MRR for a reference scenario
# ---------------------------------------------------------------------------
def m24_mrr(scn_name, A_over=None, upsell=None, close3=None):
    from copy import deepcopy
    scn = deepcopy(next(s for s in SCN if s["name"] == scn_name))
    scn["_upsell_rate"] = upsell if upsell is not None else 0.45
    A = deepcopy(M.A)
    if A_over:
        A.update(A_over)
    res = M.simulate(scn, A=A)
    return res["rows"][-1]["mrr"]


def sensitivity(ref="Ads-Only Aggressive"):
    base = m24_mrr(ref)
    # (label, low_call, high_call, low_desc, high_desc)
    levers = [
        ("Upsell take-rate\n33% ↔ 60%",       m24_mrr(ref, upsell=0.33),               m24_mrr(ref, upsell=0.60),               "33%", "60%"),
        ("Monthly churn\n4% ↔ 2%",            m24_mrr(ref, A_over={"churn": 0.04}),     m24_mrr(ref, A_over={"churn": 0.02}),     "4%", "2%"),
        ("Winnable metro share\n0.28 ↔ 0.42", m24_mrr(ref, A_over={"pen_max": 0.28}),   m24_mrr(ref, A_over={"pen_max": 0.42}),   "28%", "42%"),
        ("Both prices\n−20% ↔ +20%",          m24_mrr(ref, A_over={"price_entry": 400, "price_full": 1200}),
                                              m24_mrr(ref, A_over={"price_entry": 600, "price_full": 1800}), "−20%", "+20%"),
        ("Cost per lead\n$32 ↔ $18",          m24_mrr(ref, A_over={"cpl_base": 32}),    m24_mrr(ref, A_over={"cpl_base": 18}),    "$32", "$18"),
        ("Close rate (3+ CS)\n28% ↔ 42%",     m24_mrr(ref, A_over={"close_3cs": 0.28}), m24_mrr(ref, A_over={"close_3cs": 0.42}), "28%", "42%"),
        ("Lead→booked\n26% ↔ 38%",            m24_mrr(ref, A_over={"lead_to_booked": 0.26}), m24_mrr(ref, A_over={"lead_to_booked": 0.38}), "26%", "38%"),
    ]
    # rank by absolute swing
    levers.sort(key=lambda x: abs(x[2] - x[1]))
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    y = np.arange(len(levers))
    for i, (lab, lo, hi, ld, hd) in enumerate(levers):
        left, right = min(lo, hi), max(lo, hi)
        ax.barh(i, right - base, left=base, color=CAT[0], alpha=0.9, height=0.34,
                edgecolor=SURFACE, zorder=3)
        ax.barh(i, left - base, left=base, color=CAT[5], alpha=0.9, height=0.34,
                edgecolor=SURFACE, zorder=3)
        ax.text(left - 400, i, money(left), va="center", ha="right", fontsize=8, color=INK2)
        ax.text(right + 400, i, money(right), va="center", ha="left", fontsize=8, color=INK2)
    ax.axvline(base, color=INK, lw=1.4, zorder=4)
    ax.text(base, -0.85, f"baseline {money(base)}", color=INK, fontsize=8.5,
            va="top", ha="center")
    ax.set_yticks(y); ax.set_yticklabels([l[0] for l in levers], fontsize=8.5)
    ax.set_title(f"Sensitivity of month-24 MRR — {ref} (single metro)",
                 color=INK, fontsize=12.5, pad=8, loc="left")
    ax.set_xlabel("", color=INK2)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v/1e3:.0f}k"))
    ax.grid(True, axis="x"); ax.grid(False, axis="y")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    lg = [plt.Line2D([0], [0], color=CAT[5], lw=8, label="downside input"),
          plt.Line2D([0], [0], color=CAT[0], lw=8, label="upside input")]
    ax.legend(handles=lg, fontsize=8.5, frameon=False, loc="lower right")
    savepng(fig, "chart_sensitivity.png")
    ranked = [(l[0].replace("\n", " "), l[1], l[2], abs(l[2] - l[1])) for l in reversed(levers)]
    return b64(fig), base, ranked


# ---------------------------------------------------------------------------
# SETUP-FEE sensitivity — worst drawdown $0 vs $297
# ---------------------------------------------------------------------------
def setup_fee_compare():
    from copy import deepcopy
    rows = []
    for scn in SCN:
        r0 = M.simulate({**deepcopy(scn), "_upsell_rate": 0.45}, setup_fee=0)
        r2 = M.simulate({**deepcopy(scn), "_upsell_rate": 0.45}, setup_fee=297)
        rows.append((scn["short"], r0["worst"], r2["worst"],
                     r0["rows"][0]["cash_flow"], r2["rows"][0]["cash_flow"]))
    fig, ax = plt.subplots(figsize=(10.5, 5.0))
    x = np.arange(len(rows)); w = 0.38
    ax.bar(x - w/2, [r[1] for r in rows], w, color=CAT[5], label="$0 setup", edgecolor=SURFACE)
    ax.bar(x + w/2, [r[2] for r in rows], w, color=CAT[0], label="$297 setup", edgecolor=SURFACE)
    ax.axhline(0, color=BASELINE, lw=1.2)
    for i, r in enumerate(rows):
        ax.text(i - w/2, r[1] - 60, money(r[1]), ha="center", va="top", fontsize=7.5, color=INK2)
        ax.text(i + w/2, r[2] + 40, money(r[2]), ha="center", va="bottom", fontsize=7.5, color=INK2)
    ax.set_ylim(top=260)   # headroom so the near-zero $297 labels clear the title
    ax.set_xticks(x); ax.set_xticklabels([r[0] for r in rows], fontsize=8.5, rotation=12)
    ax.set_title("Worst cash drawdown: $0 setup vs $297 setup fee (45% upsell)",
                 color=INK, fontsize=12.5, pad=8, loc="left")
    ax.set_ylabel("Deepest cumulative-cash hole", color=INK2)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.grid(True, axis="y"); ax.grid(False, axis="x")
    ax.legend(fontsize=9, frameon=False, loc="lower right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    savepng(fig, "chart_setupfee.png")
    return b64(fig), rows


# ---------------------------------------------------------------------------
# BUILD
# ---------------------------------------------------------------------------
print("rendering charts…")
IMG_3D = chart_3d()
IMG_ACTIVE = line_chart(lambda r: r["active"], "Active clients per scenario  (45% upsell)",
                        "Active clients", lambda v, _: f"{v:.0f}", "chart_active_clients.png",
                        hline=M.A["pen_max"]*M.A["metro_size"], hlabel=" single-metro ceiling ≈ 105",
                        converge_note=(118, "Aggressive · Hybrid · Team\n· Premium · Lean all cap ≈105"))
IMG_MRR = line_chart(lambda r: r["mrr"], "MRR per scenario  (45% upsell)", "MRR",
                     lambda v, _: f"${v/1e3:.0f}k", "chart_mrr_lines.png",
                     converge_note=(97000, "4 paths converge\n≈ $97k (single metro)"))
IMG_CUM = chart_cumcash()
IMG_VALLEY = chart_valley()
IMG_SENS, SENS_BASE, SENS_RANK = sensitivity()
IMG_SETUP, SETUP_ROWS = setup_fee_compare()
print("charts done. writing report.html…")

# ---- helper builders for HTML ----
def scn_table(n):
    rows = MID[n]["rows"]
    head = ["Mo", "New", "Entry", "Upsold", "Active", "MRR", "Cash flow", "Cum cash",
            "CAC", "Payback", "Team", "CPL"]
    trs = []
    for r in rows:
        pay = "—" if math.isnan(r["payback"]) else f"{r['payback']:.1f}mo"
        cac = "—" if math.isnan(r["cac"]) else f"${r['cac']:,.0f}"
        neg = ' class="neg"' if r["cash_flow"] < 0 else ""
        trs.append(
            f"<tr><td>{r['month']}</td><td>{r['new']:.1f}</td><td>{r['entry']:.0f}</td>"
            f"<td>{r['upsold']:.0f}</td><td><b>{r['active']:.0f}</b></td>"
            f"<td>${r['mrr']:,.0f}</td><td{neg}>${r['cash_flow']:,.0f}</td>"
            f"<td>${r['cum_cash']:,.0f}</td><td>{cac}</td><td>{pay}</td>"
            f"<td>{r['team_size']}</td><td>${r['cpl_eff']:.0f}</td></tr>")
    return ("<table class='mt'><thead><tr>" + "".join(f"<th>{h}</th>" for h in head) +
            "</tr></thead><tbody>" + "".join(trs) + "</tbody></table>")


def summary_cards():
    cells = []
    for scn in SCN:
        n = scn["name"]; r = MID[n]
        last = r["rows"][-1]
        hit = next((row["month"] for row in r["rows"] if row["active"] >= 104), None)
        hit_txt = f"hits ceiling m{hit}" if hit else "never saturates"
        cells.append(f"""
        <div class="card" style="border-top:3px solid {scn['color']}">
          <div class="card-name">{html.escape(scn['name'])}</div>
          <div class="big">{money(last['mrr'])}<span class="unit">/mo MRR · m24</span></div>
          <div class="kv"><span>Active clients</span><b>{last['active']:.0f}</b></div>
          <div class="kv"><span>Upsold share</span><b>{100*last['upsold']/max(last['active'],1e-9):.0f}%</b></div>
          <div class="kv"><span>Worst drawdown</span><b>{money(r['worst'])} @m{r['worst_m']}</b></div>
          <div class="kv"><span>24-mo cash</span><b>{money(last['cum_cash'])}</b></div>
          <div class="kv"><span>Team @ m24</span><b>{last['team_size']} hire(s)</b></div>
          <div class="note">{hit_txt}</div>
        </div>""")
    return "\n".join(cells)


# ---------------------------------------------------------------------------
# PROSE DATA
# ---------------------------------------------------------------------------
CEIL = int(M.A["pen_max"] * M.A["metro_size"])
WORST_ALL = min(MID[n]["worst"] for n in NAMES)

FUNNEL_ROWS = [
    ("Cost per lead (CPL)", "$25", "Meta lead ads, med-spa niche. Rises with metro saturation (→ ~$79 at the single-metro cap)."),
    ("Lead → booked demo", "32%", "Booking funnel + 5-min callback. 28% sloppy / 36% dialed-in."),
    ("Cost per booked demo", "≈ $78", "= CPL ÷ (lead→booked). Derived, not independent."),
    ("Show rate", "70%", "Reminders before every demo. +3pts once a VA owns reminders."),
    ("Cost per show", "≈ $112", "= cost-per-booked ÷ show rate. Derived."),
    ("Close rate — 0 case studies", "20%", "Cold traffic, launch. This is the tax on being new."),
    ("Close rate — 3+ case studies", "35%", "Ramps in as you bank proof (½ of maturing clients → a usable case study)."),
    ("Algorithm learning phase", "×1.4 CPL, month 1 only", "First 2 weeks Meta is guessing; month-1 leads cost ~40% more."),
    ("Creative fatigue / refresh", "+6% CPL per month, reset on refresh", "Disciplined = refresh every 2 mo; sloppy = every 4 mo (CPL drifts +24%)."),
]
FIXED_ROWS = [
    ("Entry price", "$500/mo", "Reactivation + review & referral. $0 setup fee (baseline)."),
    ("Full-system price", "$1,500/mo", "Upgrade tier — replaces entry, not additive."),
    ("Upsell take rate", "45% (33 / 45 / 60% modeled)", "Fires 2 months after close, once ROI dashboard shows $5k+ recovered."),
    ("Monthly churn", "3%", "Compounds. At 3%/mo you lose 31% of any cohort over 12 months, 52% over 24."),
    ("Tool cost", "$400 base + $30/active", "≈ $700/mo at 10 clients, ≈ $3,550/mo at 105 (GHL sub-accounts, Twilio, AI)."),
    ("Solo fulfillment ceiling", "15 full-tier installs", "Forces the first account-manager hire."),
    ("Solo support ceiling", "28 active clients", "Past it, quality slips → +2%/mo overwhelm churn until you hire."),
    ("Founder-closer ceiling", "132 demos/mo (~6 closes/day)", "88 solo +22 with VA +22 with AM. Never binds — saturation caps leads first."),
    ("Addressable / metro", "300 med spas; 35% winnable", f"Realistic ceiling ≈ {CEIL} active clients per metro. You will not sign 90% of a metro."),
]

def churn_curve():
    pts = [(m, (1-M.A["churn"])**m) for m in (6, 12, 18, 24)]
    return " · ".join(f"{m}mo: {p*100:.0f}% left" for m, p in pts)

# per-scenario phase playbooks (actions / bottleneck / trigger — triggers are NUMBERS)
PLAYBOOKS = [
 {"name":"Ads-Only Conservative","color":CAT[0],"idea":"Flat $2k/mo, no hires, one metro. The floor case — deliberately under-throttled.",
  "phases":[
    ("0 → 5 clients","Ship 1 creative angle, 5-min callback on every lead, run 3–4 demos/day yourself, bank the first 3 case studies.","Zero proof → 20% close.","—"),
    ("5 → 15","Turn on review/referral automation for every client; screenshot every ROI-dashboard win.","Your fulfillment hours.","Nothing hired by design."),
    ("15 → 30","You cross the 28-client solo support ceiling here → +2% overwhelm churn kicks in and caps you.","Support load; you refuse to hire.","(Would-be) VA at 12; you skip it."),
    ("30+","Plateau ~39 active / ~$35k MRR. $2k/mo can't out-run churn on a bigger base.","Under-spend + no leverage.","None — this path tops out."),
  ]},
 {"name":"Ads-Only Aggressive","color":CAT[1],"idea":"Ramp spend $3k→$10k, hire on triggers, dominate one metro fast.",
  "phases":[
    ("0 → 5","2–3 creative angles live, 5-min callback, 4–5 demos/day. Push to 3 case studies by month 3.","Learning phase + no proof.","—"),
    ("5 → 15","Raise spend to $5k at month 4. Systematize onboarding so installs don't eat every hour.","Fulfillment time.","VA at 12 active ($1,200)."),
    ("15 → 30","Spend $8k. Hire media buyer + first AM. Close rate now 35% (proof banked).","Support crosses 28 → must hire.","Media buyer at $6k spend; AM at 25 active / 15 installs."),
    ("30+","Reach ~105 active by ~m15, then CPL saturates. Auto-throttle spend to ~$3k maintenance — full budget is now waste.","Metro saturation (~105 cap).","Cut spend or expand: metro-2 trigger = 90 active."),
  ]},
 {"name":"Hybrid (Ads + Warm + Referrals)","color":CAT[2],"idea":"$2.5k ads + 2 founder-outreach/mo + referral engine (8% of actives refer). Lowest blended CAC.",
  "phases":[
    ("0 → 5","Ads + hand-pick 2 warm med spas/mo from your network. Referral automation on from client #1.","Proof, but warm closes faster.","—"),
    ("5 → 15","Referrals compound: 8% of actives send a signed client/mo at ~$0 CAC. Blended CAC falls to ~$200.","Fulfillment time.","VA at 12 active."),
    ("15 → 30","Referral flywheel does the heavy lifting; ads become top-up. Cheapest cash build here.","Support ceiling.","AM at 25 active / 15 installs."),
    ("30+","Same ~105 single-metro ceiling — but you got there on the least cash (worst drawdown only −$276).","Metro saturation.","Metro-2 trigger = 90 active."),
  ]},
 {"name":"Scale-With-Team","color":CAT[3],"idea":"Hire ahead into the ceiling so ops never caps you. Same endpoint as Aggressive, more resilient.",
  "phases":[
    ("0 → 5","Standard launch. Document every SOP from day 1 so a VA can take it.","Proof + your calendar.","—"),
    ("5 → 15","Spend $6k at month 5. VA owns booking/reminders/CRM (show rate +3pts).","Booking + admin drag.","VA at 12; media buyer at $6k spend."),
    ("15 → 30","AM owns fulfillment before the 15-install ceiling bites. Founder stays on closes only.","Fulfillment ceiling (15 installs).","AM at 15 installs / 25 active."),
    ("30+","One AM per +30 actives keeps churn at baseline 3%. Endpoint ~105 / ~$97k, team cost ~$9–13k/mo.","Metro saturation.","+1 AM per +30 active; metro-2 at 90."),
  ]},
 {"name":"Multi-Metro Expansion","color":CAT[4],"idea":"Saturate metro 1, then open 2 and 3. The ONLY path past ~$100k MRR without raising price.",
  "phases":[
    ("0 → 5","Win metro 1 exactly like Aggressive. Keep creatives/offers documented to clone into metro 2.","Proof.","—"),
    ("5 → 15","Build the team that makes a metro copy-pasteable (VA + first AM).","Fulfillment.","VA at 12; AM at 25 active."),
    ("15 → 30 (per metro)","At 90 active in metro 1, open metro 2 with fresh $4–8k spend (CPL resets low). Dedicated AM per metro.","Ops replication + your closing time.","Open metro-2 at 90 active; +1 AM per new metro."),
    ("30+ / 3 metros","m24 ≈ 315 active / ~$282k MRR. Now the founder-closer (132 demos/mo) is the next wall.","Closer throughput across metros.","Hire a 2nd closer when demos booked > 120/mo; metro-3 at 90 active in metro 2."),
  ]},
 {"name":"Premium-Pricing","color":CAT[5],"idea":"Raise entry $500→$750 and full $1,500→$2,000 once you hold 10 case studies. Same clients, +38% MRR.",
  "phases":[
    ("0 → 5","Launch at standard price. Obsess over documented ROI ($5k+ recovered) — the case studies ARE the pricing power.","Proof volume.","—"),
    ("5 → 15","At 10 case studies (~month 6) raise both tiers. Close rate dips ~15% but revenue/client jumps.","Nerve to raise price.","Price raise at 10 case studies."),
    ("15 → 30","Higher price = higher CAC tolerance and better-fit clients (lower churn in practice).","Support ceiling.","AM at 25 active / 15 installs."),
    ("30+","Same ~105-client ceiling, but at ~$134k MRR vs $97k — the highest single-metro outcome.","Metro saturation.","Metro-2 at 90 active."),
  ]},
 {"name":"Lean Cash-First","color":CAT[6],"idea":"Reinvest only 35% of collections into ads (start $1k). Near-zero cash risk, ~same endpoint, a few months slower.",
  "phases":[
    ("0 → 5","$1k/mo ads, 1 warm outreach/mo, referral automation on. Every dollar of profit is yours.","Slow lead volume.","—"),
    ("5 → 15","Ad budget self-funds as collections grow (caps at 3× the start). Drawdown never exceeds −$256.","Growth rate, not cash.","VA at 12 active."),
    ("15 → 30","Compounds into the ceiling anyway — profit reinvestment is enough to fill one metro.","Support ceiling.","AM at 25 active."),
    ("30+","m24 ≈ 105 active / ~$97k MRR — identical endpoint to Aggressive, reached ~4–6 months later, with the safest balance sheet of any path.","Metro saturation.","Metro-2 at 90 active."),
  ]},
]

# cadence per scenario (derived)
def cadence_rows():
    out = []
    for scn in SCN:
        rows = MID[scn["name"]]["rows"]
        peak_demos = max(r["demos"] for r in rows)
        peak_leads = max(r["leads"] for r in rows)
        refresh = M.OPT[scn["opt"]]["refresh"]
        cr_wk = {4: "2–3", 2: "4–6"}[refresh] if scn["opt"] < 3 else "6–8"
        out.append((scn["short"], f"{peak_leads/22:.0f}", f"{peak_demos/22:.1f}", cr_wk,
                    scn["color"]))
    return out


# ---------------------------------------------------------------------------
# ASSEMBLE report.html  (self-contained; base64 charts; theme-aware chrome)
# ---------------------------------------------------------------------------
def img(b, alt):
    return f'<img src="data:image/png;base64,{b}" alt="{html.escape(alt)}" loading="lazy">'

def tbl(rows, headers):
    h = "".join(f"<th>{html.escape(x)}</th>" for x in headers)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
    return f"<table class='ref'><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table>"

# ---- exec findings (dynamic) ----
agg = MID["Ads-Only Aggressive"]["rows"][-1]
multi = MID["Multi-Metro Expansion"]["rows"][-1]
prem = MID["Premium-Pricing (after 10+ case studies)"]["rows"][-1]
cons = MID["Ads-Only Conservative"]["rows"][-1]
top_lever = SENS_RANK[0]

CSS = """
:root{
 --bg:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
 --grid:#e1e0d9; --line:#c3c2b7; --good:#006300; --crit:#d03b3b; --accent:#2a78d6;
 --card:#ffffff; --shadow:0 1px 2px rgba(11,11,11,.06),0 1px 10px rgba(11,11,11,.04);
 --chip:#eef4fd;
}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme=light])){
 --bg:#0d0d0d; --surface:#1a1a19; --ink:#fff; --ink2:#c3c2b7; --muted:#898781;
 --grid:#2c2c2a; --line:#383835; --good:#0ca30c; --crit:#e66767; --accent:#3987e5;
 --card:#161615; --shadow:none; --chip:#17233a;}}
:root[data-theme=dark]{
 --bg:#0d0d0d; --surface:#1a1a19; --ink:#fff; --ink2:#c3c2b7; --muted:#898781;
 --grid:#2c2c2a; --line:#383835; --good:#0ca30c; --crit:#e66767; --accent:#3987e5;
 --card:#161615; --shadow:none; --chip:#17233a;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5;font-size:15px}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:30px;line-height:1.15;margin:0 0 6px}
h2{font-size:22px;margin:52px 0 4px;padding-top:14px;border-top:1px solid var(--grid)}
h3{font-size:17px;margin:26px 0 8px}
.sub{color:var(--ink2);font-size:15px;margin:0 0 8px}
.tag{display:inline-block;font-size:12px;color:var(--ink2);background:var(--chip);
 border-radius:999px;padding:3px 11px;margin:2px 4px 2px 0}
p{margin:10px 0}
a{color:var(--accent)}
.callout{background:var(--card);border:1px solid var(--grid);border-left:4px solid var(--accent);
 border-radius:10px;padding:18px 20px;margin:18px 0;box-shadow:var(--shadow)}
.callout ol{margin:8px 0 0;padding-left:20px}
.callout li{margin:8px 0}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(232px,1fr));gap:14px;margin:18px 0}
.card{background:var(--card);border:1px solid var(--grid);border-radius:12px;padding:14px 15px;box-shadow:var(--shadow)}
.card-name{font-weight:650;font-size:13.5px;min-height:34px;line-height:1.25}
.big{font-size:23px;font-weight:700;margin:6px 0 10px;font-variant-numeric:tabular-nums}
.unit{font-size:12px;font-weight:400;color:var(--muted);margin-left:5px}
.kv{display:flex;justify-content:space-between;font-size:12.5px;color:var(--ink2);padding:2.5px 0}
.kv b{color:var(--ink);font-variant-numeric:tabular-nums}
.note{margin-top:9px;font-size:11.5px;color:var(--muted);border-top:1px dashed var(--grid);padding-top:7px}
figure{margin:20px 0;background:var(--surface);border:1px solid var(--grid);border-radius:12px;
 padding:12px;box-shadow:var(--shadow);overflow-x:auto}
figure img{width:100%;height:auto;display:block;border-radius:6px;min-width:640px}
figcaption{color:var(--ink2);font-size:13px;margin-top:8px;padding:0 4px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:760px){.two{grid-template-columns:1fr}}
table{border-collapse:collapse;width:100%;font-size:13px}
table.ref td,table.ref th{border-bottom:1px solid var(--grid);padding:8px 10px;text-align:left;vertical-align:top}
table.ref th{color:var(--ink2);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.03em}
table.ref td:first-child{font-weight:600;white-space:nowrap}
table.ref td:nth-child(2){font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--accent);font-weight:600}
.mtwrap{overflow-x:auto;border:1px solid var(--grid);border-radius:10px;margin:8px 0}
table.mt{font-size:12px;font-variant-numeric:tabular-nums;min-width:720px}
table.mt th,table.mt td{padding:5px 9px;text-align:right;border-bottom:1px solid var(--grid);white-space:nowrap}
table.mt th{position:sticky;top:0;background:var(--surface);color:var(--ink2);font-size:11px;text-align:right}
table.mt td:first-child,table.mt th:first-child{text-align:center;color:var(--muted)}
table.mt td.neg{color:var(--crit)}
details{background:var(--card);border:1px solid var(--grid);border-radius:10px;margin:10px 0;box-shadow:var(--shadow)}
summary{cursor:pointer;padding:12px 16px;font-weight:600;font-size:14.5px;list-style:none;display:flex;justify-content:space-between;align-items:center}
summary::-webkit-details-marker{display:none}
summary::after{content:"▸";color:var(--muted);font-size:13px}
details[open] summary::after{content:"▾"}
details .inner{padding:0 16px 16px}
.pb{background:var(--card);border:1px solid var(--grid);border-radius:12px;padding:16px 18px;margin:14px 0;box-shadow:var(--shadow)}
.pb-head{font-weight:700;font-size:16px}
.pb-idea{color:var(--ink2);font-size:13.5px;margin:4px 0 12px}
.phase{border-left:3px solid var(--pc);padding:2px 0 2px 14px;margin:12px 0}
.phase .pt{font-weight:650;font-size:14px}
.phase .pa{font-size:13.5px;margin:3px 0}
.phase .meta{font-size:12.5px;color:var(--ink2);margin-top:4px}
.phase .meta .b{color:var(--crit);font-weight:600}
.phase .meta .t{color:var(--good);font-weight:600}
.rank{list-style:none;padding:0;margin:10px 0;counter-reset:r}
.rank li{display:flex;justify-content:space-between;gap:12px;padding:9px 12px;border:1px solid var(--grid);
 border-radius:9px;margin:6px 0;background:var(--card);font-size:13.5px}
.rank li b{font-variant-numeric:tabular-nums;white-space:nowrap}
.foot{margin-top:60px;padding-top:16px;border-top:1px solid var(--grid);color:var(--muted);font-size:12.5px}
code{background:var(--chip);border-radius:5px;padding:1px 6px;font-size:12.5px}
"""

def build_playbooks():
    out = []
    for pb in PLAYBOOKS:
        phases = ""
        for pt, pa, bn, tg in pb["phases"]:
            phases += f"""<div class="phase" style="--pc:{pb['color']}">
              <div class="pt">{html.escape(pt)}</div>
              <div class="pa">{html.escape(pa)}</div>
              <div class="meta"><span class="b">Bottleneck:</span> {html.escape(bn)}
                 &nbsp;·&nbsp; <span class="t">Trigger:</span> {html.escape(tg)}</div></div>"""
        out.append(f"""<div class="pb">
          <div class="pb-head" style="color:{pb['color']}">{html.escape(pb['name'])}</div>
          <div class="pb-idea">{html.escape(pb['idea'])}</div>{phases}</div>""")
    return "\n".join(out)

def build_month_tables():
    out = ""
    for scn in SCN:
        n = scn["name"]; last = MID[n]["rows"][-1]
        out += f"""<details><summary><span style="color:{scn['color']}">{html.escape(n)}</span>
          <span style="color:var(--muted);font-weight:400;font-size:12.5px">
          m24 {money(last['mrr'])}/mo · {last['active']:.0f} active · worst {money(MID[n]['worst'])}</span></summary>
          <div class="inner"><div class="mtwrap">{scn_table(n)}</div></div></details>"""
    return out

def build_cadence():
    rows = cadence_rows()
    body = ""
    for short, leads_d, demos_d, cr, color in rows:
        body += (f"<tr><td style='color:{color};font-weight:600'>{short}</td>"
                 f"<td>{leads_d}</td><td>{demos_d}</td><td>{cr}/wk</td></tr>")
    return (f"<table class='ref'><thead><tr><th>Scenario</th><th>Leads/day (peak)</th>"
            f"<th>Demos/day (peak)</th><th>Creatives tested</th></tr></thead><tbody>{body}</tbody></table>")

# ---- sensitivity ranked list ----
sens_li = ""
for lab, lo, hi, swing in SENS_RANK:
    sens_li += (f"<li><span>{html.escape(lab)}</span>"
                f"<b>{money(lo)} → {money(hi)} &nbsp;(Δ {money(swing)})</b></li>")

# ---- setup fee read ----
setup_body = ""
for short, w0, w2, c0, c2 in SETUP_ROWS:
    setup_body += (f"<tr><td>{short}</td><td>{money(w0)}</td><td>{money(w2)}</td>"
                   f"<td>{money(w2-w0)}</td><td>{money(c0)} → {money(c2)}</td></tr>")

HTML = f"""<title>Med-Spa Agency — 24-Month Scenario Model</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{CSS}</style>
<div class="wrap">
<h1>Med-Spa AI-Automation Agency — 24-Month Scenario Model</h1>
<p class="sub">Solo founder · GoHighLevel · $500 entry (no setup) → $1,500 full system · Meta lead ads you close yourself.
Month 1 = launch. All figures at the <b>45% upsell</b> variant unless noted; 33% and 60% variants in the tables.</p>
<div>
 <span class="tag">7 scenarios</span><span class="tag">24 months</span>
 <span class="tag">churn {int(M.A['churn']*100)}%/mo</span><span class="tag">winnable/metro ≈ {CEIL}</span>
 <span class="tag">upsell 33/45/60%</span>
</div>

<div class="callout">
<b>The honest read — 5 things the math says</b>
<ol>
<li><b>One metro caps you at ~{CEIL} clients ≈ {money(agg['mrr'])}/mo MRR.</b> Aggressive, Team, Hybrid and Lean all
converge to the same ceiling — heavier ad spend only changes <i>how fast</i> you get there, not the endpoint. Past
~90 active, extra spend in one metro is waste (the model auto-throttles it).</li>
<li><b>To beat ~$100k MRR you change price or geography, not spend.</b> Premium pricing lifts the same {CEIL} clients to
{money(prem['mrr'])}/mo (+{100*(prem['mrr']/agg['mrr']-1):.0f}%); three metros reach {money(multi['mrr'])}/mo with {multi['active']:.0f} active.</li>
<li><b>This business has almost no cash valley.</b> With $0 setup, same-month billing and founder-delivered fulfillment,
the deepest any scenario ever goes is <b>≈ {money(WORST_ALL)}</b> — about one month of ad spend. Payback per client is ~1 month.
You are not cash-constrained; you are <i>throughput- and retention-constrained</i>.</li>
<li><b>The single input that moves month-24 MRR most is {html.escape(top_lever[0].split('  ')[0])}</b> — swinging it moves the endpoint by
{money(top_lever[3])}. Funnel efficiency (CPL, close, booking) barely moves the <i>endpoint</i> in a capped metro; it only moves the <i>date</i> you hit the cap.</li>
<li><b>Churn compounds quietly:</b> at 3%/mo you keep {churn_curve().split(' · ')[1].split(': ')[1]} of a cohort at 12 months and only
{churn_curve().split(' · ')[3].split(': ')[1]} at 24. Every point of churn is worth more than a point of close rate once you're near the ceiling.</li>
</ol>
</div>

<div class="cards">{summary_cards()}</div>

<h2>1 · Assumptions (edit these first)</h2>
<p class="sub">Everything downstream is computed from this block. Change a number in <code>model.py</code> and rerun — every table and chart regenerates. These are defensible defaults, not your numbers; overwrite them the moment you have real data.</p>
<h3>Funnel</h3>
{tbl([(a,b,c) for a,b,c in FUNNEL_ROWS], ["Input","Baseline","Note / how it moves"])}
<h3>Fixed business assumptions</h3>
{tbl([(a,b,c) for a,b,c in FIXED_ROWS], ["Input","Baseline","Note"])}
<h3>What each scenario varies (only founder-controllable inputs)</h3>
{tbl([
  ("Ads-Only Conservative","$2k flat","level 1","none","1","—","The floor / do-nothing-fancy case"),
  ("Ads-Only Aggressive","$3k→$10k","level 2","VA+MB+AM","1","—","Max spend into one metro"),
  ("Hybrid","$2.5k flat","level 2","VA+AM","1","—","+2 warm/mo +8% referral engine"),
  ("Scale-With-Team","$3k→$9k","level 2","VA+MB+AM early","1","—","Hire ahead of the ceiling"),
  ("Multi-Metro","$4k→$12k","level 2","VA+MB+AM/metro","1→3","—","Open metro 2 @90 active, metro 3 later"),
  ("Premium-Pricing","$3k→$6k","level 3","VA+MB+AM","1","@10 CS","Raise both tiers at 10 case studies"),
  ("Lean Cash-First","35% of collections","level 2","VA+AM","1","—","Reinvest profit only; near-zero risk"),
 ], ["Scenario","Monthly ad spend","Funnel opt","Hiring","Metros","Pricing","What it tests"])}

<h2>2 · The charts</h2>
<figure>{img(IMG_3D,"3D MRR surface")}<figcaption><b>(a) Required 3D chart.</b> X = month, Y = scenario, Z = MRR. The Multi-Metro ridge is the only one that keeps climbing; the single-metro paths flatten as they hit the ~{CEIL}-client ceiling. Surface shade = MRR magnitude; colored ridge = scenario.</figcaption></figure>
<figure>{img(IMG_ACTIVE,"active clients per scenario")}<figcaption><b>(b) Required chart: active clients / scenario.</b> Note the convergence — every well-funded single-metro path lands at ~{CEIL}. The dashed line is the single-metro ceiling (0.35 × 300). Only Multi-Metro breaks through; only Conservative fails to reach it.</figcaption></figure>
<div class="two">
<figure>{img(IMG_MRR,"MRR lines")}<figcaption><b>(c) MRR over time</b> — the readable 2-D companion to the surface. Premium separates from the pack once the price raise fires (~month 6).</figcaption></figure>
<figure>{img(IMG_CUM,"cumulative cash")}<figcaption><b>(d) Cumulative cash</b> (collections − ad spend − tools − team; founder pay not deducted). All lines go up and to the right fast — the model mints cash.</figcaption></figure>
</div>
<figure>{img(IMG_VALLEY,"cash valley zoom")}<figcaption><b>(e) The cash valley, zoomed to months 1–6.</b> The deepest hole across all 7 scenarios is ≈ {money(WORST_ALL)}. This is the single most important cash fact: there is essentially no valley to fund.</figcaption></figure>

<h2>3 · Full monthly tables (all 24 months)</h2>
<p class="sub">Per scenario: new closed · active split entry/upsold · MRR · cash flow · cumulative cash · CAC · payback · team size · effective CPL. Negative cash-flow months are red. (45% upsell variant.)</p>
{build_month_tables()}

<h2>4 · Per-scenario playbooks — phase actions, #1 bottleneck, numeric triggers</h2>
<p class="sub">Phases are by <b>client count</b>, never dates. Every hire/expansion trigger is a number.</p>
{build_playbooks()}

<h2>5 · Sensitivity — what moves month-24 MRR the most</h2>
<figure>{img(IMG_SENS,"sensitivity tornado")}<figcaption>Reference = Ads-Only Aggressive (single metro), baseline M24 MRR {money(SENS_BASE)}. Bars show M24 MRR when each input is swung to its low/high. Longer bar = bigger lever.</figcaption></figure>
<p><b>Ranked by impact on month-24 MRR (biggest first):</b></p>
<ol class="rank">{sens_li}</ol>
<p class="sub"><b>Read it this way:</b> in a saturated single metro the endpoint is set by <b>ceiling economics</b> — upsell take-rate, churn, winnable market share and price. Funnel inputs (CPL, close, booking) rank at the bottom <i>for the endpoint</i> because they only change the <b>month you hit {CEIL}</b>, not the height of the ceiling. That flips in Multi-Metro, where you're never capped and funnel efficiency compounds. Practical takeaway: once you have proof, <b>defend churn and push upsell/price before you touch the ad account.</b></p>

<h2>6 · Setup-fee sensitivity — $0 vs $297</h2>
<figure>{img(IMG_SETUP,"setup fee comparison")}<figcaption>Worst cumulative-cash drawdown under each policy (45% upsell).</figcaption></figure>
{tbl([(short,money(w0),money(w2),money(w2-w0),f"{money(c0)} → {money(c2)}") for short,w0,w2,c0,c2 in SETUP_ROWS],
     ["Scenario","Worst draw ($0)","Worst draw ($297)","Cash saved","Month-1 cash flow"])}
<p class="sub"><b>What removing the setup fee costs you:</b> almost nothing in cash risk — a $297 fee shaves only ~$300–1,700 off an already-shallow drawdown and flips month 1 positive in most paths. The fee's real value isn't cash-flow; it's a <b>commitment filter</b> (fewer tire-kickers) traded against a <b>lower close rate</b> (a price objection at the worst moment — cold, zero case studies). At your close rates the $0-setup offer is the right call to maximize logo velocity; revisit a setup fee only after 3+ case studies when you can absorb the close-rate hit.</p>

<h2>7 · Translate to daily / weekly behavior</h2>
<p class="sub">Peak-month operating tempo implied by each scenario. "Leads/day" and "demos/day" are the busiest month ÷ 22 workdays.</p>
{build_cadence()}
<h3>The non-negotiable daily loop (every scenario)</h3>
<ul>
<li><b>&lt;5-min callback</b> on 100% of leads — speed-to-lead is the highest-ROI habit; it's baked into the {int(M.A['lead_to_booked']*100)}% book rate. Miss it and booked-rate falls first.</li>
<li><b>Confirm-and-remind</b> every booked demo (24h + 2h + 15-min) — this is the {int(M.A['show_rate']*100)}% show rate. No-shows are the cheapest leak to fix.</li>
<li><b>Run your demos, then log every ROI-dashboard win</b> — proof is what moves close rate 20% → 35% and unlocks the price raise at 10 case studies.</li>
</ul>
<h3>The Friday scoreboard (report these 8 numbers to yourself weekly)</h3>
{tbl([
 ("1 · Leads in","weekly","Ad account. Falling → creative fatigue; refresh."),
 ("2 · Cost per lead","weekly","Vs $25 baseline. Climbing → saturation or fatigue."),
 ("3 · Callbacks &lt;5 min","% of leads","Target 100%. This is your speed-to-lead discipline."),
 ("4 · Demos booked / shown","count + %","Show% &lt;70% → fix reminders before spending more."),
 ("5 · Closes + close rate","count + %","Tracks toward 35% as case studies bank."),
 ("6 · New MRR added","$","New closes × price. The growth number."),
 ("7 · Churn this week","logos + $","The number that quietly caps you. Guard it hardest."),
 ("8 · Active vs ceiling","x / {ceil}".replace("{ceil}",str(CEIL)),"At 90 → open metro 2 or raise price. Don't just add spend."),
], ["Metric","Unit","Why it's on the board"])}

<div class="foot">
<p><b>Model files:</b> <code>model.py</code> (all assumptions + cohort engine) · <code>report.py</code> (charts + this page) · <code>data/*.csv</code> (per-scenario monthly output) · <code>charts/*.png</code>.</p>
<p><b>Rerun with real data:</b> replace the funnel numbers in <code>model.py</code> → <code>A</code> (and the scenario ad-spend schedules) with your mentor's student numbers or your first 2 weeks of campaign data, then <code>python3 report.py</code>. Every table, chart and the honest read above recompute automatically. Nothing here is your data yet — these are defensible placeholders.</p>
<p>Cohort churn compounds monthly; upsell fires on survivors at cohort age 2; saturation and case-study effects read the prior month's state (no within-month circularity). Cash flow = collections − ad spend − tools − team; founder pay is <i>not</i> deducted (it's your take-home = cumulative cash).</p>
</div>
</div>"""

with open(os.path.join(HERE, "report.html"), "w") as f:
    f.write("<!doctype html><html><head><meta charset='utf-8'></head><body>" + HTML + "</body></html>")
# also write the artifact-ready fragment (no html/head/body wrappers)
with open(os.path.join(HERE, "report_artifact.html"), "w") as f:
    f.write(HTML)
print("wrote report.html and report_artifact.html")
print(f"exec: single-metro ceiling {CEIL} | worst draw {money(WORST_ALL)} | top lever {top_lever[0].split(chr(10))[0]} Δ{money(top_lever[3])}")
