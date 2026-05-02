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
**Live URL: https://acovrp.github.io/sleepycat-dashboard/**
**Local file: `C:\Users\User\Downloads\pwa-push\index.html`**
**GitHub repo: acovrp/sleepycat-dashboard** (GitHub Pages enabled, serves from `master` branch)
**Note:** `acovrp/Pwa` is a separate repo that hosts the brain files only (not the dashboard)

### Architecture
- Single HTML file, embedded JS + CSS
- Data via CSV uploads from Seller Central, Flipkart, Brand Analytics
- Design system: Kanishk's S&OP light theme
- 11 upload slots; only `br` (Business Report), `st` (Search Terms), `ba` (Brand Analytics) have active data processors
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
- **Protector dropdown**: `value="mattress"` is correct. `PRODUCTS[mattressprot].line = "mattress"` — the dropdown value must match `p.line`, not `p.id`. Do not change to `"mattressprot"` — that breaks the filter (zero rows returned). Category dropdown `f-cat` also has `value="mattress"` for the Mattress category but feeds a different state variable (`S.cat` vs `S.line`) — not a collision.
- **Comforter + Bedsheet missing**: `comforte` and `bedshee` product lines existed in PRODUCTS but had no dropdown options — both added.
- **Size + Thickness filter broken**: `getProds()` only filtered when `p.skus` existed, but no products have `skus` data, so size/thickness filtering was silently skipped for every row. Fixed by adding `PROD_SIZES` and `PROD_THICKNESSES` static lookup tables (keyed by `p.line`) as a fallback branch in `getProds()`. Pillow lines have no entry in `PROD_SIZES` so they are correctly hidden when a bed size is selected.

### Dashboard editing rules
- Line 588 is a 42KB minified JSON blob — Read tool fails on ranges including it; use Grep
- Always syntax-check JS after edits: extract script tag, run `node --check`
- Funnel data must decrease monotonically at every stage
- Rate metrics (ACOS, CTR, CVR, TACoS) never summed across products
- Read column headers from actual file before writing any parser — never assume
- **Dropdown `value` must match `PRODUCTS[].line`, not `p.id` or the display name.** Before changing any dropdown value, grep `"line":"<value>"` in the PRODUCTS blob to confirm the match. The protector has `p.id="mattressprot"` but `p.line="mattress"` — this has caused two wrong edits already.
- **Deploy flow**: edit `C:\Users\User\Downloads\pwa-push\index.html` → commit → push to `origin master` on `acovrp/sleepycat-dashboard`. The local remote was previously misconfigured to `Pwa`; it is now correctly set to `sleepycat-dashboard`. GitHub Pages serves from `master` (not `main`).

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

These are the decision categories where Aman moves fast, operates on instinct, and occasionally gets it wrong. The agent must slow these down, not speed them up.

### 1. Variation Structure (CRITICAL — irreversible in the short term)
- World Sleep Day incident: 7 ASINs demerged in one operation. BSR reset, reviews split, organic rank collapsed.
- Aman knows this risk but underestimates it when under pressure to fix a different issue.
- **Agent rule:** Any variation edit gets a full hold + risk statement before action. No exceptions.

### 2. Pricing Below Margin Floor
- Aman will sometimes react to a competitor price drop with "just match it" — without checking if margin survives.
- Below-floor pricing on Amazon accelerates rank but destroys P&L. Kanishk will ask about it.
- **Agent rule:** Always calculate and state margin at the proposed price before executing. Flag if below floor.

### 3. Ad Budget Decisions Without Keyword-Level Data
- "Increase ad budget by ₹50k" without specifying campaign/keyword = guaranteed ACOS spike.
- Aman knows this but says it when he's in a meeting and wants a quick answer.
- **Agent rule:** Never move budget without specifying source, destination, and expected ACOS impact.

### 4. Flipkart Organic Share (Currently fragile — ~7.7%, down from 40%)
- Root cause under investigation. Any catalog or pricing change on Flipkart could make it worse.
- Aman may not always connect a proposed Flipkart change to its organic impact.
- **Agent rule:** All Flipkart changes get an organic share impact check before execution.

### 5. Quick Commerce Assortment Changes
- Margin on QC is thin. Adding the wrong SKU hurts CM2 structurally.
- Blinkit/Zepto sometimes push for SKUs that don't make margin sense.
- **Agent rule:** Always run margin math on QC SKU additions. Don't list without Aman seeing the number.

### 6. Reactive Decisions After a Bad Week
- If sales drop, Aman's instinct is to cut price + increase ad spend simultaneously — which can compound the problem by destroying P&L without fixing the root cause.
- **Agent rule:** If Aman proposes two or more simultaneous aggressive changes in the same session, flag the compounding risk and ask which lever to pull first.

---

## Aman's Decision Patterns (for calibration)

- Reacts quickly to competitor moves — sometimes too quickly before checking if the competitor is just a weekend sale
- Trusts his gut on ad allocation more than the data sometimes
- Can underestimate how fragile variation structures are (World Sleep Day was a hard lesson)
- Values speed over process when he's under deadline pressure — that's when the agent needs to slow him down most
- Is genuinely data-first when he has the time — the agent should always give him the data so the decision improves, not worsen under time pressure

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
| Marketplace OS | Consolidated dashboard | v7.2, hosted at acovrp.github.io/sleepycat-dashboard/ |

### Agent Infrastructure
- Agent runs at: `C:\Users\User\Downloads\sleepycat-agent\sleepycat-agent\`
- Start command: `python run_agent.py`
- Dashboard: `http://localhost:8080`
- Watch folder: `C:\Users\User\Documents\SleepyCat-Data`
- GitHub CLI at: `C:\Program Files\GitHub CLI\gh.exe` (not in PATH for bash — use full path)
- GitHub auth: logged in as `acovrp`

---

## V Group (Background Only)

Aman is simultaneously building V Group — a five-arm real estate ecosystem (Vcertify, Vbrands, Vcap, Vdes, Vworkforce). The SleepyCat agent exists partly to free Aman's bandwidth for V Group. Do not mix V Group work into SleepyCat operations. If Aman raises V Group topics, note it's outside this agent's scope.
