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

**FK Gross / OIV methodology (confirmed May 2026):**
- FK Gross = OIV (Order Item Value) = `listing_price + CLF` — what the customer actually pays FK
- `listing_price` = `sellingPrice` from FK order API — what SC sets as the listed price
- `CLF` (Customer Logistics Fee) = per-SKU fee FK charges the customer for logistics. NOT in seller settlement for NON_FBF sellers from Q2 FY25-26 onwards. Stored in FK listing metadata → `attributeData.customer_logistics_fee`. Fetched via `get-listings-info-by-id` API using session replay.
- `customer_price` = `customerPrice` from order API — actual buying price after FK-funded bank/card offers (FK absorbs this discount, not SC)
- All 297 active SKUs have CLF mapped. File: `agent_data/fk_clf_by_sku_actual.csv`
- FK vs Amazon YTD history now tracked in `fk_history.csv` (March 1 onwards, updated daily)

**FK vs Amazon channel comparison (Apr-May 2026):**
- FK runs at 22–63% of Amazon's weekly gross (unit economics similar, volume is the gap)
- FK ASP ≈ AMZ ASP for mattresses within ±0.6% (validated at SKU×week level) — proves OIV methodology is correct
- Pillow/bedding show 15–44% divergence — Amazon running permanent coupons on those SKUs, not a calc error
- FK is 3–4pp less discounted than Amazon at channel level, but this is product mix (mattresses dominate FK)

### Quick Commerce (Growth channel)
- Blinkit, Zepto, Swiggy Instamart
- Underperformance acknowledged — attributed to channel growth pace and bandwidth constraints
- Needs more attention; bandwidth constraint is what the agent is solving

---

## Marketplace OS Dashboard

Aman's single-file HTML command center, built personally and maintained by the agent.

**Current version: v7.4** (ads metrics fix + snapshot system, May 8 2026)
**Live URL (team, auth-gated): https://scos.aman-verma-741.workers.dev/** — Cloudflare Workers + Cloudflare Access, Google login, `@sleepycat.in` whitelisted. **Auto-deploys from `acovrp/Pwa` main branch via GitHub Actions** (`.github/workflows/deploy-workers.yml`). Requires repo secrets: `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID`.
**Live URL (public, no auth): https://acovrp.github.io/Pwa/** — GitHub Pages, still live
**Local file: `C:\Users\User\Downloads\pwa-push\index.html`**
**GitHub repo: acovrp/Pwa** (single repo for everything — dashboard, brain files, agent context, data)
**GitHub Pages serves from `main` branch; Cloudflare Pages also deploys from same repo**

### Architecture
- Single HTML file, embedded JS + CSS
- Data via CSV uploads from Seller Central, Flipkart, Brand Analytics
- Design system: Kanishk's S&OP light theme
- 11 upload slots, all active: `br` (AMZ units/revenue/sessions via ASIN_MAP), `st` (keywords), `ba` (search funnel), `sp` (AMZ adspend/ACOS/TACoS via ASIN_MAP), `sb`/`sd` (total spend → `UPLOADED_TOTALS.sb/sd`), `fk` (FK units/revenue via FK_NAME_MAP title matching → `PRODUCTS.flk.units/revenue`), `fkads` (FK ad spend → `UPLOADED_TOTALS.fkads` + per-product `PRODUCTS.flk.adspend.recent` + `PRODUCTS.flk.tacos.recent`; re-renders FK KPI + tables), `inv` (stock levels → `window.INVENTORY`), `ret` (returns → `window.RETURNS`), `pp` (raw rows → `window.PURCHASE_DATA`).
- FK tab KPI row: FK Revenue, Mar, Apr, May MTD, **FK Ad Spend** (live after fkads upload OR wow_data.json load), **FK TACoS** (same). TACoS card goes red if >15%.
- FK product table metric tabs: Gross Units, GMV, **Ad Spend**, **TACoS**. Ad Spend + TACoS now auto-populate from `wow_data.json` via `populateFkAdsFromWOW()` on page load — no manual upload needed for monthly view. FK ads groups mapped: Hybrid/Original/Ultima/UltimaLatex=1:1; Pillows/Bedding/Other Mattress/Toppers split proportionally by monthly revenue.
- Channels: Amazon, Flipkart, Quick Commerce, Other, Search Funnel tab

### ID Scheme (critical — causes bugs if confused)
- `PRODUCTS[].id` = 12-char (e.g. `hybridlatexm`, `originalmatt`)
- `PRODUCTS[].line` = 8-char (e.g. `hybridla`, `original`)
- Dropdown `value` attributes match `line` (8-char), not `id`
- KW product filtering uses `p.id.indexOf(S.line)===0 || p.line===S.line` (the OR clause handles cases where id prefix doesn't match line, e.g. after Protector's line was renamed to `"protector"`)

### Known Data Sources
| Source | What it feeds |
|---|---|
| Amazon Business Report (auto via SP-API) | Units, revenue, sessions, organic CVR (units/sessions), organic CTR (page_views/sessions) by ASIN — `br_history.csv` auto-loaded on page open |
| FK Order History (auto via FK Seller API) | Daily SKU-level FK orders — units, listing_price, CLF, OIV, customer_price — `fk_history.csv`. Updated daily by `fk_history_agent.py` via `run_spapi.py`. Backfilled from March 1 2026. |
| Unified Ads report (manual upload or future auto-pull) | Ad spend, ACOS, TACoS, Org%, ad CTR (ad_clicks/impressions), ad CVR (ad_units/impressions) per product per month. Upload via Unified Ads slot. `initAdsStreamProcessor` writes to both `WEEKLY_CUBE` (weekly diagnostics) and `PRODUCTS.channels.amz` (monthly metric tabs). Overwrites CTR with ad CTR on upload. |
| SP Search Terms report (manual CSV or Ads API) | Keyword spend, clicks, ACOS → Keyword Intelligence tab |
| Brand Analytics — Search Catalog Performance (manual CSV) | Search funnel — impression/click/ATC/purchase share → Search Funnel tab (Category Demand, SC Funnel Share, etc.) |
| Brand Analytics — Search Terms Report (SP-API auto) | SC organic search presence — 147 search terms, position #1/2/3, click share, conv share, month-over-month → SC Organic Search Presence view |
| Flipkart Sales export | Units, GMV, returns |
| Snowflake (`V_ADS_ENRICHED` view) | Amazon Ads — all campaign types. SP spend 100% ASIN-matched (enriched via ADID→SP_ADS JOIN). SD spend +40% inflated vs Amazon CSV (upstream Airbyte pipeline bug — not yet fixed). Account 2 (~25-30% of campaigns) missing from Snowflake entirely. Brand Analytics data also in Snowflake: `ASP_GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT` (4.45M rows) — may remove need for manual BA downloads. Scripts: `C:\Users\User\Downloads\az-ads-dashboard-snowflake\`. |

### SP Report Column Format (current export as of Apr 2026)
Amazon SC SP report columns (after normalization): `date` (format: "Apr 23, 2026"), `week`, `month`, `year`, `ad product`, `campaign name`, `advertised product id` (= ASIN), `total cost` (= spend), `sales` (= 14-day attributed revenue). processSpReport handles this format. If columns change in a future export, update `ci()` lookup strings in processSpReport.

### Changes in v7.3 (May 2026)
- All 7 previously unhooked upload processors now called from `handleUpload`: `fk`, `fkads`, `sb`, `sd`, `pp`, `inv`, `ret`
- `processFkAdsReport` now writes per-product adspend + TACoS to `PRODUCTS.flk` and re-renders
- FK KPI row: replaced hardcoded Cancel Rate/FBF Share with live FK Ad Spend + FK TACoS cards
- FK product table: added Ad Spend and TACoS metric tabs
- Removed all hardcoded placeholders: FLAGS, QCOM_AVAIL, QCom/Other KPI cards, header subtitle, status badge — all dynamic or TBD
- `updateHeaderStats()`: live date range + AMZ/FK revenue computed from PRODUCTS data
- Keyword Intelligence: date badge `#kw-date-range` shows report date range when ST data loads
- Search Funnel: `#sf-status` and `#sf-section-desc` show actual date range from SF.dates (fixed hardcoded "Jan 2024 - Feb 2026")
- New view "SC Organic Search Presence" in Search Funnel tab: shows 147 terms where SC appears in top 3 clicks, March vs April MoM, position badge, click share%, conv share%, 4 sort modes
- `BA_SQP` global + auto-fetch of `data/ba_sqp.json` on page load
- `data/ba_sqp.json` and `data/st_report.csv` committed to repo — auto-loaded on page open

### v7.4 Changes (May 8 2026)
- **Ads metrics wired**: `initAdsStreamProcessor` now builds `monthAgg` per ASIN per month (4 week-slots), writes to `PRODUCTS.channels.amz` on `finish()`: `adspend`, `acos`, `tacos`, `organic_pct`, `ctr` (ad CTR overwrite), `adcvr`. Also updates `AD_SPEND` global and calls `renderAmzKpi() + renderTables()`.
- **Two CVR metrics**: `cvr` = organic (units/sessions, from BR) and `adcvr` = ad CVR (ad_units/impressions, from Unified Ads). Both have tabs in Amazon Product Performance.
- **CTR = ad CTR**: `ch.ctr` for Amazon is now ad_clicks/impressions from Unified Ads. Business Report's page_views/sessions value is overwritten on Unified Ads upload.
- **Snapshot system**: `exportSnapshot()` button in dashboard header serializes `PRODUCTS.channels` + `WEEKLY_CUBE` + `AD_SPEND` → `snapshot.json`. `SNAPSHOT_INLINE` var baked into `index.html` for synchronous load on `file://`. `applySnapshot()` runs on page load — no server needed for local file. `fetch('./data/snapshot.json')` also runs for hosted version (applies if newer than inline). Workflow: upload files → Export Snapshot → save to `data/snapshot.json` → update inline in `index.html` via PowerShell regex replace → commit both.
- **Update inline snapshot**: `$snap = Get-Content 'data/snapshot.json' -Raw; $html = Get-Content 'index.html' -Raw; $html = [regex]::Replace($html, '(?s)var SNAPSHOT_INLINE = \{.*?\};', "var SNAPSHOT_INLINE = $snap;"); [IO.File]::WriteAllText('index.html', $html)`

### FK Products in PRODUCTS array (as of May 27 2026)
16 products have `channels.flk` data. Key lines: `hybridla`, `original`, `ultimama`, `ultimala` (Ultima Latex Mattress — added May 27, FK-only, data from Mar 2026), `trifoldm`, `latexort`, `cloudspr`, `mfpillow`, `cloudpil`, `softtouc`, `sleepyca`, `cuddlepi`, `cervical`, `memoryfo`, `protector`, `comforte`, `bedshee`.
FK ads group → PRODUCTS mapping (used in `populateFkAdsFromWOW`):
- "Hybrid Latex Mattress" → `hybridla`
- "Original Mattress" → `original`
- "Ultima Mattress" → `ultimama` + `ultimala` (split by revenue)
- "Pillows" → `mfpillow`, `cloudpil`, `softtouc`, `sleepyca`, `cuddlepi`, `cervical`
- "Bedding" → `comforte`, `bedshee`
- "Other Mattress" → `trifoldm`, `latexort`, `cloudspr`
- "Toppers & Accessories" → `memoryfo`, `protector`
- "Switch Dual Mattress" → no PRODUCTS entry, skipped

### WoW Inline + Gran Toggle (May 2026 — this session)
- **Month `+` expand**: each month column has expand button → expands inline to weekly sub-cols; current partial month expands to individual day columns (`RECENT_DAY_LABELS`)
- **Amazon metric tabs cleanup**: removed Ses.WoW and Ads.WoW as separate tabs — WoW trend accessible via + expansion on any month. Amazon tabs now: Units, Revenue, Org%, Ad Spend, ACOS, TACoS, CTR, CVR
- **FK WoW**: still accessible via "WoW ▸" metric tab button in Flipkart section
- **Gran toggle semantics fixed**: Monthly+Sum=total, Monthly+Avg=daily avg, Weekly=per-week avg (toggle irrelevant), Daily=daily avg (toggle irrelevant). Avg toggle only changes values in Monthly mode.
- **Partial month denominator fix**: `processBusinessReport` now dynamically reads actual CSV dates and sets `MONTHS[partial].daysSoFar` + `weeksSoFar` — no more hardcoded wrong denominators
- **WoW data source**: `C:\Excel\extract_wow.py` extracts FK+AZ weekly data from Excel → `C:\Excel\wow_data.json` → copied to `pwa-push\data\wow_data.json`. AZ sessions/ads data available in json but not yet merged into AZ product table rows (pending design decision).

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
- **Protector dropdown**: `value="protector"` is correct. `PRODUCTS[mattressprot].line = "protector"` (renamed from the old confusing `"mattress"` value). `PROD_SIZES` key is also `protector`. Do not change to `"mattressprot"` — that breaks the filter.
- **Comforter + Bedsheet missing**: `comforte` and `bedshee` product lines added to dropdown.
- **Size + Thickness filter broken**: Fixed by adding `PROD_SIZES` and `PROD_THICKNESSES` static lookup tables (keyed by `p.line`) as a fallback in `getProds()`.

### Dashboard editing rules
- Line 588 is a 42KB minified JSON blob — Read tool fails on ranges including it; use Grep
- Always syntax-check JS after edits: extract script tag, run `node --check`
- Funnel data must decrease monotonically at every stage
- Rate metrics (ACOS, CTR, CVR, TACoS) never summed across products
- Read column headers from actual file before writing any parser — never assume
- **Dropdown `value` must match `PRODUCTS[].line`, not `p.id` or the display name.**
- **FK-only products** (e.g. `ultimala`) must have `channels: { flk: {...} }` with NO `channels.amz` key. If `channels.amz` is missing/undefined and the snapshot has `sc.amz`, `applySnapshot` will throw `Object.assign(undefined, ...)` — crashing all subsequent script execution on page load (wow_data.json fetch, snapshot.json fetch, toggleTheme all stop). Guard is now in `applySnapshot` (`if (sc.amz && p.channels.amz)`), but do not add a dummy `amz: {}` to FK-only products.
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
- Snowflake SP ASIN coverage is now 100% via `V_ADS_ENRICHED` view (ADID JOIN to SP_ADS table). SD spend +40% inflated vs Amazon CSV (Airbyte upstream). Account 2 (~25-30% of campaigns) not in Snowflake.

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
| Snowflake | Amazon Ads data via `SLEEPYCAT_DB.MAPLEMONK.V_ADS_ENRICHED`. SP 100% ASIN-matched. SD +40% inflated (Airbyte bug). Account 2 missing. BA data: `ASP_GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT`. |
| Marketplace OS | Consolidated dashboard | v7.4, hosted at https://acovrp.github.io/Pwa/ |

### SP-API (Mark1) — Now Live (May 2026)
- App: Mark1, Developer Central, Private developer, self-authorized (1 of 10 slots used)
- Credentials in `config.yaml` on agent machine — never commit to git
- Region: **EU endpoint** — `sellingpartnerapi-eu.amazon.com` (India is EU, not FE)
- Reports API version: `2021-06-30`
- All reports are GZIP compressed — decode with `utf-8-sig` (handles BOM on first column)
- Daily runner: `run_spapi.py` + `spapi_module.py` in agent folder
- Output: `agent_data/spapi_data.json` — listings + traffic + callouts
- After each daily pull, `run_spapi.py` pushes three files to `pwa-push/data/` via git: `br_history.csv` (sessions/traffic), `st_report.csv` (search terms — Ads API when authorized, else watch folder), `ba_sqp.json` (SC organic search presence). Each committed + pushed separately → Cloudflare redeploys → team sees fresh data automatically
- Historical backfill: `spapi_history.py` — pulls day-by-day GET_SALES_AND_TRAFFIC_REPORT from Jan 1 2026, checkpointed (safe to kill and resume). 56,264 rows pulled as of May 1 2026.
- `data/br_history.csv` is committed in `acovrp/Pwa` repo — dashboard auto-loads it on open (relative path first, localhost fallback)
- **Session backfill (May 8 2026)**: `_append_to_br_history` now upserts — if date exists with sessions=0 (Amazon lag), removes old rows and rewrites with fresh data. If sessions>0, skips. `run_daily_checks` pulls days 1+2+3 ago on every run to backfill sessions Amazon releases 2-3 days late. This is fully automatic.
- Telegram callouts live. Task Scheduler registered.

**What SP-API pulls (daily at 7:30 AM via run_spapi.py):**
- `GET_MERCHANT_LISTINGS_ALL_DATA` — 1165 ASINs, TSV, fields: `asin1`, `status`, `seller-sku`, `item-name`, `quantity`
- `GET_SALES_AND_TRAFFIC_REPORT` — 536 ASINs with traffic, JSON, fields: `sessions`, `buyBoxPercentage`, `unitSessionPercentage` (CVR), `pageViews`, `unitsOrdered`, `orderedProductSales`. **Critical**: `dataEndTime` must be `T23:59:59Z` — if it equals `dataStartTime` (`T00:00:00Z`), Amazon silently returns an empty report. Bug was live May 2–3 2026; fixed May 4 2026.
- `GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT` — filters 713K rows for SC ASINs → 147 SC search terms with position, click share, conv share. Saves `agent_data/ba_sqp.json` → pushed to `pwa-push/data/ba_sqp.json`. Pulls last 2 complete months. **API limitation**: does NOT return total search volume, total clicks, or absolute click counts — only `clickShare%` and `conversionShare%`. Seller Central BA UI shows more columns that are not exposed in the API.
- Does NOT cover ad spend — stays Snowflake/ad report CSVs

**Advertising API (LIVE — May 8 2026):**
- `AdsAPIClient` class in `spapi_module.py` — uses `advertising-api-eu.amazon.com`
- LWA app: client_id `amzn1.application-oa2-client.da984bffb21a4bb0af46968ddad911b9` (under Aman's developer account)
- Approved scopes: `advertising::campaign_management` + audiences + others
- Auth endpoint: `https://eu.account.amazon.com/ap/oa` (India uses EU LWA — NOT www.amazon.com)
- Account structure: SLEEP MANAGEMENT PVT LTD (Manager Account, `amzn1.ads1.ma1.e6ofylyyj1ukqkduc7dj6jutp`) → SleepyCat New 2024 (active vendor, profile `1306806054242557`) + SLEEPYCAT (old seller, inactive)
- Target profile: `1306806054242557` (SleepyCat New 2024, vendor) — saved in config.yaml as `ads_profile_id`
- Credentials saved in config.yaml: `ads_client_id`, `ads_client_secret`, `ads_refresh_token`
- Daily pull: `pull_search_term_report()` in `spapi_module.py` → `agent_data/st_report.csv` → `pwa-push/data/st_report.csv` → Keyword Intelligence tab auto-populates

**Critical calibration note:**
- `GET_MERCHANT_LISTINGS_ALL_DATA` `status` column = merchant-fulfilled status only
- SleepyCat is FBA/Flex — this column is unreliable for live/dead ASIN detection
- True dead ASIN = 0 sessions + 0 units + 0 page views for 2+ consecutive days (from traffic report)
- Do NOT flag "inactive" from listings status — will false-positive on all FBA ASINs

**CVR callout thresholds (calibrated May 2026):**
- Minimum sessions: 200+ (below this, child ASIN traffic split makes CVR meaningless)
- CVR floor: < 0.5% (1% threshold flags too many size variants)

### Agent Infrastructure

**Primary: Oracle Cloud VM (24/7, always-on)**
- VM: `VM.Standard.E2.1.Micro` (1 OCPU, 1GB RAM, Always Free) at `161.118.175.141`
- SSH: `ssh -i ~/.ssh/oci_sleepycat ubuntu@161.118.175.141` (from OCI Cloud Shell)
- Systemd service: `sudo systemctl status/restart/logs sleepycat-agent`
- Logs: `sudo tail -f /var/log/sleepycat-agent.log`
- SP-API cron: daily 2:00 AM UTC (7:30 AM IST) → `/var/log/sleepycat-spapi.log`
- Working dir: `/home/ubuntu/sleepycat-agent/`
- pwa-push repo: `/home/ubuntu/pwa-push/` — all data stays in git, VM is stateless
- Watch folder: `/home/ubuntu/sleepycat-data/` (transient drop zone — not persisted)
- Config: `/home/ubuntu/sleepycat-agent/config.yaml` (never committed to git)
- To update code on VM: edit locally → push to git → `ssh ... 'cd ~/sleepycat-agent && git pull && sudo systemctl restart sleepycat-agent'`

**Secondary: Windows laptop (interactive/dev)**
- Agent entry point: `C:\Users\User\Downloads\sleepycat-agent\sleepycat-agent\run_agent.py`
- Start command: `cd C:\Users\User\Downloads\sleepycat-agent\sleepycat-agent && python run_agent.py`
- Dashboard repo (local): `C:\Users\User\Downloads\pwa-push\index.html`
- Brain path (config.yaml): `C:\Users\User\Downloads\pwa-push\brain\sleepycat_brain.md`
- Watch folder: `C:\Users\User\Documents\SleepyCat-Data`
- GitHub: `acovrp/Pwa`, branch `main` — dashboard, brain files, agent context all live here
- GitHub CLI: `C:\Program Files\GitHub CLI\gh.exe` (not in PATH — use full path)
- GitHub auth: logged in as `acovrp`

---

### Flipkart Seller API (LIVE — approved May 2026)
- Credentials in `config.yaml`: `flipkart_app_id`, `flipkart_app_secret`
- Token URL: `GET https://api.flipkart.net/oauth-service/oauth/token?grant_type=client_credentials&scope=Seller_Api` — Basic auth header with base64(`app_id:app_secret`). **No `/sellers/` in the URL — that's wrong.**
- Status: **Approved and live** (confirmed 2026-05-19).
- Shipments API: `POST https://api.flipkart.net/sellers/v3/shipments/filter` — paginated, pre/post-dispatch buckets. Implemented in `fk_module.py` (`get_token()` + `fetch_shipments()`).
- `fk_history.csv` built and live — daily ASIN-level FK order history from March 1 2026. Schema: `date, sku, asin, product, category, units, listing_price, clf, oiv, customer_price`. Mirrors `br_history.csv`. Updated daily by `run_spapi.py` via `fk_history_agent.py`.
- CLF extraction: FK Seller Hub session replay (Selenium CDP → cookies → requests) → `get-listings-info-by-id` API → `attributeData.customer_logistics_fee`. 297 SKUs mapped in `fk_clf_by_sku_actual.csv`.
- Session replay technique: capture browser session cookies via Chrome DevTools Protocol, replay with Python `requests.Session()` to call FK's internal REST APIs directly. ~8 req/sec, ~36s for full 297-listing extract. Works for any data visible in FK Seller Hub.

---

## AI Tools & Access Layer (May 2026)

This section defines what tools exist, what they do, and when to use each. Read this before deciding how to answer a question or take an action.

### Tool Map

| Tool | How to invoke | Best for | NOT for |
|---|---|---|---|
| `/aman` | `/aman` in Claude Code | Strategy, decisions, business context, brainstorming | Execution, data pulls, dashboard edits |
| `/scos` | `/scos` in Claude Code | Operations, tasks, dashboard, code, data queries | High-level strategy without data |
| **Amazon Ads MCP** | Auto-available in `/scos` Claude Code sessions | Live ad data: campaigns, keywords, ACOS, spend by ASIN — interactive, on-demand | Scheduled automation, bulk history pulls |
| **SleepyCat Agent** | Telegram or `python run_agent.py` | Scheduled daily pulls, mobile briefings, on-the-go L1 approvals | Complex analysis, dashboard edits, code changes |
| **SP-API scripts** | `python run_spapi.py` | Scheduled data pipeline — BR, FK, BA SQP, snapshot | Interactive queries |
| **Ads API scripts** | `pull_ads_weekly.py`, etc. | Bulk ad history pulls, dashboard CSV injection | Live conversational queries |

### When to Use Which

**Use `/aman` when:**
- Strategic decisions — channel priorities, budget philosophy, team structure
- Preparing for Kanishk reviews or JBP
- Evaluating a new opportunity or risk
- Anything where business judgment > data execution

**Use `/scos` when:**
- Fixing the dashboard, editing brain files, running scripts
- Querying sales/keyword data from existing CSVs
- Building or debugging anything in the agent stack
- **Asking live ad questions** (MCP kicks in automatically)

**Use Amazon Ads MCP (within /scos) when:**
- "Why did ACOS spike on [product] last week?"
- "Which campaigns are burning budget with zero conversions?"
- "List all SP campaigns for [product] with spend and ACOS"
- "Compare this week vs last week for Hybrid Latex"
- Any question that needs live ad data without a CSV upload

**Use the SleepyCat Agent (Telegram) when:**
- You're away from the laptop — mobile queries
- Daily briefing review
- Quick L1 approval (approve/reject a recommendation)
- Triggering a manual data pull

**Use SP-API/Ads scripts directly when:**
- Backfilling history (>30 days)
- Something broke in the daily automation
- Building a new data source for the dashboard

### Amazon Ads MCP — Technical Details (live May 2026)

- **Endpoint:** `https://advertising-ai-eu.amazon.com/mcp` (EU = India region)
- **Mode:** Fixed Account — profile `1306806054242557` (SleepyCat New 2024)
- **Credentials:** Own LWA app — `ads_client_id` + `ads_refresh_token` from `config.yaml`
- **Token:** Access token expires every 1 hour. Refresh before each Claude Code session:
  ```powershell
  cd C:\Users\User\Downloads\sleepycat-agent\sleepycat-agent
  python refresh_ads_mcp_token.py
  ```
- **Covers:** SP, SB, SD, DSP campaigns. Last 90 days SP, 60 days SB/SD.
- **Does NOT cover:** Account 2 campaigns (different profile — not yet configured). Snowflake SD spend inflation is a separate Airbyte bug, MCP data is clean.
- **Config location:** `C:\Users\User\.claude.json` (added via `claude mcp add`)

---

## V Group (Background Only)

Aman is simultaneously building V Group — a five-arm real estate ecosystem (Vcertify, Vbrands, Vcap, Vdes, Vworkforce). Do not mix V Group work into SleepyCat operations.
