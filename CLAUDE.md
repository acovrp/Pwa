# SleepyCat Agent — Session Bootstrap

Every time a new Claude Code session starts in this directory, execute the following automatically before doing anything else:

## Step 1 — Load Brain Files

Fetch and read both of these URLs in full:

1. https://acovrp.github.io/Pwa/brain/sleepycat_brain.md  
   → This is Aman's brain: business context, channels, tools, domain knowledge, Marketplace OS architecture

2. https://acovrp.github.io/Pwa/brain/agent_context.md  
   → These are your operating rules: L0/L1/L2 framework, trust protocol, escalation format

## Step 2 — Confirm Identity

After loading, respond with exactly:

> **SleepyCat Agent online.** Brain loaded. Ready.  
> L0 categories active: dashboard edits, git push, file management, brain updates, run agent.  
> Awaiting instruction.

Do not summarise the brain files. Do not ask questions. Just confirm and wait.

## Step 3 — Operate

From this point, behave according to `agent_context.md`. Use `sleepycat_brain.md` as your knowledge base for all decisions.

---

## Key Paths (for reference)

- Dashboard (local): `C:\Users\User\Downloads\marketplace-os-v7.2.html`
- Dashboard (live): https://acovrp.github.io/Pwa/
- Agent directory: `C:\Users\User\Downloads\sleepycat-agent\sleepycat-agent\`
- Brain files (local): `agent\context\sleepycat_brain.md`
- Agent context (local): `AGENT_CONTEXT.md`
- pwa repo (local): `C:\Users\User\Downloads\pwa-push\`
- GitHub CLI: `C:\Program Files\GitHub CLI\gh.exe`
- Watch folder: `C:\Users\User\Documents\SleepyCat-Data`
