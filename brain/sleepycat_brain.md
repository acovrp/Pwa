# Aman Verma — Operating Brain

This is Aman's knowledge base. It is context fed to the agent — not operating instructions. The agent reads this to understand the business, the person, and the domain. Instructions on how the agent should behave live in AGENT_CONTEXT.md.

---

## Who Aman Is

**Aman Verma** — Senior Category Manager at SleepyCat, an Indian D2C mattress and sleep products brand.

- Manages Amazon India, Flipkart, and Quick Commerce (Blinkit, Zepto, Swiggy Instamart)
- P&L ownership mindset — treats the role like running a business, not managing a function
- ~₹15 Cr/month GMV across channels, ~₹40 LPA compensation
- Based in Indirapuram, Ghaziabad
- Reports to COO Kanishk Arya. Key colleague: Manoj

**Key achievements:**
- Amazon rank: #8 → #4 in mattress category
- Toppers sub-category: BSR #1
- Flipkart CM2: substantial improvement
- Scaled SleepyCat to ₹150 Cr in 1.8 years
- Previously scaled Wendy's to ₹100 Cr in 2 years

---

## Team Structure

Aman leads 5 specialist roles. The agent does not manage them directly — it prepares tasks and drafts communications for Aman to send.

| Role | Scope |
|---|---|
| **KAM 1** | Amazon India — catalog, pricing, promotions, account health |
| **KAM 2** | Flipkart — same scope, platform-specific |
| **Ads POC** | Advertising across SP/SB/SD (Amazon) and PLA/PCA (Flipkart) — budgets, keywords, ACOS/TACoS |
| **Catalogue POC** | Listings, A+ content, variation management, flat files, image compliance |
| **Reviews/VOC POC** | Review monitoring, VOC analysis, response drafting, rating improvement |

---

## Key Stakeholders

- **Kanishk Arya** — COO of SleepyCat. Aman's primary reporting line. S&OP reviews, JBP/AOP presentations go to him. Budget increases above monthly threshold get escalated here.
- **Manoj** — Colleague/peer. Coordinates on cross-functional matters.

---

## Channels & Business Context

### Amazon India (Primary channel)
- Largest revenue source
- Rank improved from #8 to #4 in mattress category
- Toppers sub-category: BSR #1
- Key metrics: TACoS, ACOS, organic share, CPC, RPC, CVR
- SP-API app "Mark1" in Developer Central
- EasyEcomm = live data source for orders and inventory
- Variation structures are critical — demerge crises happen (World Sleep Day incident: 7 ASINs demerged)
- Critical insight: variation consolidation explains only part of organic share gap; genuine CVR underperformance on broad generic terms explains the rest
- ASIN → SKU → Product mapping achieving ~98% revenue coverage

### Flipkart (Secondary channel)
- CM2 improvement is key metric
- earn_more data being integrated into Marketplace OS
- Different catalog and ad mechanics from Amazon
- Organic share historically at ~40% but collapsed to ~7.7% — under investigation

### Quick Commerce (Growth channel)
- Blinkit, Zepto, Swiggy Instamart
- Underperformance acknowledged — attributed to channel growth pace and bandwidth constraints
- Needs more attention; bandwidth constraint is what the agent is solving

---

## Marketplace OS Dashboard

Aman's single-file HTML command center, built personally and maintained by the agent.

**Current version: v7.2** (full audit + 30 bug fixes, May 2026; filter fixes May 2026)
**Live URL: https://acovrp.github.io/Pwa/**
**Local file: `C:\Users\User\Downloads\pwa-push\index.html`**
**GitHub repo: acovrp/Pwa** (single repo for everything — dashboard, brain files, agent context)
**GitHub Pages serves from `main` branch**

### Architecture
- Single HTML file, embedded JS + CSS
- Data via CSV uploads from Seller Central, Flipkart, Brand Analytics
- Design system: Kanishk's S&OP light theme
- 11 upload slots total; only 3 have active data processors: `br` (Business Report), `st` (Search Terms), `ba` (Brand Analytics). The other 8 (SP campaigns, SB, SD, Flipkart sales, Flipkart ads, Inventory, Returns) accept files but don't yet update any dashboard numbers.
- Channels: Amazon, Flipkart, Quick Commerce, Other, Search Funnel tab

### ID Scheme (critical — causes bugs if confused)
- `PRODUCTS[].id` = 12-char (e.g. `hybridlatexm`, `originalmatt`)
- `PRODUCTS[].line` = 8-char (e.g. `hybridla`, `original`)
- Dropdown `value` attributes match `line` (8-char), not `id`
- KW product filtering must use `p.id.indexOf(S.line) === 0`, not `p.id === S.line`

### Known Data Sources
| Source | What it feeds |
|---|---|
| Amazon Business Report | Units, revenue, sessions, CVR by ASIN |
| SP Search Terms report | Keyword spend, clicks, ACOS |
| Brand Analytics (Search Catalog Performance) | Search funnel — impression/click/ATC/purchase share |
| Flipkart Sales export | Units, GMV, returns |
| Snowflake | Ad spend (SP ASIN coverage ~62% due to keyword-level vs product-ad-level row mixing) |

### Bugs fixed in v7.2 (reference — don't re-introduce)
- setFunnel() now scoped to `.funnel-type-nav .ftn-btn` (was corrupting SF tab active states)
- Funnel data is monotonically decreasing (search > imp > click > atc > purchase)
- `vs Target` uses Mar MTD total (was projecting from last week incorrectly)
- `renderAmzKpi` has null guard on `organic_pct.mar`
- Rate metric totals show `—` (unweighted mean was misleading)
- `.xlsx` drag-drop rejected with alert (was silently corrupting binary as CSV)
- `dsb` status badge updates on upload
- KW search debounced 200ms

### Filter bugs fixed post-v7.2 (May 2026)
- **Protector dropdown**: `value="mattress"` is correct. `PRODUCTS[mattressprot].line = "mattress"` — the dropdown value must match `p.line`, not `p.id`. Do not change to `"mattressprot"` — that breaks the filter (zero rows returned).
- **Comforter + Bedsheet missing**: `comforte` and `bedshee` product lines added to dropdown.
- **Size + Thickness filter broken**: Fixed by adding `PROD_SIZES` and `PROD_THICKNESSES` static lookup tables (keyed by `p.line`) as a fallback in `getProds()`.

### Dashboard editing rules
- Line 588 is a 42KB minified JSON blob — Read tool fails on ranges including it; use Grep
- Always syntax-check JS after edits: extract script tag, run `node --check`
- Funnel data must decrease monotonically at every stage
- Rate metrics (ACOS, CTR, CVR, TACoS) never summed across products
- Read column headers from actual file before writing any parser — never assume
- **Dropdown `value` must match `PRODUCTS[].line`, not `p.id` or the display name.**
- **Deploy flow**: edit `C:\Users\User\Downloads\pwa-push\index.html` → commit → push to `origin main` on `acovrp/Pwa`. GitHub Pages serves from `main`.

---

## Marketplace OS as a Product (Aman's Strategic Context)

Aman is building the Marketplace OS into a product — an AI-led marketplace management layer that SleepyCat is the first customer of. If it solves SleepyCat's real operational pain, it becomes sellable to other D2C brands on Amazon/Flipkart.

- SleepyCat is client #1. Aman is both the builder and the user.
- Target buyers: D2C brands doing ₹2–30 Cr/month on marketplaces
- Sales channel: Aman's existing Amazon/Flipkart POC network
- This is separate from SleepyCat operations. Do not mix the two.
- The agent's job is to make SleepyCat operations run well — that is what proves the product works.

---

## Data & Analytical Patterns

- Word-boundary regex matching over SUMIF wildcards (learned from Search Funnel module)
- Case sensitivity check on all data joins (learned from Latex Ortho Mattress bug)
- Validate file formats and column headers before writing parsers
- Conservative numbers always — Aman catches inflated projections immediately
- Snowflake SP ASIN coverage gap is a known, accepted limitation (~62%)

---

## Reporting Cadence

| Frequency | What |
|---|---|
| Weekly | Team task allocation, ad performance review, catalog health, sales vs target, competitor monitoring |
| Monthly | P&L review + commentary, S&OP update to Kanishk, category deep-dive |
| Quarterly | JBP/AOP review prep, KRA/KPI assessment for all 5 roles, strategic planning |

---

## How Aman Thinks

- Data-first, skeptical of surface-level explanations
- Builds his own tools rather than relying on off-the-shelf reporting
- Deep fluency in Amazon catalog mechanics — flat files, variation structures, ad attribution
- Checks for case sensitivity in data joins
- Validates file formats before writing parsers
- Conservative numbers — low tolerance for over-confidence
- Catches inflated projections immediately

## How Aman Communicates

- Direct, no fluff
- Hindi-English code-switching is normal
- Hates public information presented as insight
- Values substantive challenge over agreement
- Prefers conservative, defensible numbers

## What Aman Approves vs Rejects

**Approves:**
- Data-backed ad budget shifts with specific ASIN/keyword rationale
- Catalog fixes with clear evidence (suppressed ASIN, broken variation)
- Competitor response pricing within defined margin floors
- Team task reallocation based on workload data

**Rejects:**
- Recommendations based on vanity metrics without P&L impact
- Generic "increase budget" without specific rationale
- Changes that risk variation structure stability
- Anything that could trigger catalog suppression

**Escalates to Kanishk:**
- Budget increases above monthly threshold
- New channel launches or exits
- Pricing strategy shifts affecting brand positioning
- Cross-functional resource requests

---

## Risk Map — Where Aman Can Make Costly Mistakes

### 1. Variation Structure (CRITICAL — irreversible in the short term)
- World Sleep Day incident: 7 ASINs demerged. BSR reset, reviews split, organic rank collapsed.
- **Agent rule:** Any variation edit gets a full hold + risk statement before action. No exceptions.

### 2. Pricing Below Margin Floor
- **Agent rule:** Always calculate and state margin at the proposed price before executing.

### 3. Ad Budget Decisions Without Keyword-Level Data
- **Agent rule:** Never move budget without specifying source, destination, and expected ACOS impact.

### 4. Flipkart Organic Share (Currently fragile — ~7.7%, down from 40%)
- **Agent rule:** All Flipkart changes get an organic share impact check before execution.

### 5. Quick Commerce Assortment Changes
- **Agent rule:** Always run margin math on QC SKU additions.

### 6. Reactive Decisions After a Bad Week
- **Agent rule:** If Aman proposes two or more simultaneous aggressive changes, flag the compounding risk and ask which lever to pull first.

---

## Aman's Decision Patterns (for calibration)

- Reacts quickly to competitor moves — sometimes too quickly
- Trusts gut on ad allocation more than data sometimes
- Underestimates variation structure fragility (World Sleep Day was a hard lesson)
- Values speed over process under deadline pressure — that's when the agent needs to slow him down most
- Genuinely data-first when he has time

---

## Technical Setup

| Tool | Purpose | Notes |
|---|---|---|
| Amazon Seller Central | Sales, inventory, catalog, ads | CSV exports + SP-API (Mark1 app) |
| Flipkart Seller Hub | Sales, catalog, ads | CSV exports |
| EasyEcomm | Orders, inventory aggregation | Live data source |
| Google Sheets | Search funnel data layer | 26 months BA data |
| Brand Analytics | Search catalog performance | Monthly/weekly exports |
| Snowflake | Ad spend data | ~62% coverage (known gap) |
| Marketplace OS | Consolidated dashboard | v7.2, hosted at https://acovrp.github.io/Pwa/ |

### Agent Infrastructure
- Agent runs at: `C:\Users\User\Downloads\sleepycat-agent\sleepycat-agent\`
- Start command: `python run_agent.py`
- Dashboard: `http://localhost:8080`
- Watch folder: `C:\Users\User\Documents\SleepyCat-Data`
- GitHub CLI at: `C:\Program Files\GitHub CLI\gh.exe` (not in PATH for bash — use full path)
- GitHub auth: logged in as `acovrp`
- Single repo: `acovrp/Pwa` — dashboard, brain files, agent context all live here

---

## V Group (Background Only)

Aman is simultaneously building V Group — a five-arm real estate ecosystem (Vcertify, Vbrands, Vcap, Vdes, Vworkforce). Do not mix V Group work into SleepyCat operations.
