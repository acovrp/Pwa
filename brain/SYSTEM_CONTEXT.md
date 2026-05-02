# V Group System Context — Master Navigation Document

This document tells every tool (Python agent, Claude Code, Claude.ai) exactly where everything lives, how it connects, and what each tool can and cannot do. Read this before operating. Never guess paths.

---

## The Three Tools

| Tool | What it is | When it runs | Can edit files? | Can push GitHub? |
|---|---|---|---|---|
| **Python Agent** (`run_agent.py`) | Autonomous ops brain | Always (auto-starts on login) | Via subprocess only | Via subprocess git commands |
| **Claude Code** | File editor + builder | Only when you open it | Yes — directly | Yes — directly |
| **Claude.ai** | Strategy + thinking partner | Only when you're here | No | No |

They share the same brain files. They do not share memory between sessions.

---

## Complete File Map

### Python Agent
```
C:\Users\User\Downloads\sleepycat-agent\sleepycat-agent\
├── run_agent.py              ← START HERE: python run_agent.py
├── voice.py                  ← Voice interface: python voice.py
├── bridge.py                 ← Task executor for file/git ops
├── config.yaml               ← API keys + paths
├── task_queue.json           ← Bridge task queue
├── agent.log                 ← All agent actions logged here
├── agent_data/               ← Trust levels, decision history
│   ├── memory/action_log.jsonl
│   └── trust/trust_state.json
└── agent/
    ├── core.py               ← Agent brain code (SleepyCatAgent class)
    ├── dashboard.py          ← Local web UI
    ├── telegram_bot.py       ← Telegram approvals
    ├── watcher.py            ← CSV file watcher
    └── context/              ← EMPTY — brain moved to pwa-push/brain/
```

### Dashboard Repo (pwa-push) — Single Source of Truth
```
C:\Users\User\Downloads\pwa-push\
├── index.html                ← Marketplace OS dashboard (THE product)
├── ai-token-dashboard.html   ← API usage tracker
├── .nojekyll                 ← GitHub Pages config
├── CLAUDE.md                 ← Claude Code reads on startup
├── brain/                    ← MASTER BRAIN — all tools read from here
│   ├── sleepycat_brain.md    ← Business knowledge, who Aman is, channels, metrics
│   └── agent_context.md      ← How the agent behaves, L0/L1/L2 rules
└── .claude/
    ├── settings.local.json
    └── commands/
        ├── aman.md           ← /aman command: loads Aman's brain context
        └── scos.md           ← /scos command: loads full agent context
```

### Watch Folder (data drops)
```
C:\Users\User\Documents\SleepyCat-Data\
└── [drop CSV exports here — agent auto-processes]
```

---

## GitHub

- **Repo:** `acovrp/Pwa` — https://github.com/acovrp/Pwa
- **Live dashboard:** https://acovrp.github.io/Pwa/
- **Live brain:** https://acovrp.github.io/Pwa/brain/sleepycat_brain.md
- **Branch:** `main` (GitHub Pages serves from main)
- **Auth:** logged in as `acovrp`
- **GitHub CLI:** `C:\Program Files\GitHub CLI\gh.exe` (not in PATH — use full path or subprocess)
- **Remotes:** `origin` and `pwa` both point to same repo (harmless duplicate)

### Git workflow (always from pwa-push folder)
```powershell
cd C:\Users\User\Downloads\pwa-push
git add -A
git commit -m "message"
git push
```

---

## Config (config.yaml)
```yaml
anthropic_api_key: [set]
telegram_bot_token: not configured
telegram_owner_id: 0
agent:
  model: claude-sonnet-4-20250514
  watch_folder: C:\Users\User\Documents\SleepyCat-Data
  data_dir: ./agent_data
brain_path: C:\Users\User\Downloads\pwa-push\brain\sleepycat_brain.md
```

---

## How Tools Connect

```
pwa-push/brain/sleepycat_brain.md  ← SINGLE SOURCE OF TRUTH
         ↓                    ↓
   Python Agent          Claude Code
   (reads on start)      (reads via /scos or /aman)
         ↓                    ↓
   Daily ops              Code edits
   decisions              file changes
   data analysis          git push
```

When brain is updated:
1. Edit `pwa-push/brain/sleepycat_brain.md` locally
2. `git add -A && git commit -m "..." && git push`
3. Both tools read updated brain next session

---

## Known Issues / Fixes Applied

### Agent startup
- Python 3.13 on Windows — always run from correct folder
- Start command: `cd C:\Users\User\Downloads\sleepycat-agent\sleepycat-agent && python run_agent.py`
- Auto-starts on Windows login via Task Scheduler ("SleepyCat Agent" task)
- Laptop sleep disabled when plugged in (`powercfg /change standby-timeout-ac 0`)

### update_brain command
- Trigger: type `update brain: [content]` at agent prompt
- Method: `agent.update_brain()` in core.py
- Flow: shows proposal → y/n approval → writes to brain file → git push
- **Known issue as of May 2026:** Method may not be saved in core.py — verify with `findstr /n "update_brain" agent\core.py`

### Dashboard (index.html)
- Version: v7.2
- ID scheme: `PRODUCTS[].line` = 8-char, dropdown values must match `.line` not `.id`
- Line 588 is 42KB minified JSON — don't edit that line
- Always syntax-check after JS edits: extract script, run `node --check`
- Deploy: edit locally → git push → GitHub Pages auto-updates in ~60 seconds

### Voice (voice.py)
- STT: Google Speech Recognition (requires internet)
- TTS: pyttsx3 (Windows native, offline)
- Push-to-talk: press ENTER to start, ENTER to stop
- Known gap: small Vosk model had poor Indian English accuracy — switched to Google STT

---

## What Each Tool CAN and CANNOT Do

### Python Agent (run_agent.py)
**CAN:**
- Think, analyze, recommend, decide (via Claude API)
- Watch folder and auto-process CSV drops
- Log all actions to agent_data/
- Track trust levels per decision category
- Call subprocess for git and file operations
- Update brain files (when update_brain method works)

**CANNOT:**
- Browse the internet
- Log into Seller Central or Flipkart directly
- Edit its own code files
- Run without PowerShell window open (unless Task Scheduler running)

### Claude Code
**CAN:**
- Read and edit any file on disk
- Run terminal commands
- Push to GitHub
- Fix bugs in index.html, core.py, run_agent.py, voice.py
- Execute multi-step coding tasks

**CANNOT:**
- Run persistently — dies when you close it
- Access the internet (only local files + git)
- Remember between sessions without brain files

### Claude.ai (this chat)
**CAN:**
- Deep strategy, architecture, complex reasoning
- Build new files and artifacts
- Access web search
- Long-form thinking and planning

**CANNOT:**
- Edit files on your machine directly
- Push to GitHub
- Run code on your machine
- Persist between sessions (uses Claude.ai memory, not brain files)

---

## Daily Operating Flow

### Morning (agent auto-started)
1. Drop previous day's Seller Central Business Report CSV into watch folder
2. Agent auto-processes, flags anomalies
3. Check `http://localhost:8080` for pending decisions
4. Approve/reject via dashboard or terminal

### When dashboard needs fixing
1. `cd C:\Users\User\Downloads\pwa-push`
2. `claude` (opens Claude Code)
3. Type `/scos` to load full context
4. Describe the bug — Claude Code reads index.html, fixes, pushes

### When you want agent to remember something
1. At agent terminal: `update brain: [what to remember]`
2. Agent shows proposal, asks y/n
3. Approve → writes to pwa-push/brain/sleepycat_brain.md → pushes to GitHub

### When you want to think through strategy
1. Open Claude.ai (this chat)
2. All V Group, SleepyCat strategy, complex decisions here

---

## V Group Context (agent does not operate on this yet)

Aman is building V Group — five-arm real estate ecosystem:
- Vcertify (property due diligence)
- Vbrands (white-label products)
- Vcap (capital platform)
- Vdes (renovation)
- Vworkforce (trade booking)

V Group agents: not yet built. Architecture designed, no code written.
Do not mix V Group work into SleepyCat operations.

---

## Emergency Recovery

### Agent won't start
```powershell
cd C:\Users\User\Downloads\sleepycat-agent\sleepycat-agent
python run_agent.py
# If TabError: open agent\core.py, find mixed tabs/spaces, fix indentation
# If AttributeError update_brain: method missing from core.py — add it
```

### Dashboard broken
```powershell
cd C:\Users\User\Downloads\pwa-push
git log --oneline -5        # find last working commit
git diff HEAD~1 index.html  # see what changed
git revert HEAD             # undo last commit if needed
```

### Brain out of sync
```powershell
cd C:\Users\User\Downloads\pwa-push
git pull                    # get latest from GitHub
git status                  # check for conflicts
```

### GitHub push fails
```powershell
cd C:\Users\User\Downloads\pwa-push
git status
git pull --rebase
git push
```
