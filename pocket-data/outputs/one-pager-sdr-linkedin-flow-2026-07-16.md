# SDR LinkedIn Outreach — One Combined Flow (One-Pager)

> EMAsphere · July 2026 · Proposal to align our three parallel initiatives (call-prep plan, SDR Agent, TA outreach) on a single workflow.
> Full analysis: `pocket-data/outputs/rapport-workflow-sdr-linkedin-hubspot-2026-07-16.md`

## The problem

"I see an interesting LinkedIn profile → I find their phone → I send a personalized message → I log it in HubSpot" takes **15–25 min per profile** today, and three of us are building separate solutions for it.

## The answer in one line

**Everything automates except one click** — the "send" button stays human (LinkedIn ToS). Brief, phone, drafting and logging run on tools **we already pay for**. Human time drops to **~2–3 min per profile** (~1h15–1h50 saved per day at 5 profiles/day).

## Target workflow

| Step | How | Tool (already in-house) |
|---|---|---|
| 1. Read the profile | Auto-generated prospect brief: ICP fit, triggers, competitors, suggested hook | **SDR Agent** (Chrome extension in HubSpot, `/api/brief`) — built, deployment to finish |
| 2. Get the phone | **Not scraped from LinkedIn** — waterfall enrichment from the LinkedIn URL returns a verified mobile in ~60–65% of cases, written to HubSpot `mobilephone` (never overwrites) | **FullEnrich** (paid, wired) |
| 3. Write the message | AI drafts it personalized (persona, language, channel); **a human copy-pastes and clicks send** (~10 s) | **Claude** / `/api/pitch` |
| 4. Log in HubSpot | Fully automatic: contact (check-before-create — ~71% of our 278k contacts already have a LinkedIn URL), native "LinkedIn message" activity, message content | **Claude → HubSpot** |

## What we log (shared convention)

- ✅ The **contact** (search before create — avoid duplicates)
- ✅ The **outreach activity** (native "LinkedIn message" type, in the timeline like a call or email)
- ✅ The **message content** (whoever picks up the thread knows what was said)
- ❌ **Never the prospect's LinkedIn activity** (posts/comments read for context) — GDPR minimization; only the chosen angle, reworded, may go in a note

## Two use cases — two tools, one bridge

| | **A — Volume** (list-based, 50–500) | **B — High-intent** (1 spotted profile) |
|---|---|---|
| Tool | **Lemlist** sequence (invite → message → follow-up) | **Claude**: brief + 1:1 draft + logging |
| Send | Automated = LinkedIn ToS risk **accepted explicitly at team level** (per-SDR accounts, volume caps) — never a personal setup | Human copy-paste — zero risk |
| Phone | FullEnrich batch (≤100), empty fields only | FullEnrich one-by-one |

**The bridge**: Claude writes the personalized icebreaker and injects it as a **custom variable in the Lemlist sequence** — volume automation *and* real personalization, 100% existing tooling.

## Red lines (non-negotiable)

1. No phone scraping from LinkedIn (ToS + GDPR) — pointless anyway, FullEnrich does it compliantly.
2. No automated LinkedIn sends without an explicit team-level risk decision — "more natural" sequencers lower *detection*, not *ToS exposure*.
3. Nothing the prospect did on LinkedIn gets persisted in the CRM.

## Decisions needed (30-min sync, the three of us + manager)

1. Adopt the logging convention above as team standard.
2. One single arbitration on automated sends (sequencer / PhantomBuster / Sales Navigator) — owned by the manager, applies to everyone.
3. Finish SDR Agent deployment (Vercel + extension) and onboard TA on it — one flow, not two.
4. Pilot: run 2–3 real profiles through the case-B flow this week to measure the actual time saved.
