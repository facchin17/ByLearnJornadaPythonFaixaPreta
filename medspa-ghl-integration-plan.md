# Med Spa ↔ GoHighLevel Integration — Full Backend Design & Build Plan

> **Purpose:** A complete, reusable blueprint for connecting a med spa's existing CRM / booking / EHR to GoHighLevel (GHL) **without replacing** their current system. GHL becomes the *marketing, speed-to-lead, follow-up, review, reactivation, and reporting* layer. The med spa's system stays the *source of truth* for appointments and clinical records.
>
> **Design principle:** Keep Protected Health Information (PHI) out of GHL. Sync only the minimum "marketing-grade" data needed to run automations. Everything is packaged into a reusable snapshot so each new med spa is a 1–2 day deploy, not a rebuild.

---

## Table of Contents

1. [Ideal System Architecture](#1-ideal-system-architecture)
2. [Role of GoHighLevel](#2-role-of-gohighlevel)
3. [Role of the Med Spa's Existing CRM/Booking System](#3-role-of-the-med-spas-existing-crmbooking-system)
4. [What Data Syncs INTO GHL](#4-what-data-syncs-into-ghl)
5. [What Data Should NOT Sync Into GHL](#5-what-data-should-not-sync-into-ghl)
6. [HIPAA / Privacy-Sensitive Handling](#6-hipaa--privacy-sensitive-handling)
7. [Access You Need From the Client](#7-access-you-need-from-the-client)
8. [Discovery Questions to Ask the Med Spa](#8-discovery-questions-to-ask-the-med-spa)
9. [Connection Methods (Native / Zapier / Make / Webhooks / API / CSV)](#9-connection-methods)
10. [Events That Trigger Automations](#10-events-that-trigger-automations)
11. [Custom Fields in GHL](#11-custom-fields-in-ghl)
12. [Tags in GHL](#12-tags-in-ghl)
13. [Pipeline Stages in GHL](#13-pipeline-stages-in-ghl)
14. [Workflows in GHL](#14-workflows-in-ghl)
15. [Speed-to-Lead Automation](#15-speed-to-lead-automation)
16. [Review Automation](#16-review-automation)
17. [No-Show Recovery](#17-no-show-recovery)
18. [Reactivation Campaigns](#18-reactivation-campaigns)
19. [Internal Alerts (Owner / Front Desk)](#19-internal-alerts)
20. [Owner Dashboard](#20-owner-dashboard)
21. [Testing Before Go-Live](#21-testing-before-go-live)
22. [Common Failure Points & How to Avoid Them](#22-common-failure-points)
23. [What to Customize Per Med Spa](#23-what-to-customize-per-med-spa)
24. [What Becomes a Reusable Snapshot](#24-what-becomes-a-reusable-snapshot)
25. [Sales Demo Script](#25-sales-demo-script)
26. [Appendix A — Example Field Mappings](#appendix-a--example-field-mappings)
27. [Appendix B — Master Build Checklist](#appendix-b--master-build-checklist)

---

## 1. Ideal System Architecture

### High-level flow

```
                     ┌─────────────────────────────────────────────┐
                     │         MED SPA'S EXISTING SYSTEM            │
                     │   (CRM / Scheduler / EHR — source of truth)  │
                     │   e.g. Aesthetic Record, Boulevard,          │
                     │   Zenoti, Nextech, Mangomint, Vagaro,        │
                     │   Jane, Acuity, Mindbody                     │
                     └───────────────┬─────────────────────────────┘
                                     │
              Appointment/status events (NO clinical data)
                                     │
                    ┌────────────────▼───────────────┐
                    │        MIDDLEWARE / SYNC        │
                    │   Native app  ─┐                │
                    │   Webhooks     ├─►  Zapier /    │
                    │   API polling ─┘    Make.com    │
                    │   (field mapping + PHI filter)  │
                    └────────────────┬────────────────┘
                                     │
                  Marketing-safe fields only (name, phone,
                  email, appt status, service category, $value)
                                     │
                     ┌───────────────▼─────────────────┐
                     │           GOHIGHLEVEL            │
                     │   Contacts • Custom Fields •     │
                     │   Tags • Pipelines • Workflows • │
                     │   SMS/Email • Reviews • Reporting│
                     └───────────────┬─────────────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        ▼                            ▼                             ▼
   Lead sources              Communication              Owner/Staff visibility
 (FB/IG, Google,           (SMS, Email, Voicemail       (Dashboard, alerts,
  website forms,            drops, GBP reviews)          Slack/SMS notifications)
  call tracking)
```

### The four architectural layers

| Layer | Responsibility | Tooling |
|---|---|---|
| **System of Record** | Appointments, clinical notes, payments, charts | The med spa's CRM/EHR (unchanged) |
| **Integration / Sync** | Move marketing-safe events both ways, map fields, strip PHI | Native connector → Webhooks → Zapier/Make (in that priority order) |
| **Engagement / Automation** | Lead nurture, speed-to-lead, follow-up, reviews, reactivation | GoHighLevel |
| **Presentation / Reporting** | Owner dashboard, ROI proof, alerts | GHL Dashboards + custom values |

### Direction of sync

- **CRM → GHL (inbound):** appointment status changes (booked, cancelled, no-show, completed), new patient contact record (marketing-safe fields only). This is what powers review, no-show, and reactivation automations.
- **GHL → CRM (outbound, optional):** new lead captured in GHL that the front desk should add to the scheduler. Often handled by a task/alert to the front desk rather than a true write-back, to avoid duplicate/dirty records in the EHR.
- **Rule of thumb:** Prefer **read/notify** into the EHR (a task for a human) over automated writes. EHRs are messy to write into and often not the place you want automation creating records.

### Why middleware instead of direct

The med spa's system rarely has a clean native GHL connector. A thin middleware layer (Make.com is the workhorse) lets you:
- Map fields once and reuse the scenario per client.
- **Filter PHI at the boundary** — the single most important control.
- Add retry/error handling and logging.
- Swap the source system without rebuilding GHL.

---

## 2. Role of GoHighLevel

GHL is the **growth engine**, never the medical record. It owns:

- **Lead capture & routing** — FB/IG lead ads, Google LSA/PPC, website forms, chat widget, call tracking numbers.
- **Speed-to-lead** — instant SMS/email/call-connect the moment a lead arrives.
- **Nurture & follow-up** — multi-touch sequences until the lead books or goes cold.
- **Reputation** — automated Google/Facebook review requests after completed visits.
- **Reactivation** — win-back campaigns for lapsed clients (Botox due, filler touch-up, etc.).
- **No-show & cancellation recovery** — automated rebooking outreach.
- **2-way conversations** — unified inbox (SMS, email, IG/FB DM, WhatsApp, GBP chat).
- **Reporting** — attribution, pipeline value, response times, review counts, reactivation revenue.
- **Owner visibility** — dashboards, internal alerts, weekly summaries.

**GHL does NOT own:** clinical charting, consent forms with medical detail, treatment records, dosages, photos, payment/PCI data, or the appointment calendar of record.

---

## 3. Role of the Med Spa's Existing CRM/Booking System

The existing system remains the **single source of truth** for:

- The live appointment calendar and provider scheduling.
- Patient charts, treatment history, clinical notes, before/after photos.
- Medical consent forms and intake with health history.
- Payments, memberships, packages, gift cards (PCI scope).
- Inventory (units of Botox, filler, etc.).
- Compliance/audit trail for clinical care.

Its only obligation to the integration is to **emit status events** (or expose them via API/report) so GHL knows when to fire an automation. It should **never be replaced or bypassed** for booking — the front desk keeps working exactly as they do today.

---

## 4. What Data Syncs INTO GHL

Only "marketing-grade" identity + logistics data. The test: *"Would this be fine in a Mailchimp list?"* If yes, sync it. If it reveals a medical condition or treatment, don't.

| Field | Purpose | PHI? |
|---|---|---|
| First name, Last name | Personalization | Low |
| Mobile phone | SMS/calls | Low |
| Email | Email automations | Low |
| Lead source / UTM | Attribution | No |
| Contact creation date | Aging / cold logic | No |
| **Appointment status** (booked/cancelled/no-show/completed) | Triggers | Low* |
| Appointment **date/time** | Reminders, review timing | Low* |
| **Service category** (generic bucket, see §6) | Segmentation, reactivation timing | ⚠️ handle carefully |
| Provider name (optional) | Routing/personalization | Low |
| Appointment **value / ticket** ($) | ROI reporting | No |
| Membership status (member / non-member) | Segmentation | Low |
| Last visit date | Reactivation logic | Low* |
| Preferred location (multi-location spas) | Routing | No |

\* The *fact* of an appointment is lower-risk than the *nature* of treatment. See §6 for the service-category strategy — this is the sensitive edge and must be de-identified into generic buckets.

---

## 5. What Data Should NOT Sync Into GHL

**Never** push into GHL:

- Diagnoses, medical conditions, health history, allergies, medications.
- Specific treatment details tied to a condition (e.g. "hyperhidrosis Botox", "acne scarring", "hormone therapy", "weight-loss/GLP-1", "PRP for hair loss"). These reveal a condition.
- Dosages, units, injection maps, treatment notes.
- Before/after clinical photos.
- Consent form contents, intake health questionnaires.
- Lab results, prescriptions.
- Full payment card numbers / PCI data.
- SSN, insurance IDs, driver's license.
- Anything a reasonable person would consider a medical secret.

**Gray area → bucket it.** Instead of "Botox for TMJ," sync the generic category **"Injectables"** or a neutral code. Instead of "GLP-1 weight loss program," sync **"Wellness"** or **"Membership – Program A."** You still get segmentation and timing without storing a diagnosis.

---

## 6. HIPAA / Privacy-Sensitive Handling

> ⚠️ **Not legal advice.** Med spas that perform medical procedures are typically HIPAA covered entities. If GHL stores PHI, you likely need a **BAA (Business Associate Agreement)** in the chain. Confirm with the client's compliance counsel.

### Strategy: minimize, de-identify, and gate

1. **PHI minimization at the boundary.** The middleware (Make/Zapier) is where you strip and transform. GHL only ever receives fields from the approved list in §4.

2. **Service de-identification map.** Maintain a lookup that converts specific services into neutral marketing categories *before* they reach GHL:

   | CRM service (PHI-adjacent) | GHL value (de-identified) |
   |---|---|
   | Botox for hyperhidrosis, TMJ, migraines | `Injectables` |
   | Dysport, Xeomin, lip filler, cheek filler | `Injectables` |
   | GLP-1 / semaglutide / weight loss | `Wellness Program` |
   | PRP hair restoration | `Restorative` |
   | Acne / rosacea laser, IPL | `Skin` |
   | HydraFacial, chemical peel, microneedling | `Skin` |
   | Hormone / IV therapy | `Wellness Program` |

   The **specific** service stays in the EHR. GHL only knows the bucket. Reactivation timing (e.g. "Injectables clients get a 12-week touch-up nudge") still works.

3. **BAA & platform config.**
   - Ask GHL about a signed BAA and enable any HIPAA/compliance-mode features on the sub-account if the client insists on storing any PHI-adjacent data.
   - Sign BAAs with every middleware vendor in the path (Make and Zapier both offer BAAs on higher tiers) **if** any PHI could transit — even though the goal is that none does.
   - Prefer vendors/regions and tiers that support BAAs from day one so you're not re-architecting later.

4. **Consent & communication compliance.**
   - Capture **explicit SMS/email opt-in** (TCPA). Store consent + timestamp as a custom field.
   - Every SMS includes STOP language; honor unsubscribes automatically (GHL DND).
   - Register **A2P 10DLC** branded messaging for the sub-account to avoid carrier filtering.
   - Keep marketing messages non-clinical: "Time for your next visit?" not "Time for your next Botox for TMJ."

5. **Access control & audit.**
   - Least-privilege GHL user roles; unique logins per staff member (no shared logins).
   - Log all sync activity in Make/Zapier for auditability.
   - Data retention policy: purge stale marketing data on a schedule.

6. **Default posture:** *No PHI in GHL.* Only if a client explicitly needs a specific clinical field for an automation do you revisit — and then only with a BAA and de-identification review.

---

## 7. Access You Need From the Client

Request in a single onboarding checklist (use a secure password manager / vault share — never plaintext email):

**GoHighLevel**
- Agency creates the sub-account (you own the snapshot), OR admin access to their existing location.

**Their CRM / Booking / EHR**
- Admin or API-enabled account, **API key / OAuth credentials**, and webhook configuration rights.
- Confirmation of what events/webhooks the system can emit and what its API exposes.

**Lead sources**
- Facebook/Instagram: admin on the **Business Manager / Page / Ad account** (for Lead Ads → GHL).
- Google: access to **Google Business Profile** (reviews + GBP messaging) and Google Ads (if running).
- Website: ability to embed forms/chat widget or add tracking (CMS login or dev contact).

**Communications & brand**
- Business phone number(s), ability to complete **A2P/10DLC** registration (EIN, business info).
- Domain/DNS access for **email sending domain** authentication (SPF/DKIM/DMARC).
- Google/Facebook review profile URLs.
- Logo, brand colors, hours, service menu, pricing (for messaging + dashboard).

**Middleware**
- Make.com or Zapier seat (you can host on your agency account and bill through).

**Legal**
- Signed **BAA(s)** where applicable; signed marketing/messaging consent process.

---

## 8. Discovery Questions to Ask the Med Spa

**Systems**
1. What CRM/scheduler/EHR do you use? (Exact product + version/plan.)
2. Does it have an API, native GHL/Zapier integration, or webhooks? Can it export CSV?
3. Who administers it? Can we get API access?
4. One location or multiple? Shared or separate calendars/providers?

**Current process**
5. How do leads reach you today (FB, Google, website, referrals, walk-ins, calls)?
6. What happens the moment a new lead comes in? Who responds, how fast?
7. How do you currently handle missed calls?
8. How do you request reviews today?
9. What's your no-show / cancellation rate and current recovery process?
10. Do you ever reach back out to past clients? How?

**Data & compliance**
11. What data are you comfortable leaving your EHR? Any compliance rules/counsel?
12. Do you have a BAA process? Are you a HIPAA covered entity?
13. Do you have SMS/email consent captured at intake?

**Goals & baseline (for ROI proof)**
14. Monthly new leads? Current lead-to-booking rate?
15. Average ticket / lifetime value per client?
16. Which services are highest margin / most repeatable (best reactivation targets)?
17. Typical rebook interval per service (e.g. Botox ~12 weeks)?
18. What does success look like in 90 days?

**Ops**
19. Business hours + after-hours coverage expectations?
20. Who should get internal alerts (owner, front desk, specific provider)?
21. Brand voice — clinical/professional vs. warm/casual?

---

## 9. Connection Methods

Pick the **highest method the source system supports**, in this priority order. Most med spa builds end up as a hybrid: native where it exists, Make/webhooks for the rest.

### 9.1 Native integrations
- **When:** The CRM has a direct GHL connector or both sit on a shared marketplace.
- **Pros:** Cleanest, least maintenance. **Cons:** Rare for med spa EHRs; limited field control.
- **Also native-in-GHL:** Facebook/Instagram Lead Ads, Google Business Profile (reviews + messaging), Google/Outlook calendar, Stripe. Use these directly — no middleware needed.

### 9.2 Webhooks (preferred for real-time CRM → GHL)
- **When:** The CRM can POST an event (appointment.completed, appointment.no_show) to a URL.
- **How:** Point the CRM's webhook at a **GHL Inbound Webhook** or (better) a **Make/Zapier webhook** that filters PHI → then updates the GHL contact + fires the workflow.
- **Pros:** Real-time, event-driven, exactly what speed-to-lead and status automations need.

### 9.3 Make.com (the workhorse middleware)
- **When:** You need field mapping, PHI filtering, conditional logic, or the CRM only has an API (poll) not webhooks.
- **Why Make over Zapier here:** cheaper at volume, visual router/filter logic, easy PHI-strip modules, error handling, BAA available.
- **Pattern:** Trigger (webhook or scheduled API poll) → Filter (drop PHI, map service→bucket) → GHL module (upsert contact, add/remove tag, update field, move pipeline stage).

### 9.4 Zapier
- **When:** Faster to ship, client already uses it, or the CRM has a Zapier app but no Make app.
- **Pros:** Largest app library, simplest UI. **Cons:** pricier at volume, less flexible logic. BAA on higher tiers.

### 9.5 API (custom)
- **When:** No webhooks, no Zapier/Make app — you poll the CRM's REST API on a schedule (e.g. every 5–15 min) for status changes, or push via GHL's API.
- **Tools:** Make/Zapier custom HTTP modules, or a small serverless function (Cloudflare Worker / AWS Lambda) if you need real control. GHL API v2 for writes into GHL.

### 9.6 CSV import/export (fallback / kickoff)
- **When:** The CRM has *no* API — or for the **initial bulk load** of past clients for reactivation.
- **How:** Export client list (marketing-safe columns only) → clean/de-identify → GHL bulk import with tags. For ongoing sync, schedule an export + Make "watch folder / email parser" if truly no API exists.
- **Caution:** Manual, not real-time; last resort for ongoing ops but perfect for the one-time reactivation seed list.

**Decision tree:**
```
CRM has native GHL app?            → use it (+ Make for field control if needed)
Else CRM can send webhooks?        → Webhook → Make (PHI filter) → GHL
Else CRM has API?                  → Make/Zapier scheduled poll → GHL
Else CRM has Zapier/Make app?      → use it
Else only CSV?                     → CSV bulk load now + scheduled export later
Lead sources (FB/Google/website)?  → native GHL integrations, always
```

---

## 10. Events That Trigger Automations

| Event | Origin | GHL reaction (summary) |
|---|---|---|
| **New lead created** | FB/Google/website/CSV | Speed-to-lead: instant SMS + email + call task; add to pipeline `New Lead` |
| **Form submitted** | Website/GHL form | Auto-reply, tag by service interest, notify front desk, start nurture |
| **Missed call** | Call tracking / GHL number | Instant "Sorry we missed you" SMS (missed-call text-back), create task |
| **Appointment booked** | CRM webhook | Move pipeline → `Booked`, confirmation + reminder sequence, stop nurture |
| **Appointment cancelled** | CRM webhook | Move → `Cancelled`, rebooking outreach, alert front desk |
| **No-show** | CRM webhook | Move → `No-Show`, no-show recovery sequence, alert |
| **Appointment completed** | CRM webhook | Move → `Completed`, start review request + post-care check-in, set reactivation timer |
| **Review request ready** | Completed + delay | Send review ask (SMS/email), route happy→Google, unhappy→private feedback |
| **Lead went cold** | No engagement in X days | Move → `Cold`, long-term nurture / drip, "still interested?" |
| **Client due for reactivation** | Last-visit + interval elapsed | Win-back campaign, offer, book-now link |

---

## 11. Custom Fields in GHL

Create these under Settings → Custom Fields (group them under a "Med Spa Integration" folder). Keep them minimal and non-clinical.

| Field name | Key | Type | Notes |
|---|---|---|---|
| CRM Contact ID | `crm_contact_id` | Text | Foreign key back to source system |
| Lead Source | `lead_source` | Dropdown | FB, Google, Website, Referral, Walk-in |
| Service Interest | `service_interest` | Dropdown | **De-identified buckets only** |
| Appointment Status | `appt_status` | Dropdown | Booked / Cancelled / No-Show / Completed |
| Appointment Date | `appt_date` | Date | Next/last appt |
| Last Visit Date | `last_visit_date` | Date | Drives reactivation |
| Reactivation Due Date | `reactivation_due` | Date | Computed = last_visit + interval |
| Service Category | `service_category` | Dropdown | Injectables / Skin / Wellness / Restorative |
| Appointment Value | `appt_value` | Monetary | ROI reporting |
| Provider | `provider` | Text | Optional routing |
| Location | `location` | Dropdown | Multi-location spas |
| Membership Status | `membership_status` | Dropdown | Member / Non-member |
| SMS Consent | `sms_consent` | Checkbox | TCPA |
| SMS Consent Date | `sms_consent_date` | Date | Audit |
| Review Status | `review_status` | Dropdown | Requested / Left / Declined |
| No-Show Count | `no_show_count` | Number | Escalation logic |

---

## 12. Tags in GHL

Consistent, namespaced tags (prefix by category so they sort and filter cleanly):

**Source:** `src-facebook`, `src-google`, `src-website`, `src-referral`, `src-walkin`, `src-csv-import`

**Lifecycle:** `lead-new`, `lead-nurturing`, `lead-cold`, `client-active`, `client-lapsed`

**Service bucket:** `svc-injectables`, `svc-skin`, `svc-wellness`, `svc-restorative`

**Appointment:** `appt-booked`, `appt-cancelled`, `appt-noshow`, `appt-completed`

**Automation state:** `speed-to-lead-done`, `reminder-sent`, `review-requested`, `review-left`, `reactivation-active`, `noshow-recovery-active`

**Flags:** `vip`, `do-not-contact`, `member`, `multi-noshow`

> Keep the list tight. Tags are for *routing and segmentation*, not a second database — anything queryable belongs in a custom field.

---

## 13. Pipeline Stages in GHL

### Pipeline A — "New Patient Acquisition" (leads → first visit)
1. **New Lead** — just arrived, speed-to-lead firing
2. **Contacted / Engaged** — replied or reached
3. **Consultation Requested**
4. **Booked** — appointment on the CRM calendar
5. **Completed – First Visit** — became a client
6. **Cold / Lost** — no engagement

### Pipeline B — "Client Lifecycle & Reactivation" (existing clients)
1. **Active Client**
2. **Post-Visit Follow-up**
3. **Due for Reactivation**
4. **Reactivation – In Progress**
5. **Reactivated / Rebooked**
6. **Lapsed – Long Term**

> Two pipelines keep acquisition ROI separate from retention ROI — which is exactly how the owner thinks about the money, and makes the dashboard obvious.

---

## 14. Workflows in GHL

Core workflow set (each maps to events in §10):

1. **Speed-to-Lead** — new lead → instant multi-channel outreach (§15)
2. **Missed-Call Text-Back** — missed call → instant SMS + task
3. **Form/Auto-Reply & Router** — form submit → confirm, tag interest, notify, start nurture
4. **New-Lead Nurture** — 7–14 day multi-touch until booked or cold
5. **Appointment Confirmation & Reminders** — booked → confirm + reminders (24h/2h)
6. **No-Show Recovery** — no-show → rebooking sequence (§17)
7. **Cancellation Rebooking** — cancelled → offer to reschedule
8. **Review Request** — completed → review ask + reputation routing (§16)
9. **Post-Care Check-in** — completed → wellbeing / upsell touch
10. **Reactivation** — reactivation-due → win-back campaign (§18)
11. **Cold-Lead Long-Term Drip** — monthly value/offer touch
12. **Internal Alerts** — owner/front-desk notifications (§19)
13. **Consent & Compliance** — capture opt-in, honor DND/STOP
14. **Dashboard Data Maintenance** — update custom values/counters for reporting

---

## 15. Speed-to-Lead Automation

**Goal:** contact every new lead in **under 60 seconds**, 24/7. This is the flagship "wow" for the owner.

**Trigger:** New contact created via FB/Google Lead Ad, website form, or CRM lead webhook (tag `lead-new`).

**Sequence:**
```
0 sec   → SMS #1: "Hi {{first_name}}, it's {{spa}}! Thanks for reaching out about
                   {{service_interest}}. Are you looking to book a consult this week? 😊"
0 sec   → Email #1: brief intro + booking link + what to expect
0 sec   → Internal alert to front desk (SMS/Slack): "🔥 New lead: {{name}} / {{phone}}"
2 min   → If no reply → optional auto-call connect (ring front desk, then lead) OR call task
30 min  → If no reply → SMS #2: gentle nudge + booking link
1 day   → If no reply → SMS #3 / Email #2: social proof (before/afters, review snippet)
3 days  → If no reply → move to New-Lead Nurture
On reply at any point → stop sequence, notify staff, move pipeline → Contacted
On booking → stop, move → Booked, tag speed-to-lead-done
```

**Build notes:**
- Use business-hours branching: after-hours leads still get instant SMS/email; live-call attempts wait for open hours.
- Respect `sms_consent`. Include STOP language.
- All copy uses de-identified `service_interest` bucket.
- Booking link points to their **real CRM booking page** (or a GHL calendar that syncs to it) — never a parallel calendar.

---

## 16. Review Automation

**Goal:** systematically convert completed visits into Google/Facebook reviews while catching unhappy clients privately.

**Trigger:** `appt-completed` (from CRM webhook), after a delay (e.g. 2–4 hours or same-evening).

**Reputation-routing flow (NPS-style gate):**
```
Completed + delay
  → SMS/Email: "How was your visit with {{provider}} today, {{first_name}}?  (1–5)"
      ├─ 4–5 (happy)  → "So glad! Would you share a quick review? {{google_review_link}}"
      │                  → tag review-requested; on detect/manual → review-left
      └─ 1–3 (unhappy)→ "We'd love to make it right — what happened?" (private form → owner alert)
                         → tag needs-service-recovery; DO NOT send public link
```

**Build notes:**
- Use GHL's native **Reputation / Review Request** + Google Business Profile connection so reviews post to Google directly.
- Cap frequency: don't ask the same client more than once per N days.
- Only fire on `appt-completed` — never on no-show/cancelled.
- Keep clinical detail out; reference `provider` and generic "visit," not the treatment.

---

## 17. No-Show Recovery

**Goal:** recover revenue from no-shows automatically; reduce future no-shows.

**Trigger:** `appt-noshow` from CRM webhook → move pipeline → `No-Show`.

**Sequence:**
```
0 min   → SMS: "Hi {{first_name}}, we missed you today! No worries — want to grab a new time?
                {{booking_link}}"
0 min   → Internal alert to front desk (so a human can also call)
2 hrs   → If no rebook → SMS/Email with 1-tap reschedule
1 day   → If no rebook → call task for front desk + softer nudge
3 days  → If no rebook → light incentive (owner-approved) OR move to nurture
Increment no_show_count. If ≥2 → tag multi-noshow (front desk may require deposit).
On rebook → stop, move → Booked.
```

**Prevention loop:** feed the confirmation/reminder workflow (24h + 2h reminders with 1-tap confirm) to cut no-shows at the source.

---

## 18. Reactivation Campaigns

**Goal:** bring back lapsed clients — usually the fastest ROI because the list already exists.

**Two entry points:**
- **Bulk seed (kickoff):** CSV import of past clients → tag `client-lapsed` + `src-csv-import`, set `last_visit_date`, compute `reactivation_due`.
- **Ongoing:** each `appt-completed` sets `reactivation_due = last_visit + service interval` (e.g. Injectables 12 wks, Skin 6 wks, Wellness per program). A daily workflow checks for due dates.

**Sequence (personalized by service bucket, not by diagnosis):**
```
reactivation_due reached  → move → Due for Reactivation, tag reactivation-active
Touch 1 (SMS): "Hi {{first_name}}, it's been a while! Ready to refresh your results?
                Book here 👉 {{booking_link}}"
Touch 2 (Email, +3d): value + before/after + limited-time member offer
Touch 3 (SMS, +7d): urgency / seasonal offer (owner-approved)
Touch 4 (Email, +14d): last call
On booking → move → Reactivated/Rebooked, tag client-active, clear lapsed
No response after sequence → Lapsed – Long Term (quarterly drip)
```

**Segment offers** by `service_category` and `membership_status`. Members get loyalty framing; non-members get a return incentive.

---

## 19. Internal Alerts

Keep staff in the loop without them living in GHL.

| Event | Recipient | Channel | Message |
|---|---|---|---|
| New lead | Front desk | SMS + Slack + GHL notification | "🔥 New lead: {{name}} {{phone}} — {{source}}. Respond fast." |
| Missed call | Front desk | SMS | "📞 Missed call from {{phone}}. Auto-text sent. Call back." |
| Hot reply ("book", "price", "yes") | Front desk / owner | SMS | "💬 {{name}} is ready to book!" |
| No-show | Front desk | SMS + task | "⚠️ No-show: {{name}}. Recovery started." |
| Unhappy review (≤3) | **Owner** | SMS + email | "🚨 Service recovery needed: {{name}} rated {{score}}." |
| VIP / high-value lead | Owner | SMS | "⭐ High-value lead: {{name}} ({{service}})." |
| Daily digest | Owner | Email 8am | New leads, booked, no-shows, reviews, reactivations. |

Use GHL **internal notifications** + **Slack** integration (or SMS to staff). Keep alert volume low enough that staff don't tune them out — alert on *action-needed*, digest the rest.

---

## 20. Owner Dashboard

Build in GHL **Dashboards** (widgets) + custom values, so the owner sees value at a glance without training.

**Top KPIs (cards):**
- New leads (this month) + source breakdown
- **Avg speed-to-lead response time** (the flagship metric)
- Leads → booked conversion rate
- Appointments: booked / completed / no-show / cancelled
- No-shows recovered (count + $ value)
- Reviews requested vs. left; current Google rating
- Reactivations booked (count + $ value)
- **Attributed revenue** (pipeline $ from `appt_value`) — the ROI number

**Pipeline widgets:** live view of both pipelines with $ per stage.

**Trend charts:** leads over time, review growth, reactivation revenue over time.

**The money slide:** one prominent tile — *"Revenue influenced this month: $X"* — summing recovered no-shows + reactivations + attributed new-client revenue. This is what renews the retainer.

> Keep it to one screen. Owners want proof, not analytics. If they ask for more, add a second "detail" tab.

---

## 21. Testing Before Go-Live

**Sandbox first.** Use a test contact (your own phone/email) and the CRM's test/staging mode if available.

**Test matrix — fire each event and verify GHL reaction:**

| Test | Expected |
|---|---|
| Submit website form | Contact created, tagged, speed-to-lead SMS+email within seconds, front-desk alert |
| Create FB/Google lead (Lead Ads Testing tool) | Same as above, `src-facebook`/`src-google` |
| Missed call to tracking number | Missed-call text-back fires |
| CRM: book appointment | Pipeline → Booked, confirmation + reminders scheduled, nurture stops |
| CRM: cancel | Pipeline → Cancelled, rebooking outreach |
| CRM: mark no-show | Pipeline → No-Show, recovery sequence, `no_show_count`++ |
| CRM: mark completed | Pipeline → Completed, review request scheduled, `reactivation_due` set |
| Rate review 5 | Google link sent |
| Rate review 2 | Private feedback + owner alert, NO public link |
| Advance clock / set past reactivation_due | Reactivation campaign starts |
| Reply STOP | Contact goes DND, all sends stop |

**PHI leak audit (critical):** run a real completed-appointment sync and inspect the GHL contact — confirm **no** diagnosis/treatment detail landed; only the de-identified bucket. Check Make/Zapier logs for the same.

**Deliverability:** send test SMS/email; confirm A2P registered, DKIM/SPF passing, not landing in spam.

**Load/dedupe:** import a small CSV batch; confirm no duplicate contacts (match on phone/email/`crm_contact_id`).

**Sign-off checklist** with the owner before flipping live traffic.

---

## 22. Common Failure Points

| Failure | Prevention |
|---|---|
| **PHI leaks into GHL** | De-identify at middleware; audit every field; BAA in chain; §6 |
| **Duplicate contacts** | Dedupe key = phone/email/`crm_contact_id`; upsert not create |
| **SMS blocked/filtered** | Register A2P 10DLC; branded sender; STOP compliance |
| **Emails to spam** | Authenticate domain (SPF/DKIM/DMARC); warm up sender |
| **Double-booking / calendar drift** | GHL never owns the calendar of record; book into their CRM only |
| **Webhook silently fails** | Make/Zapier error handling + retry + failure alert to you |
| **Timezone bugs in reminders** | Set location timezone; store dates in ISO; test DST |
| **Over-messaging clients** | Frequency caps; central "recently contacted" check; suppression tags |
| **No consent / TCPA risk** | Capture + store `sms_consent`; only message opted-in |
| **Automations fire on wrong status** | Exact status-value mapping; test every branch (§21) |
| **CRM has no API** | CSV bulk + scheduled export fallback; set expectations early |
| **Stale reactivation timers** | Daily maintenance workflow recalculates `reactivation_due` |
| **Owner can't see value** | Dashboard "revenue influenced" tile; weekly digest email |
| **One-off spaghetti build** | Everything in a reusable snapshot (§24) |

---

## 23. What to Customize Per Med Spa

- Brand: name, logo, colors, tone, hours, booking link, review URLs.
- **Service → bucket map** (their exact menu → your de-identified categories).
- **Reactivation intervals** per service (Botox 12 wks vs. facial 6 wks, etc.).
- Lead sources actually in use (which native integrations to connect).
- CRM connection method (native/webhook/API/CSV) and field mapping specifics.
- Alert recipients & channels (who gets what).
- Offers/incentives (owner-approved copy).
- Multi-location routing (if applicable).
- A2P/DKIM records (per business).
- Baseline metrics for the ROI dashboard.

---

## 24. What Becomes a Reusable Snapshot

Build once, clone forever. The **GHL Snapshot** includes:

- All **custom fields** (§11) and **tags** (§12)
- Both **pipelines** + stages (§13)
- All **workflows** (§14) with `{{custom_value}}` placeholders instead of hardcoded brand text
- **Message templates** (SMS/email) with merge fields
- **Dashboard** layout + widgets (§20)
- **Forms / funnels** (lead capture, review gate, private feedback)
- **Custom Values** for brand config (spa name, booking link, review link, offers, intervals) — so a new deploy = fill in ~15 custom values, not rebuild
- **Standard Make/Zapier scenario templates** (CRM→GHL sync with PHI filter) exported as blueprints
- **Onboarding docs:** discovery questionnaire (§8), access checklist (§7), service-bucket map template, go-live test checklist (§21)

**Per-CRM add-on packs:** a small library of pre-mapped Make blueprints for the common med spa systems (Aesthetic Record, Boulevard, Zenoti, Mangomint, Vagaro, Jane, Acuity, Mindbox/Mindbody). Detect the client's CRM → drop in the matching blueprint.

> Target: **new med spa live in 1–2 days** = import snapshot → set custom values → connect their CRM with the matching blueprint → seed reactivation CSV → run test matrix → go live.

---

## 25. Sales Demo Script

**Frame (30 sec):** *"You keep your booking system exactly as-is. We add a growth layer on top that answers every lead in under a minute, follows up automatically, recovers no-shows, gets you 5-star reviews, and wins back past clients — all without touching your patient records."*

**Demo (5 min) — show, don't tell:**
1. Submit a fake lead on your phone → **their phone buzzes with the auto-SMS in ~10 seconds.** ("This happens 24/7, even at 11pm on a Sunday.")
2. Show the no-show recovery text and the "revenue recovered" number.
3. Show a review request → a new 5-star Google review appearing.
4. Show the reactivation campaign hitting a lapsed-client list. ("You already have hundreds of these.")
5. Open the **dashboard** → point at *"Revenue influenced this month: $X."*

**Value math:** *"You get ~X leads/month. Right now maybe Y% book because follow-up is slow. Getting to sub-minute response typically lifts that meaningfully. Plus no-show recovery + reactivating past clients. If this books even 3–4 extra treatments a month at your ~$Z ticket, it pays for itself several times over."*

**Objection handling:**
- *"Is my patient data safe?"* → *"Your medical records never leave your system. We only sync names, phone, and appointment status — nothing clinical. Signed BAA, HIPAA-conscious by design."*
- *"Do I have to switch systems?"* → *"No. You keep booking exactly how you do today. This sits on top."*
- *"Is it complicated for my staff?"* → *"They get simple text alerts and one dashboard. The automations do the work."*

**Close:** *"I can have this live in a couple of days. Want me to set it up on a 90-day pilot so you can see the revenue before you commit long-term?"*

---

## Appendix A — Example Field Mappings

### A.1 CRM Appointment Status → GHL Pipeline Stage

| CRM status | GHL pipeline / stage | Tag | Workflow fired |
|---|---|---|---|
| `scheduled` / `booked` | Acquisition → **Booked** | `appt-booked` | Confirmation & Reminders |
| `cancelled` | Acquisition → **Cancelled** | `appt-cancelled` | Cancellation Rebooking |
| `no_show` | Acquisition → **No-Show** | `appt-noshow` | No-Show Recovery |
| `completed` | Acquisition → **Completed – First Visit** | `appt-completed` | Review Request + Reactivation timer |
| `rescheduled` | (stays) **Booked**, update `appt_date` | `appt-booked` | Reminders re-scheduled |

### A.2 CRM Completed Appointment → Review Request

```
CRM webhook: appointment.completed
  → Make: strip PHI, map service→bucket
  → GHL: upsert contact, set appt_status=Completed, last_visit_date=today,
         reactivation_due = today + interval[service_category]
  → Move pipeline → Completed
  → Start "Review Request" workflow (delay 3h)
  → Start "Post-Care Check-in" (delay 1d)
```

### A.3 CRM No-Show → No-Show Recovery

```
CRM webhook: appointment.no_show
  → Make: PHI filter
  → GHL: set appt_status=No-Show, no_show_count += 1
  → Move pipeline → No-Show, tag noshow-recovery-active
  → Start "No-Show Recovery" workflow
  → Internal alert → front desk
  → If no_show_count >= 2 → tag multi-noshow
```

### A.4 Website Lead → Instant SMS

```
Website form submit (GHL form or webhook)
  → GHL: create contact, tag src-website + lead-new + svc-[interest]
  → Move pipeline → New Lead
  → Start "Speed-to-Lead" workflow (SMS #1 @ 0s)
  → Internal alert → front desk
```

### A.5 Facebook/Google Lead → Speed-to-Lead

```
FB/IG Lead Ad (native GHL integration) OR Google LSA/form
  → GHL: create contact, tag src-facebook|src-google + lead-new
  → Map form's service question → service_interest bucket
  → Move pipeline → New Lead
  → Start "Speed-to-Lead" workflow (SMS + email + call task @ 0s)
  → Internal alert → front desk with source
```

### A.6 Field-Level Mapping (CRM record → GHL contact)

| CRM field | GHL field/key | Transform |
|---|---|---|
| `patient.first_name` | First Name | direct |
| `patient.last_name` | Last Name | direct |
| `patient.mobile` | Phone | normalize to E.164 |
| `patient.email` | Email | lowercase |
| `patient.id` | `crm_contact_id` | direct (dedupe key) |
| `appointment.status` | `appt_status` | map enum (A.1) |
| `appointment.datetime` | `appt_date` | ISO + location TZ |
| `appointment.service_name` | `service_category` | **lookup → de-identified bucket** |
| `appointment.price` | `appt_value` | numeric |
| `appointment.provider` | `provider` | direct (optional) |
| `patient.location` | `location` | map |
| `patient.member_flag` | `membership_status` | Member/Non-member |
| *(diagnosis, notes, dosage, photos)* | ❌ | **NOT MAPPED — stays in CRM** |

---

## Appendix B — Master Build Checklist

**Phase 0 — Discovery & Access**
- [ ] Run discovery questions (§8); record CRM product + integration capability
- [ ] Collect access (§7) via secure vault; sign BAA(s)
- [ ] Capture baseline metrics (leads, conversion, ticket, intervals)
- [ ] Build the client's **service → bucket** map

**Phase 1 — GHL Foundation (from snapshot)**
- [ ] Import agency snapshot into new sub-account
- [ ] Fill in Custom Values (brand, booking link, review link, offers, intervals)
- [ ] Verify custom fields (§11), tags (§12), pipelines (§13), workflows (§14)
- [ ] Register A2P 10DLC; authenticate email domain (SPF/DKIM/DMARC)
- [ ] Connect native integrations: FB/IG, Google Business Profile, calendar

**Phase 2 — Integration Layer**
- [ ] Choose connection method per §9 decision tree
- [ ] Deploy Make/Zapier scenario with **PHI filter** + field mapping (Appendix A)
- [ ] Configure CRM webhooks (or API poll) for status events
- [ ] Set up dedupe on phone/email/`crm_contact_id`
- [ ] Add error handling + failure alerts on the sync

**Phase 3 — Data Seed**
- [ ] Export past-client CSV (marketing-safe columns only), de-identify
- [ ] Bulk import → tag `client-lapsed`, set `last_visit_date` + `reactivation_due`

**Phase 4 — Test (§21)**
- [ ] Run full test matrix (every event → expected reaction)
- [ ] **PHI leak audit** on a real completed sync
- [ ] Deliverability check (SMS + email)
- [ ] Owner sign-off

**Phase 5 — Go Live**
- [ ] Enable live traffic on all sources
- [ ] Turn on internal alerts + daily digest
- [ ] Confirm dashboard populating (§20)

**Phase 6 — Prove & Retain**
- [ ] Week 1 check-in: response times, deliverability, any misfires
- [ ] 30/60/90-day ROI review using dashboard "revenue influenced"
- [ ] Feed learnings back into the master snapshot

---

*End of plan.*
