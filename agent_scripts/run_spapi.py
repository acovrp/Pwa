# SleepyCat SP-API Daily Runner
# Schedule via Windows Task Scheduler at 7:30 AM daily.
# Program: python
# Arguments: run_spapi.py
# Start in: C:/Users/User/Downloads/sleepycat-agent/sleepycat-agent

import shutil
import subprocess
import sys
from pathlib import Path

import requests
import yaml

PWA_PUSH_PATH = Path(r"C:\Users\User\Downloads\pwa-push")


def _git_push_file(rel_path: str, commit_msg: str):
    """Stage one file, commit if changed, push."""
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain", rel_path],
            cwd=PWA_PUSH_PATH, capture_output=True, text=True
        ).stdout.strip()
        if not status:
            print(f"[Dashboard] {rel_path} unchanged — skipping git push")
            return
        subprocess.run(["git", "add", rel_path], cwd=PWA_PUSH_PATH, check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=PWA_PUSH_PATH, check=True)
        subprocess.run(["git", "push"], cwd=PWA_PUSH_PATH, check=True)
        print(f"[Dashboard] Pushed {rel_path} to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"[Dashboard] Git push failed: {e}")


def push_br_to_dashboard():
    src = Path(__file__).parent / "agent_data" / "br_history.csv"
    dst = PWA_PUSH_PATH / "data" / "br_history.csv"
    if not src.exists():
        print("[Dashboard] br_history.csv not found — skipping push")
        return
    dst.parent.mkdir(exist_ok=True)
    shutil.copy2(src, dst)
    from datetime import date
    _git_push_file("data/br_history.csv", f"Auto: br_history.csv {date.today()}")


def push_st_to_dashboard(config):
    """Pull Search Terms via Advertising API and push to dashboard.

    Falls back to watch-folder scan if Ads API fails (e.g. profile not found).
    """
    from datetime import date
    from spapi_module import pull_search_term_report

    src = pull_search_term_report(config, days_back=30)

    # Fallback: watch folder if API pull failed
    if not src:
        watch = Path(r"C:\Users\User\Documents\SleepyCat-Data")
        if watch.exists():
            candidates = [
                f for f in watch.iterdir()
                if f.is_file() and f.suffix.lower() in (".csv", ".tsv")
                and any(kw in f.name.lower() for kw in ("search_term", "searchterm", "search-term"))
            ]
            if candidates:
                src = max(candidates, key=lambda f: f.stat().st_mtime)
                print(f"[ST] Ads API failed — falling back to watch folder: {src.name}")

    if not src:
        print("[ST] No search term data available — skipping push")
        return

    dst = PWA_PUSH_PATH / "data" / "st_report.csv"
    dst.parent.mkdir(exist_ok=True)
    shutil.copy2(src, dst)
    _git_push_file("data/st_report.csv", f"Auto: st_report.csv {date.today()}")

def push_ba_to_dashboard(config):
    """Pull Brand Analytics SQP (weekly + monthly) and push to dashboard."""
    from datetime import date
    from spapi_module import pull_brand_analytics
    src = pull_brand_analytics(config, months=2)
    if not src:
        print("[BA] No data to push")
        return
    dst = PWA_PUSH_PATH / "data" / "ba_sqp.json"
    dst.parent.mkdir(exist_ok=True)
    shutil.copy2(src, dst)
    _git_push_file("data/ba_sqp.json", f"Auto: ba_sqp.json {date.today()}")


sys.path.insert(0, str(Path(__file__).parent))
from spapi_module import run_daily_checks


def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def send_telegram(config, message):
    token = config.get("telegram_bot_token", "")
    chat_id = str(config.get("telegram_owner_id", "0"))
    if not token or chat_id == "0" or "YOUR" in token:
        print("[Telegram] Not configured — skipping.")
        return
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10,
        )
        if resp.ok:
            print("[Telegram] Callout sent.")
        else:
            print(f"[Telegram] Failed: {resp.text}")
    except Exception as e:
        print(f"[Telegram] Error: {e}")


def main():
    print("=" * 50)
    print("  SleepyCat SP-API Daily Runner")
    print("=" * 50)

    config = load_config()

    missing = [k for k in ("spapi_client_id", "spapi_client_secret", "spapi_refresh_token")
               if not config.get(k)]
    if missing:
        print(f"ERROR: Missing from config.yaml: {', '.join(missing)}")
        sys.exit(1)

    callouts = run_daily_checks(
        config,
        send_telegram_fn=lambda msg: send_telegram(config, msg),
    )

    push_br_to_dashboard()
    push_st_to_dashboard(config)
    push_ba_to_dashboard(config)

    print(f"\n{'=' * 50}")
    print(f"  Done. {len(callouts)} callout(s).")
    print("=" * 50)
    for c in callouts:
        sev = c.get("severity", "")
        print(f"  [{sev}] {c['asin']} — {c['type']}")


if __name__ == "__main__":
    main()
