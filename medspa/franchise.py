"""
Franchise-anchored, SINGLE-NICHE growth model.

The chosen strategy: stay in ONE niche (med spa), do elite work for franchise
operators, and grow with the two channels that compound each other —
NETWORK REFERRALS (from franchise owners) + MORE ADS (scaled up as referrals
lower your blended CAC). Not niche-hopping. Not franchise-only.

This reuses the main engine's assumptions (medspa/model.py). The point it proves:
franchises are an ACCELERANT layered on the ads+referral engine, not a
replacement for it — and concentration is the one risk that defines the play.

Run:  python3 medspa/franchise.py
"""
import sys, math, csv, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as M

A = M.ASSUMPTIONS
FUNNEL_OPT = M.FUNNEL_OPT
HZN = 24

# ── EDITABLE FRANCHISE KNOBS ────────────────────────────────────────────────
FRAN = {
    "fran_price":     1100.0,   # compressed full-system price / location (vs $1,500 solo)
    "fran_churn":     0.015,    # multi-unit is stickier than a solo clinic (vs 3%)
    "fran_ref":       0.055,    # network referrals per LIVE location / month
    "fran_ref_step":  0.085,    # after the preferred-vendor tipping point
    "tip":            15,       # live locations that trigger the step-up
    "indie_ref":      0.060,    # generic referrals per indie active / month (leveraged)
    "outreach":       2.5,      # founder warm-outreach closes/mo when small (tapers)
    "upsell_take":    0.45,
}
# Ads RAMP UP over time — "referrals AND more ads": as referrals de-risk CAC and
# case studies cut CPL, you pour more into ads. (month, monthly_spend)
AD_RAMP = [(1, 2500), (6, 4000), (12, 6000)]
# Anchors: each is a DIFFERENT franchise brand -> (month_landed, num_locations).
# Diversifying across brands is what caps concentration risk.
ANCHORS = [(4, 8), (10, 6), (16, 6)]


def ramp(sched, m):
    cur = 0.0
    for mo, v in sorted(sched):
        if mo <= m:
            cur = v
    return cur


def simulate_franchise(ad_ramp=AD_RAMP, anchors=ANCHORS, F=FRAN, anchor_churn=None):
    """anchor_churn = (brand_index, month) to stress-test losing an anchor."""
    surv_i = 1 - A["churn"]; surv_f = 1 - F["fran_churn"]
    opt = FUNNEL_OPT["good"]
    hist = []                       # indie closes history (for the 2-month upsell)
    ie = iff = fran = 0.0           # indie entry, indie full, franchise locations
    brand_live = [0.0] * len(anchors)
    cum = wd = 0.0; wdm = 0; cb = 0.0; am = va = mb = 0
    rows = []
    for m in range(1, HZN + 1):
        tap = ie + iff + fran
        ad = ramp(ad_ramp, m)

        # ── indie funnel (paid), like the main model ──
        cpl = A["cost_per_lead"] * opt["cpl_mult"] * A["learn_cpl_mult"].get(m, 1.0) \
            * (1 + A["fatigue_rate"] * ((m - 1) % opt["refresh_cycle"]))
        cpl *= (1 + A["saturation_slope"] * (cb / A["metro_size"]))
        if ad > A["founder_spend_ceiling"] and not mb:
            mb = 1  # scaling ads needs a media buyer
        if mb:
            cpl *= A["media_buyer_cpl_mult"]
        cum_mat = sum(hist[:max(0, m - 2)])
        cs = min(A["case_study_cap"], A["case_study_yield"] * cum_mat)
        t = min(1.0, cs / 3.0)
        clo = A["close_0cs"] + (A["close_3cs"] - A["close_0cs"]) * t
        if cs > 3:
            clo += min(1.0, (cs - 3) / 7.0) * A["close_social_bonus"]
        clo *= A["learn_close_mult"].get(m, 1.0)
        leads = ad / cpl; booked = leads * A["lead_to_booked"]; shown = booked * A["show_rate"]
        cb += booked
        indie_paid = shown * clo
        indie_ref_c = F["indie_ref"] * (ie + iff)
        outreach_c = max(0.0, F["outreach"] - 0.05 * tap) if F["outreach"] else 0.0
        indie_new = indie_paid + indie_ref_c + outreach_c
        hist.append(indie_new)

        # ── franchise network referrals -> NEW locations (warm, near-zero CAC) ──
        fyield = F["fran_ref_step"] if fran >= F["tip"] else F["fran_ref"]
        fran_new = fyield * fran

        # ── churn (indie 3%, franchise 1.5%) ──
        ie *= surv_i; iff *= surv_i; fran *= surv_f
        brand_live = [b * surv_f for b in brand_live]
        if anchor_churn and m == anchor_churn[1]:
            bi = anchor_churn[0]; fran -= brand_live[bi]; brand_live[bi] = 0.0

        # ── add new business ──
        ie += indie_new
        fran += fran_new
        for bi, (am_, sz) in enumerate(anchors):
            if m == am_:
                fran += sz; brand_live[bi] += sz

        # ── indie upsell (2-month lag) ──
        j = m - A["upsell_delay"]
        if j >= 1:
            up = hist[j - 1] * (surv_i ** A["upsell_delay"]) * F["upsell_take"]
            ie -= up; iff += up

        # ── team scales with the book (franchise installs count as full installs) ──
        full_installs = iff + fran
        am = max(am, math.ceil(max(0.0, full_installs - A["solo_full_capacity"]) / A["am_full_capacity"]))
        va = max(va, math.ceil(max(0.0, tap - (A["solo_support_cap"] + A["am_support_add"] * am)) / A["va_support_add"]))

        # ── MRR / cash ──
        mrr = ie * A["price_entry"] + iff * A["price_full"] + fran * F["fran_price"]
        tools = A["tools_base"] + A["tools_per_client"] * (ie + iff + fran)
        team = A["salary_va"] * va + A["salary_account_mgr"] * am + A["salary_media_buyer"] * mb
        ref_cost = (indie_ref_c + fran_new) * A["referral_reward"]
        cf = mrr - ad - tools - team - ref_cost
        cum += cf
        if cum < wd: wd = cum; wdm = m

        biggest = max(brand_live) if brand_live else 0.0
        conc = (biggest * F["fran_price"]) / mrr if mrr > 0 else 0.0
        fran_share = (fran * F["fran_price"]) / mrr if mrr > 0 else 0.0
        rows.append(dict(month=m, ad_spend=round(ad), indie=round(ie + iff, 1), indie_entry=round(ie, 1),
                         indie_full=round(iff, 1), fran=round(fran, 1), biggest_brand=round(biggest, 1),
                         mrr=round(mrr), fran_share=round(fran_share, 3), concentration=round(conc, 3),
                         cash_flow=round(cf), cum_cash=round(cum), team=va + am + mb, cpl=round(cpl, 1)))
    L = rows[-1]
    return rows, dict(mrr_24=L["mrr"], indie_24=L["indie"], fran_24=L["fran"], fran_share=L["fran_share"],
                      cum_24=L["cum_cash"], worst_drawdown=round(wd), worst_month=wdm,
                      peak_conc=max(r["concentration"] for r in rows[:12]))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    plan_rows, plan = simulate_franchise()
    pure_rows, pure = simulate_franchise(ad_ramp=[(1, 2000)], anchors=[(4, 8)])   # franchise-only, low ads
    _, stress = simulate_franchise(anchor_churn=(0, 14))                          # lose anchor #1 at mo 14

    with open(os.path.join(here, "outputs", "franchise_plan.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(plan_rows[0].keys())); w.writeheader(); w.writerows(plan_rows)

    print("=" * 84)
    print("FRANCHISE-ANCHORED, SINGLE-NICHE PLAN  (ads ramp $2.5k->$6k + referral engine + 3 anchors)")
    print("=" * 84)
    print(f"{'mo':>3}{'ads':>6}{'indie':>7}{'fran':>6}{'big':>5}{'MRR':>9}{'fran%':>7}{'conc%':>7}{'cash':>9}{'cum':>10}{'team':>5}")
    for r in plan_rows:
        if r["month"] in (1, 3, 4, 6, 9, 12, 16, 18, 24):
            print(f"{r['month']:>3}{r['ad_spend']:>6}{r['indie']:>7.0f}{r['fran']:>6.0f}{r['biggest_brand']:>5.0f}"
                  f"{r['mrr']:>9,.0f}{r['fran_share']*100:>6.0f}%{r['concentration']*100:>6.0f}%{r['cash_flow']:>9,.0f}"
                  f"{r['cum_cash']:>10,.0f}{r['team']:>5}")
    print("-" * 84)
    print(f"THE PLAN     month-24 MRR ${plan['mrr_24']:,.0f}  |  {plan['indie_24']:.0f} indie + {plan['fran_24']:.0f} franchise loc"
          f"  |  franchise {plan['fran_share']*100:.0f}% of MRR")
    print(f"             worst drawdown ${plan['worst_drawdown']:,.0f} (mo {plan['worst_month']})  |  cum cash ${plan['cum_24']:,.0f}"
          f"  |  peak single-brand concentration {plan['peak_conc']*100:.0f}%")
    print(f"FRANCHISE-ONLY (low ads, 1 anchor):  month-24 MRR ${pure['mrr_24']:,.0f}  |  peak concentration {pure['peak_conc']*100:.0f}%"
          f"  <- underperforms; too dependent on one account")
    print(f"ANCHOR-CHURN STRESS (lose anchor #1 at mo 14):  month-24 MRR ${plan['mrr_24']:,.0f} -> ${stress['mrr_24']:,.0f}")
    print("\nHONEST READ: franchises are the ACCELERANT, not the engine. Keep ads scaling and the")
    print("indie base growing underneath so no single owner/brand ever exceeds ~25% of MRR.")


if __name__ == "__main__":
    main()
