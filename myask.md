# Aman's Ask — Read Before You Build Anything

This file exists because Claude spent a full session building the wrong thing, broke the dashboard, and had to write this as penance. Read it first. Every time.

---

## Who Aman Is

Senior Category Manager at SleepyCat. Owns Amazon India, Flipkart, Quick Commerce P&L — ~₹15 Cr/month GMV. Reports to COO. Operates with P&L accountability, not project accountability — every number he looks at has a rupee consequence.

He is technically capable. He runs git, understands JS, deploys to Cloudflare, directs parallel AI sessions (Claude Code + Claude.ai + Python agent + Kimi) simultaneously. He talks to you like a tech lead, not like a user. When he says "check if this makes sense," he means it literally — he wants the flaw found, not the task executed.

He thinks in first principles. He derived TACoS = inorganic share × ACOS on his own. He traces a bad ROAS number to branded budget cannibalization, to a specific keyword, to an ASIN that was OOS in Bangalore for two days. He doesn't need you to explain the business to him. He needs you to execute accurately.

He moves fast and has low tolerance for things that don't work after being told they work. "It's not working" from him is not a question — it's a fact. Don't argue. Investigate.

---

## His Ask From the Dashboard

### The one-line version
Open the dashboard, select a product, see everything about that product on one screen. If a number is off, click once, know why.

### The mental model
```
Overall target vs achievement (revenue + spend)
  → Category (Mattress / Pillow / Bedding / Mobility)
    → Product (Original / Ultima / Hybrid / Cloud...)
      → Size + Thickness
        → Organic vs Paid split
          → Ad format (SP / SD / SB)
            → Intent (Branded / Generic / Competition / Auto)
              → Keyword → ASIN → Region (future)
```

At every level: Revenue, Units, Spend, TACoS, ROAS, Organic%, Impressions, CTR, CVR.
One row per level. Click → expands inline to the next level. Never a new tab.

### The metric that matters most
TACoS = total ad spend / total revenue = inorganic share × ACOS.

If ROAS goes up but TACoS also goes up → branded campaigns are capturing sales that were already organic. That is the bad signal, not the good one. The dashboard should flag this, not hide it.

### The analytical flow he runs every week
1. Is revenue on track vs target? Is spend on track?
2. Did traffic (sessions/impressions) move?
3. If ads dropped — which format dropped? SP, SD, or SB?
4. Within that format — branded or generic intent?
5. Is ROAS going up while TACoS goes up too? (Cannibalization signal)
6. If conversion dropped — which keyword? Which ASIN? Was there a stock issue?

Each step is one click. The dashboard surfaces the anomaly. He confirms the hypothesis. Done in 2 minutes.

### What the dashboard is not
- Not a report viewer
- Not a tool for his team
- Not a place to upload 249MB CSV files
- Not something that needs tabs to navigate

---

## How He Uses It

**Morning:** Quick target vs actual check. Is anything on fire?

**Weekly ad review:** Where did spend go? Was it productive spend or brand cannibalization?

**Before approving agent recommendations:** The Python agent recommends something (increase branded spend, pause a keyword). He opens the dashboard, checks the data, confirms or rejects. The dashboard is his verification layer, not his analysis tool. He already knows what to look for.

**With his ad executive:** Shows them exactly where spend leaked. Expects the dashboard to make it obvious without explanation.

---

## Issues He Keeps Facing With Claude

These are not complaints — they are patterns. Future sessions should break them.

**1. Building without asking**
Claude starts coding before confirming what the feature is supposed to enable. The cost of asking "what decision does this help you make?" is 30 seconds. The cost of building the wrong thing is a session.

**2. Declaring victory when things don't work**
"It's live on Cloudflare" when the panel shows 0 rows. "Git is clean" when the changes aren't actually there. "Verified" when the verification test was wrong (UTF-16 encoding issue). Aman checks. He finds it broken. He loses trust.

**3. Rejecting parallel session work without understanding it**
Kimi built `integrate_unified_ads.py`. Claude rejected it for having bugs. Some of the bugs were real. But the rejection burned more tokens than fixing the bugs would have, and the alternative Claude built was also broken. Check before rejecting.

**4. Creating separate files instead of integrating**
Asked for ads analysis in the main dashboard. Got `az-ads-dashboard.html` — a separate file that serves no purpose. The ask was always integration.

**5. Memory and brain files becoming dump files**
After each session, memory fills with bug logs, code snippets, version history — things that live in git already. A future session reads 4 memory files and learns nothing actionable. Memory should contain what can't be derived from code or git log.

**6. Over-engineering the UX**
Tabs. Panels. Separate sections. Upload slots. Keyword Intelligence as a separate tab. Aman asked for one thing: select a product, see everything inline. Every added tab is a failure of design.

**7. Getting lazy at the end of long sessions**
The injection script at the end of a long session had a column name bug (`"advertised product id"` vs `"advertised product id (asin)"`). The kind of mistake that happens when you're running on fumes and don't verify. Long sessions need more verification, not less.

---

## Expectation vs Reality

| Expectation | Reality (what kept happening) |
|---|---|
| Works first time | Multiple sessions to fix one feature |
| Integrated into main dashboard | Separate file created |
| Data flows automatically | 249MB manual upload, 0 rows parsed |
| Click once to see why | Scroll through 5 tabs |
| Dashboard confirms agent recommendation | Dashboard is broken, can't confirm anything |
| 2-minute check | 2 hours of debugging |

---

## What Good Looks Like

Aman opens the dashboard. He selects "Original Mattress." He sees: Revenue ₹X, TACoS Y%, ROAS Z, Organic% W — all for the current week, versus last week. TACoS is red. He clicks the TACoS number. Sub-rows appear: SP, SD, SB. SD's ACOS is 68%. He clicks SD. Sub-rows: Branded, Generic. Branded spend is 80% of SD. He closes the laptop. He calls his ad exec. Done.

That is the goal. Not a dashboard. An answer machine.

---

## Guardrails for Any Future Build

1. No browser-side parsing of files larger than 1MB. Agent parses, JSON serves.
2. No new tabs. Inline expand only (`+` pattern already built).
3. No separate HTML files. Everything is `index.html`.
4. No feature without naming the decision it enables.
5. No injection without printing the exact anchor string from the file and confirming it matches.
6. No "it's deployed" without fetching the live URL and checking the actual content.
7. Delete `az-ads-dashboard.html`. It has never been useful.
