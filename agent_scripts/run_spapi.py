# SleepyCat SP-API Daily Runner
# Schedule via Windows Task Scheduler at 7:30 AM daily.
# Program: python
# Arguments: run_spapi.py
# Start in: C:/Users/User/Downloads/sleepycat-agent/sleepycat-agent

import sys
from pathlib import Path

import requests
import yaml

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

    print(f"\n{'=' * 50}")
    print(f"  Done. {len(callouts)} callout(s).")
    print("=" * 50)
    for c in callouts:
        sev = c.get("severity", "")
        print(f"  [{sev}] {c['asin']} — {c['type']}")


if __name__ == "__main__":
    main()
