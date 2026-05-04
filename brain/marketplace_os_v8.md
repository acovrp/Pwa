# Marketplace OS v8 — Architecture Spec

**Status:** DRAFT — pending Aman approval before code.
**Scope:** Amazon India + Flipkart only. Quick Commerce + autonomous agent attribution explicitly out of scope.
**Author:** Claude Code session, May 4 2026.
**Supersedes:** v7.3 architecture once Phase 3 ships and validation passes.

---

## 1. Why v8

v7.3 has 11 upload processors writing into 6 different in-memory shapes (`PRODUCTS[].flk`, `UPLOADED_TOTALS`, `BR`, `INVENTORY`, `RETURNS`, `BA_SQP`). Every tab reads from its own shape. Bugs cluster around the joins (FK KPI hardcoded vs computed, fkads not re-rendering, organic_pct only filling when both BR + SP are uploaded, header revenue diverging from AMZ-tab revenue).

The user-facing requirement that breaks v7.3:

> **I should be able to find root cause in 5 clicks within 1 tab for every disappointing fall or rise.**

v7.3 cannot deliver this. Every tab is a silo; no metric on any screen is clickable into its components; cross-tab joins (a SKU's organic drop → which search term lost impression share) don't exist. v8 is a rewrite around two ideas:

1. **Three fact tables** at clean, source-aligned grain — every view is a query against them.
2. **A decomposition tree** that defines, for every metric on screen, what it breaks into — and renders that breakdown in the same tab on click.

---

## 2. Goals & Non-Goals

### Goals
- Single source of truth for every number on screen
- Every KPI and every cell clickable into its decomposition, in the same tab
- 5-click max from any KPI to a root-cause atom (specific SKU + lever + date + change-log entry)
- Numbers consistent across all views (header revenue == AMZ tab revenue == WoW table sum)
- Daily incremental updates with no rebuild step
- Manual uploads + SP-API auto-pull both write into the same fact tables
- v7.3 stays live in parallel until v8 validation passes

### Non-Goals (v8)
- Quick Commerce channel
- Autonomous agent attribution / anomaly proposals (manual exploration only in v8)
- Auto-populated changes log (manual entry only)
- Mobile responsive
- Selling MOS to other brands (architecturally compatible, not a v8 feature)
- Real-time streaming (D-1 / W-1 cadence is fine)

---

## 3. Data Model

### 3.1 `daily_facts` — sku × channel × day

Primary fact table. Every row is one SKU on one channel on one day.

| Column | Type | Nullable | Notes |
|---|---|---|---|
| sku | string | no | canonical SKU id, e.g. `originalmatt-78x36x6` |
| asin | string | yes | null for FK rows |
| fsn | string | yes | null for AMZ rows |
| channel | enum(`amz`,`fk`) | no | |
| date | ISO date | no | YYYY-MM-DD |
| units | int | yes | units sold |
| revenue | float | yes | gross revenue ₹ (incl GST as today) |
| returns_units | int | yes | returns dated to original sale day if known, else event day |
| sessions | int | yes | AMZ only — FK doesn't expose |
| page_views | int | yes | AMZ only |
| buy_box_pct | float | yes | AMZ only |
| ad_spend | float | yes | |
| ad_revenue | float | yes | 14-day attributed for AMZ |
| ad_clicks | int | yes | |
| ad_impressions | int | yes | |
| inventory_units | int | yes | end-of-day stock snapshot |

**Derived at query time** (never stored, always computed):
- `cvr = units / sessions`
- `acos = ad_spend / ad_revenue`
- `tacos = ad_spend / revenue`
- `roas = ad_revenue / ad_spend`
- `organic_revenue = revenue − ad_revenue`
- `organic_units ≈ units − (ad_revenue / asp)`  *(rough — ad_units not directly reported)*
- `organic_share_pct = organic_revenue / revenue`
- `asp = revenue / units`
- `ctr = page_views / sessions`  *(engagement proxy, AMZ only — not ad CTR)*

**Source mapping:**

| Source | Writes columns | Cadence | Pipeline |
|---|---|---|---|
| SP-API GET_SALES_AND_TRAFFIC | sessions, page_views, units, revenue, buy_box_pct (AMZ rows) | D-1 daily | run_spapi.py |
| SP report (manual upload OR Ads API future) | ad_spend, ad_revenue, ad_clicks, ad_impressions (AMZ rows) | varies | browser ingest |
| FK sales export | units, revenue (FK rows) | manual | browser ingest |
| FK ads export | ad_spend, ad_revenue, ad_clicks, ad_impressions (FK rows) | manual | browser ingest |
| FK earn_more | overlay split fields onto FK rows | manual | browser ingest |
| Inventory upload | inventory_units (both channels) | manual | browser ingest |
| Returns upload | returns_units (both channels) | manual | browser ingest |

**Storage:** `data/daily_facts.jsonl` — append-only. One row per `(sku, channel, date)`. Updates are upserts (replace row by composite key).

**Volume estimate:** 500 SKUs × 2 channels × 365 days = 365K rows/year. ~80 bytes/row JSONL = ~30MB/year. Trivial for browser to load.

### 3.2 `weekly_search_facts` — search_term × channel × week

Captures consumer demand-side data. BA reports are at week level only.

| Column | Type | Nullable | Notes |
|---|---|---|---|
| search_term | string | no | normalized lowercase |
| channel | enum(`amz`,`fk`) | no | FK rows initially empty (no equivalent source) |
| week_start | ISO date | no | Monday of the week |
| search_volume_rank | int | yes | from BA SQP |
| position | int | yes | our position when our SKU appears |
| click_share_pct | float | yes | |
| conv_share_pct | float | yes | |
| top_clicked_asin | string | yes | from BA SQP — already attributed |
| top_clicked_sku | string | yes | derived: products.asin → sku |
| impression_share_pct | float | yes | from BA SCP |
| atc_share_pct | float | yes | from BA SCP |
| purchase_share_pct | float | yes | from BA SCP |

**Source mapping:**

| Source | Writes columns | Cadence | Pipeline |
|---|---|---|---|
| BA SQP report | search_volume_rank, position, click_share, conv_share, top_clicked_asin | W-1 weekly | run_spapi.py |
| BA SCP report | impression_share, atc_share, purchase_share | W-1 weekly | manual or SP-API |

**Storage:** `data/weekly_search_facts.jsonl`.

**The critical join:** `weekly_search_facts.top_clicked_asin` → `products.asin` → `products.sku` → `products.category`. This bridges search demand to our SKUs. Without it, click 3→4 in the decomposition tree fails.

### 3.3 `daily_keyword_facts` — keyword × campaign × day

Captures supply-side ad performance.

| Column | Type | Nullable | Notes |
|---|---|---|---|
| keyword | string | no | normalized lowercase |
| campaign | string | no | |
| ad_group | string | yes | |
| match_type | enum(`exact`,`phrase`,`broad`,`auto`) | yes | |
| channel | enum(`amz`,`fk`) | no | |
| date | ISO date | no | |
| ad_spend | float | yes | |
| ad_revenue | float | yes | |
| clicks | int | yes | |
| impressions | int | yes | |
| attributed_asin | string | yes | `Advertised product ID` from SP report |
| attributed_sku | string | yes | derived via products dim |

**Source mapping:**

| Source | Writes columns | Cadence | Pipeline |
|---|---|---|---|
| SP Search Terms report | all (AMZ rows) | D-1 (W-1 in practice) | manual upload, Ads API future |
| FK keyword export | all (FK rows) | manual | manual upload |

**Storage:** `data/daily_keyword_facts.jsonl`. This will be the largest table — ~50K rows/month at SleepyCat's keyword breadth. Still manageable (~50MB/year JSONL).

### 3.4 `products` — SKU dimension

| Column | Type | Notes |
|---|---|---|
| sku | string PK | canonical id |
| asin | string | nullable for FK-only SKUs |
| fsn | string | nullable for AMZ-only SKUs |
| product_name | string | display name |
| line | string | 8-char (matches v7.3 PRODUCTS[].line — preserved for compat) |
| category | string | mattress, pillow, bedsheet, comforter, protector, etc. |
| size | string | e.g. `78x36x6` |
| thickness_inches | int | nullable |
| mrp | float | nullable |
| margin_floor | float | nullable — pricing guardrail |
| active | bool | |

**Storage:** `data/products.json` — single JSON array, hand-maintained initially. Can be regenerated from Seller Central listings later.

### 3.5 `changes` — action log

| Column | Type | Notes |
|---|---|---|
| id | uuid | |
| date | ISO date | when the change happened |
| logged_at | ISO datetime | when entered into log |
| channel | enum(`amz`,`fk`,`both`) | |
| sku | string | nullable for system-wide changes |
| type | enum | `pricing`, `ad_budget`, `listing_edit`, `variation`, `ad_pause`, `bsr_shift`, `competitor_move`, `inventory_event`, `other` |
| description | string | free text |
| source | enum(`manual`,`agent`,`automated`) | `agent` reserved for future |
| magnitude | float | nullable — % change for pricing/budget |

**Storage:** `data/changes.jsonl`. Manual entry via UI in v8. Agent-driven entries deferred.

---

## 4. Tech Stack & Decisions

| Layer | Choice | Rationale |
|---|---|---|
| Storage format | JSONL files in `data/` | Inspectable, debuggable, no build step, fits existing `run_spapi.py` daily push pattern. Migrate to Parquet+DuckDB-WASM if dataset crosses 5M rows (~3 years away at current scale). |
| Query engine | Arquero (~80KB) | SQL-like dataframe ops in JS. Mature, fast, handles groupBy/joins/window functions cleanly. Vendored to `lib/`, not CDN. |
| App structure | Multi-file, no bundler | Each file < 500 lines. Browser loads via `<script>` tags. GitHub Pages serves directly. Edit any file → push → live. Preserves v7.3 deploy simplicity in spirit. |
| Sparklines | uPlot (~50KB) | Fastest sparkline lib, tiny footprint. Vendored. |
| Other charts | Plain SVG (waterfall, bars) + Chart.js if needed | SVG for the decomposition waterfall — no lib needed. Chart.js only if a complex chart demands it. |
| Routing / state | URL hash (`#sku=...&decomp=...&term=...`) | Shareable drill-paths, browser back works, no router lib. |
| Persistence of manual uploads | Browser-side parse + downloadable JSONL patch + manual git commit | Zero new infra. Browser parses upload, renders immediately, generates a `*.jsonl.patch` for user to append + push. GitHub-API direct-push deferred to post-v8 polish. |
| Auto-pull data (SP-API) | Existing `run_spapi.py` extended to write `daily_facts.jsonl` + `weekly_search_facts.jsonl` + push | Pattern already exists for `br_history.csv`. Same git-push-on-success flow. |
| Cutover | Parallel deploy at `/v8/` | v7.3 untouched at `/`. Promote when v8 numbers match v7.3 across AMZ + FK for 1 week. |

**Rejected alternatives** (logged so we don't relitigate):
- **SQLite-in-repo + sql.js**: real SQL is appealing, but +5MB lib and harder to inspect raw data. Reconsider at scale.
- **DuckDB-WASM + Parquet**: best analytical DB for browser, but Parquet writes need a Python build step in-line. Premature for current data volumes.
- **Single HTML file (v7.3 pattern)**: no longer fits — 7+ feature files needed; one file would cross 1MB and become a Read-tool problem (line 588 lesson).
- **React / Vue / Svelte**: brings build step, build step breaks "edit → push → live". Vanilla JS + small libs is enough for this surface area.

---

## 5. File Layout

```
/v8/
├── index.html                 — shell: script tags, top-nav, container divs
├── app.js                     — boot, global state (S), nav, hash router
├── schema.js                  — schema constants, validators, enums
├── store.js                   — fact table loaders (fetch JSONL → Arquero tables), upsert helpers
├── ingest.js                  — upload processors for all sources, JSONL patch generator
├── queries.js                 — reusable Arquero query helpers (groupBy, deltas, joins)
├── decompose.js               — decomposition tree definitions + path resolver
├── components/
│   ├── kpi_card.js            — clickable KPI card with sparkline
│   ├── delta_table.js         — WoW/MoM/DoD table with click-into-row
│   ├── waterfall.js           — SVG waterfall for metric decomposition
│   ├── sparkline.js           — uPlot wrapper
│   ├── breakdown_panel.js     — slide-in panel for click drill-down
│   └── changes_strip.js       — recent changes list, filtered by current scope
└── views/
    ├── home.js                — landing: top movers across AMZ + FK
    ├── amz.js                 — Amazon channel deep view
    ├── fk.js                  — Flipkart channel deep view
    ├── search.js              — search funnel + keyword intelligence (joined)
    └── decomp.js              — explicit decomposition tree explorer

/data/
├── daily_facts.jsonl          — main fact table
├── weekly_search_facts.jsonl
├── daily_keyword_facts.jsonl
├── products.json              — SKU dim
├── changes.jsonl              — change log
├── br_history.csv             — kept (legacy + migration verification source)
├── ba_sqp.json                — kept (source for weekly_search_facts ingestion)
└── wow_data.json              — kept during transition; deprecated post-cutover

/lib/
├── arquero.min.js             — vendored
└── uplot.min.js               — vendored
```

---

## 6. The Decomposition Tree

This is the schema of "what breaks into what." Every node is a metric. Every edge is a decomposition rule. The UI uses this tree to render breakdown panels on click.

```
revenue
├── by_channel        → split into AMZ rev + FK rev rows, each clickable
├── by_sku            → top 20 SKUs by absolute Δ, signed, clickable
├── by_date           → calendar heatmap, click date → that day's snapshot
└── per_sku_decomp    (when scoped to one SKU)
    ├── units × asp
    │   ├── units
    │   │   ├── sessions × cvr   (AMZ only — FK has units, no sessions)
    │   │   │   ├── sessions
    │   │   │   │   ├── organic_sessions ≈ page_views − ad_clicks
    │   │   │   │   └── paid_sessions ≈ ad_clicks
    │   │   │   └── cvr
    │   │   │       ├── price_event       → changes(sku=X, type=pricing)
    │   │   │       ├── inventory_event   → changes(sku=X, type=inventory_event) OR daily_facts.inventory_units==0
    │   │   │       └── (reviews/rating drift — out of scope v8)
    │   │   └── (FK) units
    │   │       ├── price_event
    │   │       └── inventory_event
    │   └── asp = revenue / units
    │       └── price_event       → changes(sku=X, type=pricing)
    ├── organic vs paid
    │   ├── organic_revenue
    │   │   └── search_drift     → join weekly_search_facts via products.asin = top_clicked_asin
    │   │       └── (per term)
    │   │           ├── position Δ
    │   │           ├── click_share Δ
    │   │           └── new_top_clicked_asin (competitor took position)
    │   └── ad_revenue
    │       ├── ad_spend × roas
    │       │   └── per keyword  → daily_keyword_facts(attributed_sku=X)
    │       │       ├── impressions Δ
    │       │       ├── clicks Δ
    │       │       ├── cvr Δ
    │       │       └── budget_event   → changes(type=ad_budget)
    │       └── acos
    └── changes_for_period       → changes(sku=X, date in window)
```

**Implementation:** `decompose.js` exports a graph. Each node has:
- `id` (string, e.g. `revenue.units.sessions`)
- `label`
- `compute(scope) → { value, prev_value, delta_pct }`
- `children(scope) → array of child nodes`
- `render(scope, container)` (component to render the breakdown panel section)

The breakdown panel renders the current node + its children, each child clickable. URL hash tracks the path: `#scope=amz&sku=originalmatt&period=wow&path=revenue.units.sessions`.

---

## 7. The 5-Click Path — Worked Examples

### Example A: "FK Revenue dropped 18% WoW"

| Click | Action | Component | Query |
|---|---|---|---|
| 1 | Land on Home → click `FK Revenue WoW −18%` KPI card | `kpi_card` → opens `views/fk.js` with WoW filter | `daily_facts |> filter(channel='fk') |> rollup(rev=sum(revenue)) by week` |
| 2 | FK view shows SKU delta table → click top loser row | `delta_table` → `breakdown_panel` opens for that SKU | `daily_facts |> filter(sku=X, channel='fk') |> WoW deltas` |
| 3 | Panel: units × asp waterfall, organic vs ad split → click `organic_units −34%` | `waterfall` + click handler | (already in panel state) |
| 4 | Panel expands: search-term impression share table for SKU's category, sorted by share Δ | `delta_table` (search facts) | `weekly_search_facts |> join(products on top_clicked_sku=sku) |> filter(category=X) |> WoW deltas` |
| 5 | Click date the shift began OR click search-term row | `changes_strip` opens at that date OR drill into the term's history | `changes |> filter(sku=X OR sku=null, date in window)` |

5 clicks. Same tab. URL: `#scope=fk&period=wow&sku=originalmatt&path=revenue.organic.search_drift&term=foldable+mattress&date=2026-04-28`. Browser back undoes each level.

### Example B: "AMZ ACOS spiked to 28% this week"

| Click | Action |
|---|---|
| 1 | KPI `ACOS WoW +9pp` → AMZ view ACOS focus |
| 2 | Campaign-level delta table → click worst campaign |
| 3 | Panel: keyword-level breakdown (ad_spend, clicks, conv) for that campaign |
| 4 | Click worst keyword by ACOS Δ → impressions × ctr × cvr decomposition |
| 5 | Click date the spike began → `changes` log entry (e.g. budget shift, bid change) OR if no change logged, see organic search position Δ for that keyword |

Same tab. Same panel pattern.

---

## 8. Ingestion Pipeline

### 8.1 Auto sources (run_spapi.py extended)

Existing `run_spapi.py` already pulls daily and pushes `data/br_history.csv`. Extend to also write:
- `data/daily_facts.jsonl` — append AMZ rows from sales+traffic report (one row per ASIN per day), upsert by `(sku, channel='amz', date)`
- `data/weekly_search_facts.jsonl` — append rows from BA SQP, upsert by `(search_term, channel='amz', week_start)`

Same git-commit + push pattern. No new infra.

### 8.2 Manual uploads (browser)

Each upload slot in v8:
1. User drops file into upload zone
2. `ingest.js` parses (CSV/XLSX/JSON) → validates against schema
3. New rows shown in a preview table — user confirms
4. On confirm: rows are upserted into in-memory Arquero table → views re-render immediately
5. **Patch generation:** browser also generates `data/<table>.jsonl.patch` containing only the new/changed rows, downloaded automatically
6. User commits the patch:
   ```
   cat ~/Downloads/daily_facts.jsonl.patch >> data/daily_facts.jsonl
   git add data/daily_facts.jsonl && git commit -m "data: <source> for <date>" && git push
   ```
7. (Future polish) "Push to repo" button uses GitHub PAT stored in localStorage to commit + push directly. Deferred — extra surface area, security model needs design.

**Why not auto-push:** would require a backend (Cloudflare Worker + GitHub App) — out of scope for v8. The manual `cat >> && git push` flow is one-time-per-day friction Aman already does.

### 8.3 Upsert semantics

JSONL is append-only on disk, but `(sku, channel, date)` is the logical primary key for `daily_facts`. Strategy:
- New uploads append rows
- A periodic compaction script (run weekly via run_spapi.py) reads the JSONL, deduplicates by composite key (last-write-wins), rewrites the file, commits the compacted version
- Browser load logic also dedupes in-memory on load — so even if the file isn't compacted, the latest row wins

---

## 9. Migration Plan

All work happens at `/v8/` until validation. v7.3 stays at `/` untouched.

### Phase 1 — Data layer + AMZ + FK ingestion (1–2 sessions)
- Create `/v8/` folder structure, vendor arquero+uplot
- Write `schema.js` (column defs, validators, enums)
- Write `store.js` (load JSONL → Arquero tables, upsert, dedupe)
- Write `ingest.js` for: BR auto (read existing `br_history.csv`, transform to AMZ daily_facts rows), SP manual upload, FK sales upload, FK ads upload
- Generate initial `data/daily_facts.jsonl` from existing `br_history.csv` (one-time backfill)
- Write `data/products.json` from current dashboard's PRODUCTS[] array
- Smoke test: console queries return expected sums for known months
- **Gate:** `daily_facts |> filter(channel='amz') |> rollup(rev=sum(revenue)) by month` matches v7.3 AMZ revenue exactly for last 3 months

### Phase 2 — AMZ view + KPI strip + delta table (1 session)
- `views/amz.js`: KPI strip (revenue, units, ad_spend, ACOS, TACoS, organic_share_pct, sessions, CVR), all clickable
- `components/kpi_card.js`, `components/sparkline.js`, `components/delta_table.js`
- `queries.js`: helpers for WoW/MoM/DoD deltas
- **Gate:** Every AMZ KPI in v8 matches v7.3 AMZ KPI exactly for last week + last month

### Phase 3 — FK view (1 session)
- `views/fk.js`: same shape as AMZ but no sessions/CVR (FK doesn't expose), adds FK-specific cards (FK Ad Spend, FK TACoS — already live in v7.3)
- Reuse all components from Phase 2
- **Gate:** Every FK KPI matches v7.3 for last week + last month
- **At this point: cutover is technically possible — promote v8 to `/` if Aman approves**

### Phase 4 — Decomposition tree + breakdown panel (2–3 sessions)
- `decompose.js`: register every node in the tree from §6
- `components/breakdown_panel.js`: slide-in panel, renders current node + children, click handlers wired
- `components/waterfall.js`: SVG waterfall for units = sessions × CVR, revenue = units × ASP, etc.
- Click handlers on every KPI card and every cell in delta table → opens panel at correct path
- URL hash state + browser back nav
- **Gate:** Worked Examples A and B above are reproducible end-to-end in 5 clicks

### Phase 5 — Search facts + cross-table join (1–2 sessions)
- `ingest.js` extended for BA SQP, BA SCP → `weekly_search_facts.jsonl`
- `ingest.js` extended for SP Search Terms → `daily_keyword_facts.jsonl`
- `views/search.js`: combined search funnel + keyword intelligence (replaces v7.3 Keyword Intelligence + Search Funnel tabs as one joined view)
- Wire into decomposition: organic_units click → search-term impression share table (the click 3→4 join)
- **Gate:** From any AMZ SKU's `organic_revenue` decomposition, can drill to a specific search term's WoW position drift in ≤ 2 clicks within the panel

### Phase 6 — Action log + manual change entry (2 sessions)
- `data/changes.jsonl` + UI to add a change (modal: date, sku, channel, type, description, magnitude)
- `components/changes_strip.js`: recent changes filtered to current scope (visible at bottom of every breakdown panel)
- Wire into decomposition tree as terminal nodes (click 5)
- **Gate:** From any KPI drop, the panel surfaces the relevant changes log entry as a candidate root cause

### Total estimate
**8–10 sessions**, with Phases 4 and 5 being the highest variance — could stretch to 12 if the BA SQP → products attribution proves messier than expected (e.g. ASIN in BA doesn't match `products.asin` cleanly, requires fuzzy join).

### Cutover criteria
- All v7.3 KPIs reproduce exactly in v8 for AMZ + FK (Phases 2-3)
- Decomposition tree works end-to-end (Phase 4)
- 1 week of parallel run with no number divergences
- Aman explicit go
- Then: rename `index.html` → `legacy.html`, `v8/index.html` → `index.html`, update internal asset paths, single commit

---

## 10. Risks & Open Questions

### Risks
1. **BA SQP → products attribution.** BA gives `top_clicked_asin`. We need `products.asin → products.sku → products.category` to bridge to demand-side analysis. If the ASIN-level mapping is incomplete (variation children, deprecated ASINs), the join silently drops rows. **Mitigation:** Phase 5 starts with a coverage report — % of BA terms whose `top_clicked_asin` resolves to a known SKU. Target ≥85% before wiring.
2. **`organic_units` is approximate.** We derive it as `units − (ad_revenue / asp)`. SP doesn't report ad_units directly. For high-ASP, low-volume SKUs this can underflow or get noisy. **Mitigation:** show as range + flag uncertainty in UI when ad_revenue/revenue > 50%.
3. **Manual upload friction.** The "download patch + cat + git push" flow is friction Aman has to do per upload. **Mitigation:** Phase 6.5 (deferred) builds a "Push to repo" button using GitHub PAT in localStorage.
4. **JSONL grows unbounded without compaction.** **Mitigation:** weekly compaction script in `run_spapi.py` (Phase 1 ships with this).
5. **v7.3 has 6+ months of bug fixes baked in.** v8 might re-introduce regressions covered by v7.3's edge cases (Protector dropdown, partial-month denominator, etc.). **Mitigation:** Phase 2-3 gates require exact KPI match; treat any divergence as a v8 bug, port the fix.

### Open questions for Aman
1. **`data/ads_unified.csv` is in `.gitignore`.** Was there a prior attempt at this? If so, what was learned? Anything in that file we should look at before naming our table?
2. **Manual upload persistence.** OK with the "download patch + cat >> + git push" flow for v8, deferring auto-push? Or do you want auto-push (GitHub PAT in localStorage) as part of v8?
3. **Cutover threshold.** Cutover at end of Phase 3 (v8 has KPI parity but no decomposition tree) or wait for Phase 4 (full v8 vision)? Phase 3 cutover means v7.3 dies sooner but users lose Keyword Intelligence + Search Funnel until Phase 5.
4. **`changes.jsonl` entry source for v8.** Manual UI entry only? Or also a "log this" button on every panel that captures the current view's deltas as context?
5. **SKU canonicalization.** v7.3 uses `PRODUCTS[].id` (12-char) and `PRODUCTS[].line` (8-char). v8 introduces `sku` as an explicit canonical id. Do we want SKU = current `id`, or SKU = a new scheme (e.g. `line-size`)? Current `id` is opaque; new scheme is readable but means a migration.

---

## 11. What This Spec Does NOT Cover

Explicitly deferred — do not build in v8:
- Quick Commerce ingestion or views
- Autonomous agent attribution / anomaly proposals (the "morning movers" pre-computed paths)
- Auto-populated changes log (agent watching ad/listing/price changes and writing entries)
- Mobile responsive
- Authentication / multi-user (Cloudflare Access stays as-is)
- Marketplace OS as a multi-tenant product
- Reviews/ratings ingestion (mentioned in decomposition tree as "out of scope v8")
- Snowflake direct connection
- Real-time / streaming updates

---

## 12. Approval Checklist

Before code starts, Aman confirms:
- [ ] Three-fact-table model is the right grain split
- [ ] Tech decisions in §4 (JSONL + Arquero + multi-file no-bundler)
- [ ] Phased migration plan in §9, including parallel `/v8/` deploy
- [ ] Answers to open questions in §10

Once approved: this doc becomes the source of truth for v8 implementation. Any deviation during build gets logged back here.
