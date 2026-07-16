# Med-Spa AI-Automation Agency — 24-Month Scaling Model

A complete, editable scenario model for a solo founder scaling a GoHighLevel-based
AI-automation agency serving **med spas only**. Six scaling paths, one engine,
24 months (Month 1 = launch). Math and the honest read — no motivation.

- **Entry tier:** $500/mo (DB reactivation + review & referral automation), **$0 setup**.
- **Full tier:** $1,500/mo (missed-call text-back, speed-to-lead, voice AI, ROI dashboard),
  offered ~2 months after close once the ROI dashboard shows $5k+ recovered.

## Files

| File | What it is |
|---|---|
| `model.py` | The engine. Pure Python stdlib. Editable assumptions at top. Run it. |
| `franchise.py` | The chosen single-niche strategy: franchise anchors + network referrals + ramping ads. Models the accelerant on top of the ads+referral engine, with concentration risk + anchor-churn stress. |
| `dashboard.html` | Interactive cockpit — same math in JS, live-editable, all charts + tables + playbooks. Open in any browser. |
| `franchise_cockpit.html` | Interactive cockpit for the franchise-anchored strategy — live editable funnel/franchise/anchor levers, MRR composition, the concentration-risk chart, anchor-churn stress test, and the operating blueprint. Mirrors `franchise.py` (verified across 264 cells). |
| `bolso.html` | The simple view (PT): company revenue vs. net profit "in your pocket" over 24 months — one clean chart, the money-split, and Year 1 vs Year 2. Based on the franchise plan. |
| `aquisicao.html` | The acquisition plan (PT): new clients to close each month and how — stacked bars by source (ads / referral / anchor), the full monthly table with the ads-funnel requirement ($ → leads → demos → closes), and per-phase actions. Based on the franchise plan. |
| `boafe.html` | The conservative good-faith base (PT): a flat 4 new clients/mo at $500 with 1.4 upsold to $1,500 two months later, 3% churn. Simple hand-checkable MRR build (entry vs full) + net profit → $56k MRR / $45k pocket by month 24. |
| `outputs/*.csv` | One CSV per scenario, all 24 months, every metric. |
| `outputs/all_scenarios.json` | Machine-readable full output. |

## Run it

```bash
python3 medspa/model.py      # prints summary + sensitivity, writes CSVs + JSON
```

Open `medspa/dashboard.html` in a browser for the interactive version (edit any
input, everything reruns). The JS engine is verified against the Python engine
across all 1,296 monthly cells (6 scenarios × 24 months × 9 fields), zero mismatches.

## Assumptions (editable — these are honest cold-B2B defaults, not your numbers)

**Funnel** (Meta lead ads → booked demo → your close):
cost/lead **$25**, lead→booked **25%**, show rate **60%**, cold close **12%** with 0 case
studies → **28%** with 3+, a 2-week launch learning phase (month-1 CPL ×1.6, close ×0.6),
and a creative-fatigue refresh cycle by funnel-optimization level.

**Business:** churn **3%/mo compounding**, upsell lands **2 months** after close at a
**33 / 45 / 60%** take rate (by scenario), tools **$300 + $15/client** (~$700 near 27
clients), one metro = **300** addressable spas (saturation drives CPL up to **1.9×** at
full penetration), solo ceilings of **15** full installs and **~28** total actives before
hires are mandatory (each AM adds 20 full / 10 support, each VA adds 25 support, a media
buyer runs each $10k of spend).

## Results — month 24

| Scenario | MRR/mo | Active | Cum. cash (24mo) | Worst drawdown |
|---|--:|--:|--:|--:|
| Ads-Only Conservative | $31k | 40 | $283k | −$4.3k |
| Ads-Only Aggressive | $126k | 140 | $988k | −$7.3k |
| **Hybrid (ads+referrals+outreach)** | **$103k** | **116** | **$970k** | **−$0.8k** |
| Scale-With-Team | $139k | 155 | $1.06M | −$8.0k |
| Multi-Metro Expansion | $133k | 150 | $835k | −$4.9k |
| Premium-Pricing Path | $111k | 79 | $996k | −$4.5k |

## The honest read

1. **Winner on MRR: Scale-With-Team ($139k/mo)** — but deepest, longest cash hole and it
   only pays off if you fill the seats you hire.
2. **Winner on risk-adjusted return: Hybrid** — $103k/mo at a **−$826** worst drawdown and
   half the ad dependency. Referrals + outreach are near-zero-CAC closes that don't care
   what the paid funnel does.
3. **Throughput-limited, not capital-limited.** With $0 setup and a 2–3 month payback, the
   worst hole any path digs is under **$8k**. You don't need much cash — you need the funnel
   to convert.
4. **Biggest lever on month-24 MRR: your SHOW RATE**, then cold close rate — both move it
   more than churn or ad spend (±20% show rate swings Aggressive's month-24 MRR by ~$52k).
   Protect the <5-min callback and reminder sequence like revenue.
5. **One metro saturates.** Aggressive's CPL climbs to ~$87 by month 24 (re-pitching the
   same 300 spas); Multi-Metro holds ~$44 by opening fresh markets at client-count triggers.
6. **Keep the $0 setup.** A $297 fee removes only ~$950 of drawdown and, once you count the
   ~12% close-rate drag, **costs ~$111k in 24-month cumulative cash** — it's net-positive on
   cash only if it dents your close rate by **< 4.5%**.
7. **Churn is the tax you can't see.** At 3%/mo, only ~48% of a signed cohort is still paying
   at month 24. Past ~30 clients, much of each month's closing just replaces the leak.

## Hire / expansion triggers (numbers, never dates)

| Scenario | VA | Media buyer | Account manager | Expansion / pricing |
|---|---|---|---|---|
| Conservative | 22 actives | — | 13 full installs | — |
| Aggressive | 16 actives | $6k/mo spend | 12 full installs | — |
| Hybrid | 20 actives | — | 13 full installs | referral engine |
| Scale-With-Team | 10 actives | 15 actives | 11 full installs | — |
| Multi-Metro | 18 actives | 30 actives | 12 full installs | metro 2 @ 18, metro 3 @ 36 |
| Premium | 18 actives | — | 12 full installs | raise price @ 10 case studies |

Beyond the first (proactive) hire, headcount scales with the book: **1 AM per 20 full
installs, 1 VA per 25 support, 1 media buyer per $10k spend.**

## Rerun with your real numbers

When you have your mentor's student numbers or your first two weeks of campaign data,
overwrite the funnel cells in `ASSUMPTIONS` (top of `model.py`) — `cost_per_lead`,
`lead_to_booked`, `show_rate`, `close_0cs`, `close_3cs`, `churn`, and the per-scenario
`upsell_take` — and rerun. Or just type them into the dashboard's Assumptions panel;
every scenario, chart, and table reprices instantly. Nothing else needs to change.

## Caveats

Fractional clients are expected-value math, not half a person. Cumulative cash excludes
founder draw and assumes monthly collection. The Premium path reprices the entire book at
the raise (migration, not grandfathering) — grandfathering would smooth and lower that
curve. Every figure is model output under editable assumptions, not a promise.
