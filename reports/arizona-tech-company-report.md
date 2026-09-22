# Arizona Technology Company Research Report

**Prepared for:** Anuj Wadi (MS Robotics & Autonomous Systems, ASU, May 2026)
**Purpose:** Research database of Arizona-based technology companies for direct job-search cold outreach (research only — no emailing, no applying was performed as part of this task).
**Snapshot date:** 2026-09-22

> **This is a best-effort snapshot from live web search performed on 2026-09-22, not an exhaustive census of Arizona technology companies.** Arizona has well over 700 software companies alone (per Gregslist/PHX FWD), plus hundreds more in AI, robotics, aerospace, and tech-enabled verticals. Further iterative searching — especially direct crawling of aggregator sites (Built In, Gregslist, Tracxn, Wellfound, Crunchbase, Inven.ai, Seedtable), the Arizona Technology Council's 750+-member business directory, and LinkedIn company searches — would surface significantly more companies than could be captured in this session.

## Headline numbers

| Metric | Count |
|---|---|
| Total unique AZ tech companies discovered and cataloged | **72** |
| Outreach-eligible (excludes staffing/recruiting firms and company-wide ITAR/clearance-restricted companies) | **72** (0 of the 72 catalogued companies were found to be company-wide ITAR/clearance-restricted; restricted firms were placed in `excluded-companies.csv` instead and are not counted in the 72) |
| Recruiting/staffing firms identified and excluded | **12** |
| ITAR/clearance company-wide restricted companies excluded | **1** (General Dynamics Mission Systems) |
| Companies flagged UNCLEAR on ITAR/clearance status (kept, not assumed clear) | **3** (Katalyst Space Technologies, Phantom Space, KinetX Aerospace) |
| Other exclusions (defunct business, no confirmed AZ presence) | **4** (Edgio/Limelight Networks — defunct; Emerald AI, Culdesac, Nuro — no confirmed current AZ engineering presence) |
| Companies with a currently visible/confirmed relevant open role | **15 of 72** |
| Companies with at least one verified named contact (name/title from a public source) | **5 companies / 6 named contacts** |
| Companies rated HIGH confidence | **17** |
| Companies rated MEDIUM confidence | **27** |
| Companies rated LOW confidence (recommend direct re-verification before outreach) | **28** |

## Outreach priority breakdown

| Priority | Meaning | Count |
|---|---|---|
| P1 | Strong evidence of relevant tech work + confirmed AZ presence + no ITAR/clearance issue | 15 |
| P2 | Relevant company, weaker/unconfirmed hiring evidence | 25 |
| P3 | Needs more direct verification before outreach | 32 |

## Breakdown by city

| City | Companies |
|---|---|
| Scottsdale | 20 |
| Phoenix | 20 |
| Chandler | 7 |
| Tucson | 7 |
| Tempe | 6 |
| Mesa | 4 |
| Flagstaff | 3 |
| Casa Grande | 1 |
| Goodyear | 1 |
| Gilbert | 1 |
| Prescott | 1 |
| Phoenix (planned facility — Hadrian) | 1 |

No verified companies were found for this session in Peoria, Glendale, Surprise, Avondale, Sedona, Yuma, Queen Creek, Marana, Oro Valley, or Buckeye specifically as standalone tech-company HQs (some of these cities host manufacturing/logistics facilities of larger companies such as LG Energy Solution in Queen Creek, but no dedicated software/AI/robotics engineering employer could be confirmed there in this session). This is a strong candidate area for further searching.

## Breakdown by industry (grouped)

| Industry group | Companies |
|---|---|
| IT/Software Consulting (incl. custom dev, BI, Salesforce/cloud consultancies) | 10 |
| AI/ML (incl. computer vision, LLM/GenAI) | 9 |
| Other (wellness tech, footwear tech, manufacturing automation, etc.) | 9 |
| Edtech | 8 |
| Healthtech | 7 |
| Aerospace/Space | 6 |
| SaaS/Enterprise Software | 6 |
| Robotics | 5 |
| Automotive/Mobility Tech | 3 |
| Proptech | 3 |
| Cybersecurity | 3 |
| Semiconductor | 2 |
| Fintech | 1 (several more fintech candidates were found but could not be verified strongly enough for inclusion — see Gaps below) |

## Breakdown by company size (estimated)

| Size band | Companies |
|---|---|
| 1-10 / 1-50 employees (very small/early-stage) | ~24 |
| 11-50 employees | 16 |
| 50-200 employees | 18 |
| 200-500 employees | 9 |
| 500-1000 employees | 7 |
| 1000-5000 employees | 4 |
| 5000+ employees (large/public) | 7 |

## Hiring signal strength

- **15 of 72** companies (21%) have a confirmed, currently visible relevant open role (Software/Backend/Full-Stack/ML/Computer Vision/Robotics Engineer, entry-to-mid level) as of the verification date, sourced from company careers pages or job aggregators (e.g., TSMC Arizona's Phoenix fullstack SWE req, Katalyst Space Technologies' multiple software/GNC engineer reqs, Trainual's engineering careers page listing 3-6 open full-stack roles, RadiusAI's CV/ML engineer openings, OneOrigin's AI platform engineer and internship openings, Botco.ai's GenAI careers page).
- The remaining companies are marked `current_hiring: UNCLEAR` rather than assumed "no" — absence of a confirmed posting at verification time does not mean the company never hires; it means this session could not confirm an open req and recommends checking the company's own careers page directly before outreach.
- **Contacts:** because this session had no Apollo/LinkedIn-scraping/contact-enrichment access, verified named contacts are limited to 6 individuals across 5 companies, all sourced from public founder/leadership bios or LinkedIn profile titles surfaced directly in search results (no emails were found or guessed for any of them).

## ITAR / clearance handling

Per the scoping rules, a company was excluded for ITAR/clearance only when the **entire company** appeared to operate under defense/export-control restrictions:

- **Excluded (COMPANY_WIDE):** General Dynamics Mission Systems (Scottsdale) — the large majority of its Scottsdale engineering postings require active DoD Secret or TS/SCI clearance, and its core business is classified defense mission systems.
- **Kept but flagged UNCLEAR (not assumed clear):** Katalyst Space Technologies (Flagstaff), Phantom Space (Tucson), and KinetX Aerospace (Tempe) — all do space/satellite/NASA-adjacent work where export-control exposure is plausible for at least part of the business, but no explicit company-wide ITAR statement was found. These are retained in `companies.csv` with `itar_status`/`clearance_status` = `UNCLEAR` per the instruction to never assume `NONE_FOUND` without evidence.
- All other companies were marked `NONE_FOUND` only when no defense/export-control signal was found at all in available search results; this should still be treated as "no evidence found" rather than a hard guarantee.

## Recruiting/staffing firm exclusions

12 firms were identified whose primary business is recruiting/staffing/placement (e.g., PrideStaff, Vaco, Next Step Systems, Parallel Partners, Frontline Source Group, TEKsystems, Insight Global, Aerotek, Blue Signal Search, SalesFirst Recruiting, Renaissance Personnel Group, AppleOne Employment Services). These are logged in `excluded-companies.csv`, not `companies.csv`. Internal recruiting teams at normal tech companies (e.g., a "Talent Acquisition" contact at Trainual) were **not** treated as a reason to exclude the company itself.

## Key limitations and gaps (read before using this data)

1. **No Apollo / LinkedIn-scraping / contact-enrichment tool access in this session.** `cto_email`, `founder_email`, `engineering_lead_email`, and `general_contact_email` are blank for essentially every row, as expected and specified. Only 6 named contacts (with title and, where available, a directly-surfaced LinkedIn URL) were captured — never an email.
2. **Most aggregator sites were blocked by the network egress proxy** (builtin.com, gregslist.com, seedtable.com, failory.com, inven.ai, and most individual company websites such as webpt.com and botco.ai returned `EGRESS_BLOCKED` on direct fetch). All verification in this session was therefore performed via WebSearch result snippets and summaries (which do cite underlying source URLs) rather than direct page fetches. This is noted per-row in `source_urls` and in `verification-log.csv`. Companies verified this way carry MEDIUM or LOW confidence and are flagged for direct re-verification before outreach.
3. **28 of 72 companies are LOW confidence** — typically very small/local shops (e.g., Virga Labs, TucsonBizz, Eightfold Technology, Pinnacle Aerospace) found via a single aggregate listing snippet with no independent confirmation of current operating status, team size, or hiring. These should be personally re-verified (visit their website, check LinkedIn headcount, look for a careers page) before any outreach.
4. **Coverage is uneven by city.** Scottsdale and Phoenix dominate because that's where most searchable AZ tech press/listings concentrate. Tucson, Flagstaff, and Tempe have solid coverage; Gilbert, Chandler, Goodyear, Prescott, Mesa, and Casa Grande have only 1-7 companies each; several target cities (Peoria, Glendale, Surprise, Avondale, Sedona, Yuma, Queen Creek, Marana, Oro Valley, Buckeye) returned no clearly identifiable dedicated tech-company HQ in this session's searches and would benefit from further, more localized searching (e.g., city economic development pages, local chamber of commerce directories).
5. **Some larger companies were deliberately excluded even though they have an Arizona office**, when the AZ presence appeared to be a generic operations/manufacturing/sales site rather than a software-engineering hub (e.g., Amazon, PayPal, American Express, Uber Freight Phoenix offices were considered but not added, to keep the list focused on companies where a cold email to a founder/CTO/eng-lead is a realistic outreach motion rather than a mega-corp generic req). This is a judgment call the person may want to revisit — very large AZ offices of Fortune 500 companies (Amazon dev center in Tempe, American Express Phoenix campus, PayPal Scottsdale/Chandler, USAA Phoenix, JPMorgan Tempe/Chandler, Wells Fargo AZ, Vanguard Scottsdale) do hire large numbers of new-grad SWEs and were not systematically pursued here — flagged as a clear area for follow-up if the person wants "big company AZ office" leads in addition to native AZ startups/scale-ups.
6. **A handful of fintech and small-startup names surfaced in search snippets could not be independently verified enough to include with confidence** (e.g., "Soaren," "Emailed Checks" as a standalone brand) and were left out entirely rather than padding the list with unverifiable entries, per the quality bar in the task.
7. Nikola Corporation and Lucid Group (Casa Grande) are included but flagged with caution — both have experienced significant financial/operational turmoil (Nikola: bankruptcy-adjacent distress; Lucid's AZ site is primarily a manufacturing plant, with core software engineering based in California) — verify current operating/hiring status before investing outreach effort there.

## How this research was conducted

- ~30 distinct WebSearch queries were run across Arizona cities (Phoenix, Tempe, Scottsdale, Chandler, Mesa, Gilbert, Tucson, Flagstaff, Prescott, Goodyear, Queen Creek, Casa Grande, and more) crossed with industry verticals (AI/ML, robotics, fintech, healthtech, edtech, proptech, cybersecurity, computer vision, aerospace/space, semiconductor, logistics/warehouse automation, autonomous vehicles) and source types (Built In, Wellfound, Tracxn, Crunchbase, Seedtable, Failory, Gregslist, Y Combinator, Arizona Technology Council, Skysong Innovations, Tech Launch Arizona).
- Every company added to `companies.csv` has at least one cited `source_urls` entry.
- Companies were cross-checked for (a) real company + website, (b) genuine Arizona presence (HQ or real office, not just "sells into Arizona"), (c) plausible fit for entry-level SWE/AI/ML/Robotics roles, and (d) not being a staffing/recruiting firm, per the task's verification checklist.

## Files produced

- `data/companies.csv` / `data/companies.json` — 72 verified/candidate companies with full research fields.
- `data/contacts.csv` — 6 named contacts across 5 companies.
- `data/excluded-companies.csv` — 17 excluded entities (12 staffing/recruiting firms, 1 company-wide ITAR/clearance company, 1 defunct company, 3 companies with no confirmed current AZ engineering presence).
- `data/verification-log.csv` — 57 logged verification checks showing the research process at the company level.
- `reports/outreach-ready-companies.md` — clean, priority-grouped list of the 72 outreach-eligible companies for quick reference.
