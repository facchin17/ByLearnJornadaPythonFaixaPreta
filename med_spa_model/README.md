# Med-Spa AI-Automation Agency — 24-Month Scenario Model

A reproducible cash-flow + scaling model for a solo, GoHighLevel-based agency
serving med spas only. Entry tier **$500/mo** (no setup fee) → upsell to the
**$1,500/mo** full system ~2 months after close.

Open **`report.html`** in any browser for the full deliverable (charts, tables,
per-scenario playbooks, sensitivity, cadence). Everything is generated from the
two scripts below — nothing is hand-typed, so it stays internally consistent.

## Files

| File | What it is |
|------|-----------|
| `model.py` | All editable assumptions + the cohort simulation engine. **Edit this to change inputs.** |
| `report.py` | Builds every chart and the self-contained `report.html`. |
| `report.html` | The full report (open this). Self-contained — charts are embedded. |
| `data/*.csv` | Per-scenario monthly output (24 rows × all metrics). |
| `charts/*.png` | Standalone chart images. |

## Run it

```bash
pip install numpy pandas matplotlib
python3 model.py      # prints the month-24 snapshot, writes data/ + summary.json
python3 report.py     # writes charts/ and report.html
```

## The 7 scenarios (vary only founder-controllable inputs)

1. **Ads-Only Conservative** — $2k/mo flat, no hires, one metro (the floor case).
2. **Ads-Only Aggressive** — ramp $3k→$10k, hire on triggers, dominate one metro.
3. **Hybrid** — $2.5k ads + warm outreach + an 8%-of-actives referral engine.
4. **Scale-With-Team** — hire VA → media buyer → account manager ahead of ceilings.
5. **Multi-Metro Expansion** — saturate metro 1, then open 2 and 3.
6. **Premium-Pricing** — raise both tiers once you hold 10+ case studies.
7. **Lean Cash-First** — reinvest only 35% of collections; near-zero cash risk.

## The three findings that matter

1. **One metro caps you at ~105 active ≈ $97k/mo MRR.** More ad spend only changes
   *how fast* you reach the cap, not the endpoint. Growth past it comes from
   **price** (Premium → ~$134k) or **geography** (3 metros → ~$282k).
2. **There is almost no cash valley** — deepest hole across all paths ≈ **−$1.7k**
   (about one month of ad spend). This business is throughput- and retention-
   constrained, not cash-constrained.
3. **Churn and upsell/price move the 24-month endpoint far more than funnel
   efficiency** once you're near the metro ceiling.

## Replacing assumptions with real data

Open `model.py`, edit the `A` dict (funnel + fixed assumptions) and the
`SCENARIOS` ad-spend schedules, then rerun `python3 report.py`. When you paste
your mentor's student numbers or your first 2 weeks of campaign data, overwrite
`cpl_base`, `lead_to_booked`, `show_rate`, `close_0cs`, `close_3cs`, `churn`,
and the per-scenario `spend` schedules — everything recomputes.

> These are defensible **placeholder** assumptions, not your numbers. Every
> load-bearing one is flagged in the report.
