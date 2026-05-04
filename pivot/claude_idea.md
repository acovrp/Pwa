# Marketplace OS v8 — The Idea

A self-contained explainer of what we're proposing to build, what it solves, how it's structured underneath, and whether it holds up at scale. The full spec lives at `brain/marketplace_os_v8.md`. This file is the "read in 5 minutes" version.

---

## 1. The pivot in one paragraph

v7.3 is a dashboard. Each tab is a silo. Each upload is a different shape. Numbers diverge across tabs. Nothing is clickable into its components. v8 is an OS. Everything sits on three clean fact tables. Every metric on every screen is clickable into the metrics it's made of, in the same tab. The 5-clicks-1-tab rule is the product, not a feature.

---

## 2. The principle (the only thing that matters)

> **For every disappointing fall or rise, you should be able to find the root cause in 5 clicks within 1 tab.**

This is the spec. Everything else — three fact tables, JSONL files, Arquero, decomposition trees — is implementation. If the principle doesn't hold for a real movement on a real day, v8 has failed regardless of how clean the code is.

---

## 3. What v7.3 fails at today (and v8 fixes)

| v7.3 pain | Why it happens | v8 fix |
|---|---|---|
| Header revenue ≠ AMZ tab revenue ≠ FK tab sum | Each tab computes from a different in-memory shape | One fact table, every view queries it |
| FK Ad Spend / TACoS only show after fkads upload | Per-upload re-render logic; if you forget to upload, card lies | KPI is a query, not a re-rendered cache. No upload = no row = blank, never wrong |
| `organic_pct` only fills when both BR + SP uploaded | Two-source coupling baked into processor | Computed at query time; partial data is partial result, never wrong |
| Click any metric → nothing happens | No decomposition layer | Every metric is a node in a tree; clicks open its children |
| "Why did revenue drop?" requires Excel + 4 tabs | No cross-source joins anywhere in the dashboard | One join: `products.asin → BA.top_clicked_asin` bridges supply to demand |
| New metric / new view = new processor + new shape + new bugs | View tightly coupled to ingestion | Add a row → all views see it. Add a column → write one query helper |
| 11 upload slots, 6 in-memory shapes, schema drift on every Amazon export change | No central schema | One schema file (`schema.js`) validates every upload at the door |

These aren't polish issues. They're structural. v7.3 cannot deliver the 5-click principle without becoming v8.

---

## 4. The architecture, plain English

Three tables, one dimension, one log.

### `daily_facts` — the main one
Every row is **one SKU on one channel on one day**. Columns: units, revenue, sessions, page_views, ad_spend, ad_revenue, ad_clicks, inventory, returns. Everything else is derived (CVR, ACOS, TACoS, organic_share = math on these columns at query time).

### `weekly_search_facts` — demand side
Every row is **one search term on one channel for one week**. Columns: position, click_share, conv_share, top_clicked_asin, impression_share. Source: BA SQP + BA SCP. Already comes attributed to the top-clicked ASIN — that's the bridge to our SKUs.

### `daily_keyword_facts` — supply side
Every row is **one keyword in one campaign on one day**. Columns: ad_spend, ad_revenue, clicks, impressions, attributed_asin. Source: SP Search Terms (Amazon), FK keyword export.

### `products` — the dimension
SKU → ASIN, FSN, name, line, category, size, MRP, margin floor. Hand-maintained JSON. The only place the SKU↔ASIN↔FSN mapping lives.

### `changes` — the action log
Every pricing change, ad budget shift, listing edit, variation event. Manual entry in v8 (a modal). Agent-driven entries deferred. This table is where click 5 in the 5-click path lands.

### How they fit together
```
            ┌──────────────────┐
            │     products     │  (sku, asin, fsn, line, category, size...)
            └────────┬─────────┘
                     │ joins everywhere
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
  daily_facts   weekly_search   daily_keyword
  (sku×ch×day)  (term×ch×week)  (kw×campaign×day)
       │             │             │
       └──────── changes ──────────┘
                  (date filter)
```

Every screen in v8 = a query against these. No view holds its own data shape. No upload writes anywhere except into these tables.

---

## 5. The 5-click path on a real example

**"FK revenue dropped 18% week-over-week."** What does the user actually do?

| Click | What they see | What's running |
|---|---|---|
| 1 | KPI card `FK Revenue WoW −18%` | Lands them on FK view, WoW filter on |
| 2 | Top-loser SKU table → click worst row (say `originalmatt`) | Slide-in panel for that SKU |
| 3 | Panel shows `units × ASP` waterfall + `organic vs paid` split. Click `organic units −34%` | Panel expands into search-impact section |
| 4 | Table of search terms where SKU's category ranks, sorted by impression-share Δ. Click worst term. | Term-level drill: position Δ, who took the position |
| 5 | Click the date the shift began. Panel surfaces matching `changes` log entries (price change? ad pause? competitor move?) | Root cause atom |

Same tab. Same panel. URL hash captures the path so it's shareable and browser-back works. **No tab switch. No CSV download. No Excel pivot.** That's the product.

---

## 6. Will it work at scale?

Honest answer: **yes for SleepyCat-scale, with one table to watch.**

### Volume math (current SleepyCat scale)

| Table | Rows/year | Size/year (JSONL) | After 3 years |
|---|---|---|---|
| `daily_facts` | ~365K | 30 MB | 90 MB |
| `weekly_search_facts` | ~8K | 1 MB | 3 MB |
| `daily_keyword_facts` | ~1.8M | 180 MB | **540 MB ⚠** |

`daily_keyword_facts` is the one that breaks first. SP Search Terms exports daily, accumulates across thousands of keywords. After 2-3 years it'll cross the threshold where eager-loading hurts page-open time.

### Query performance (Arquero in browser)

| Operation | Rows | Time |
|---|---|---|
| GroupBy + agg on `daily_facts` (1 year) | 365K | <100 ms |
| WoW delta on `daily_facts` (1 year) | 365K | <150 ms |
| Cross-table join (`daily_facts` × `products` × `weekly_search_facts`) | 365K × 1K × 8K | ~300 ms |
| GroupBy on `daily_keyword_facts` (1 year) | 1.8M | 500 ms – 1 s |

Daily KPI rendering touches `daily_facts` only — fast. The keyword table is heavy and only loaded when the user opens search/keyword views. Lazy load is the answer.

### Multi-user

v8 is read-many, write-one. Team reads via Cloudflare Access (already configured). Only one writer (Aman or the agent) commits to repo. No race conditions because there's no concurrent write path. If team writers are added later, JSONL append needs a queue — out of scope v8.

### Growth path — what to do when JSONL hurts

Trigger conditions:
- Total fact-table size > 500 MB on disk
- First-paint > 5 seconds on broadband
- Any single Arquero query > 2 seconds

Migration when triggered:
1. Convert JSONL → Parquet partitioned by month (`data/daily_facts/2026-04.parquet`)
2. Replace Arquero with DuckDB-WASM — same SQL-like API, columnar storage, lazy-loads only months in current view
3. ~1-2 sessions of work, schema unchanged

So the architecture is forward-compatible with a 10-100× scale-up without redesigning.

### What breaks first (in priority order)

1. **`daily_keyword_facts` size** at year 2-3 → trigger Parquet migration for that table only
2. **Manual upload friction** — the "download patch + cat + git push" flow gets old → build the GitHub-PAT-in-localStorage auto-push button (~1 session)
3. **JSONL append duplication** if same week re-uploaded → weekly compaction script in `run_spapi.py` (already in Phase 1)
4. **Eager-load all 3 tables on page open** → lazy-load keyword + search facts on tab open (Phase 5)

None of these break the architecture — they're all "swap a piece" fixes.

### What this DOESN'T solve

- **High write concurrency** — multiple team members uploading at once. Solvable with a queue/lock, but not v8 scope.
- **Real-time / sub-hourly updates** — JSONL + git push is D-1 / W-1 by design. Real-time requires a backend, which kills the "edit → push → live" simplicity.
- **>10K SKUs or >5 channels** — math still works but lazy-loading + partitioning becomes mandatory from day one.

---

## 7. Scope discipline

**In v8:** Amazon + Flipkart, 3 fact tables, products dim, changes log (manual entry), decomposition tree UX, 5-click drill paths, parallel `/v8/` deploy with v7.3 left untouched.

**Out of v8 (explicitly deferred):** Quick Commerce, autonomous agent attribution, auto-populated changes log, mobile responsive, multi-tenant SaaS shape, Snowflake direct connection, real-time updates, reviews/ratings ingestion.

The deferred list is not "we'll do this later" hand-waving — every item is something that would expand v8 from 8-10 sessions to 25+ and dilute the principle. They're real features, just not v8.

---

## 8. Status

- **Spec written** (`brain/marketplace_os_v8.md`, ~370 lines, 12 sections)
- **Code paused** pending Aman approval
- **5 open questions** in spec §10 — answers needed before code starts:
  1. What was `data/ads_unified.csv` (gitignored — prior attempt?)
  2. Manual upload: download-patch-cat-push, or auto-push from day 1?
  3. Cutover at end of Phase 3 (KPI parity, no decomposition) or wait for Phase 4?
  4. `changes` log: manual modal only, or also a "log this view" button?
  5. SKU naming: keep opaque 12-char `id`, or readable scheme like `originalmatt-78x36x6`?

---

## 9. Why this and not something else

| Alternative | Why rejected |
|---|---|
| Patch v7.3 incrementally | Structural problems (silo'd tabs, no fact table, no decomposition layer) can't be patched. Each fix adds another shape. |
| Replace with off-the-shelf (Helium10, Junglescout, Sellics) | None do cross-tab decomposition. None give us the action log + change attribution. None will know SleepyCat's variation structure. |
| Move dashboard to a real backend (Postgres + API) | Kills "edit HTML → push → live" simplicity. Adds infra, auth, deploy pipeline. v8 stays static-hostable. |
| Single fact table (force everything into one shape) | BA is week-grain term-level, SP search terms is day-grain keyword-level — they don't fit `sku × channel × day`. Forcing it loses information that's essential for the click 3→4 join. |
| Keep JSON shapes per source, add a "join layer" on top | This is what v7.3 already is in spirit. The bugs come from the per-source shapes. Removing them is the only fix. |
| React / Vue / Svelte rewrite | Build step kills the deploy model. Vanilla JS + 80KB Arquero handles the surface area. |

The v8 architecture is the smallest thing that satisfies the 5-click principle without breaking the deploy simplicity v7.3 has today.

---

## 10. The honest summary

**What this gets you:** every number on screen comes from one place, every metric is drillable, every drop has a 5-click path to a logged action or external event. The dashboard becomes a tool you use to investigate, not a static report.

**What it costs:** 8-10 focused build sessions with v7.3 running in parallel. Some upload friction during transition (download patch, append, push). One real risk: BA → products attribution coverage. If <85% of BA top-clicked-ASINs map to a known SKU, click 3→4 silently misses cases. Mitigated by a coverage check in Phase 5.

**What it does not become:** a multi-tenant SaaS. A real-time system. An agent-driven autopilot. Those are real things, just not v8.

**The decision:** do we lock the spec and start Phase 1, or keep iterating on the architecture? My read: spec is tight enough to start, the 5 open questions can be answered in a 10-minute conversation, and code on Phase 1 is mostly mechanical (schema + ingestion rewrites). The variance lives in Phases 4-5 (decomposition UX + cross-table joins) where we'll learn things that may revise this doc.
