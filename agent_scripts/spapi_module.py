"""
SleepyCat SP-API Module
Pulls listings status, sales & traffic from Amazon SP-API.
Generates daily health callouts.
"""

import csv
import io
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests


class SPAPIClient:
    BASE_URL = "https://sellingpartnerapi-eu.amazon.com"
    TOKEN_URL = "https://api.amazon.com/auth/o2/token"
    MARKETPLACE_ID = "A21TJRUUN4KGV"  # Amazon India

    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._access_token = None
        self._token_expiry = None

    def _get_access_token(self):
        if self._access_token and datetime.now() < self._token_expiry:
            return self._access_token
        resp = requests.post(self.TOKEN_URL, data={
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        })
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expiry = datetime.now() + timedelta(seconds=3500)
        return self._access_token

    def _headers(self):
        return {
            "x-amz-access-token": self._get_access_token(),
            "Content-Type": "application/json",
        }

    def _request_report(self, report_type, options=None, start=None, end=None):
        body = {"reportType": report_type, "marketplaceIds": [self.MARKETPLACE_ID]}
        if options:
            body["reportOptions"] = options
        if start:
            body["dataStartTime"] = start
        if end:
            body["dataEndTime"] = end
        resp = requests.post(
            f"{self.BASE_URL}/reports/2021-06-30/reports",
            headers=self._headers(),
            json=body,
        )
        resp.raise_for_status()
        return resp.json()["reportId"]

    def _poll_report(self, report_id, timeout=300):
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = requests.get(
                f"{self.BASE_URL}/reports/2021-06-30/reports/{report_id}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            status = data["processingStatus"]
            if status == "DONE":
                return data["reportDocumentId"]
            if status in ("FATAL", "CANCELLED"):
                raise Exception(f"Report {report_id} failed with status: {status}")
            time.sleep(20)
        raise TimeoutError(f"Report {report_id} timed out after {timeout}s")

    def _download_document(self, doc_id):
        resp = requests.get(
            f"{self.BASE_URL}/reports/2021-06-30/documents/{doc_id}",
            headers=self._headers(),
        )
        resp.raise_for_status()
        url = resp.json()["url"]
        data_resp = requests.get(url)
        data_resp.raise_for_status()
        return data_resp.text

    def get_listings(self):
        """Returns {asin: {status, sku, title, qty}}"""
        print("[SP-API] Requesting listings report...")
        report_id = self._request_report("GET_MERCHANT_LISTINGS_ALL_DATA")
        doc_id = self._poll_report(report_id)
        raw = self._download_document(doc_id)

        reader = csv.DictReader(io.StringIO(raw, newline=""), delimiter="\t")
        listings = {}
        for row in reader:
            asin = row.get("asin1", "").strip()
            if asin:
                listings[asin] = {
                    "status": row.get("status", "").strip(),
                    "sku": row.get("seller-sku", "").strip(),
                    "title": row.get("item-name", "").strip()[:60],
                    "qty": row.get("quantity", "0").strip(),
                }
        print(f"[SP-API] Got {len(listings)} listings")
        return listings

    def get_sales_and_traffic(self, date_str=None):
        """Returns {asin: {sessions, page_views, buy_box_pct, cvr, units, revenue}}"""
        if not date_str:
            yesterday = datetime.now() - timedelta(days=1)
            date_str = yesterday.strftime("%Y-%m-%dT00:00:00Z")

        print(f"[SP-API] Requesting sales & traffic for {date_str[:10]}...")
        report_id = self._request_report(
            "GET_SALES_AND_TRAFFIC_REPORT",
            options={"dateGranularity": "DAY", "asinGranularity": "CHILD"},
            start=date_str,
            end=date_str,
        )
        doc_id = self._poll_report(report_id)
        raw = self._download_document(doc_id)

        data = json.loads(raw)
        result = {}
        for item in data.get("salesAndTrafficByAsin", []):
            asin = item.get("childAsin", "")
            if not asin:
                continue
            traffic = item.get("trafficByAsin", {})
            sales = item.get("salesByAsin", {})
            result[asin] = {
                "sessions": traffic.get("sessions", 0),
                "page_views": traffic.get("pageViews", 0),
                "buy_box_pct": traffic.get("buyBoxPercentage", 0),
                "cvr": traffic.get("unitSessionPercentage", 0),
                "units": sales.get("unitsOrdered", 0),
                "revenue": sales.get("orderedProductSales", {}).get("amount", 0),
            }
        print(f"[SP-API] Got traffic data for {len(result)} ASINs")
        return result


def run_daily_checks(config, send_telegram_fn=None):
    """
    Pull SP-API data, run health checks, generate callouts.
    Saves output to agent_data/spapi_data.json.
    Returns list of callouts.
    """
    sp = SPAPIClient(
        client_id=config["spapi_client_id"],
        client_secret=config["spapi_client_secret"],
        refresh_token=config["spapi_refresh_token"],
    )

    print(f"\n[SP-API] Daily checks — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    callouts = []
    data_out = {}

    # Pull listings
    try:
        listings = sp.get_listings()
        data_out["listings"] = listings
        data_out["listings_updated"] = datetime.now().isoformat()
    except Exception as e:
        print(f"[SP-API] Listings pull failed: {e}")
        listings = {}

    # Pull sales & traffic
    try:
        traffic = sp.get_sales_and_traffic()
        data_out["traffic"] = traffic
        data_out["traffic_date"] = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        data_out["traffic_updated"] = datetime.now().isoformat()
    except Exception as e:
        print(f"[SP-API] Traffic pull failed: {e}")
        traffic = {}

    # Callout: ASIN inactive or 0 sessions
    for asin, t in traffic.items():
        listing = listings.get(asin, {})
        status = listing.get("status", "unknown").lower()
        title = listing.get("title", asin)

        if status != "active" and (t["sessions"] == 0 or t["page_views"] == 0):
            callouts.append({
                "type": "inactive_asin",
                "severity": "HIGH",
                "asin": asin,
                "title": title,
                "status": status,
                "message": f"🚨 *{asin}* — status: `{status}`, 0 sessions yesterday\n_{title}_",
            })

    # Callout: Buy box below 80%
    for asin, t in traffic.items():
        bb = t.get("buy_box_pct", 100)
        if bb < 80 and t.get("sessions", 0) > 20:
            title = listings.get(asin, {}).get("title", asin)
            callouts.append({
                "type": "low_buy_box",
                "severity": "HIGH" if bb < 50 else "MEDIUM",
                "asin": asin,
                "title": title,
                "buy_box_pct": bb,
                "message": f"⚠️ *{asin}* — Buy Box {bb:.1f}% ({t['sessions']} sessions)\n_{title}_",
            })

    # Callout: CVR below 1% with meaningful traffic
    for asin, t in traffic.items():
        cvr = t.get("cvr", 0)
        if cvr < 1.0 and t.get("sessions", 0) > 50:
            title = listings.get(asin, {}).get("title", asin)
            callouts.append({
                "type": "low_cvr",
                "severity": "MEDIUM",
                "asin": asin,
                "title": title,
                "cvr": cvr,
                "message": f"📉 *{asin}* — CVR {cvr:.2f}% on {t['sessions']} sessions\n_{title}_",
            })

    data_out["callouts"] = callouts
    data_out["generated_at"] = datetime.now().isoformat()

    # Save to agent_data/
    output_path = Path("agent_data/spapi_data.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data_out, f, indent=2, ensure_ascii=False)
    print(f"[SP-API] Saved to {output_path}")

    # Send Telegram summary
    if callouts and send_telegram_fn:
        date_label = (datetime.now() - timedelta(days=1)).strftime("%d %b %Y")
        msg = (
            f"📊 *SleepyCat Daily Health — {date_label}*\n"
            f"ASINs checked: {len(traffic)}\n"
            f"Callouts: {len(callouts)}\n\n"
        )
        for c in callouts[:10]:
            msg += f"{c['message']}\n\n"
        if len(callouts) > 10:
            msg += f"_...and {len(callouts) - 10} more. Check agent\\_data/spapi\\_data.json_"
        send_telegram_fn(msg)
    elif send_telegram_fn:
        date_label = (datetime.now() - timedelta(days=1)).strftime("%d %b %Y")
        send_telegram_fn(
            f"✅ *SleepyCat Daily Health — {date_label}*\n"
            f"All {len(traffic)} ASINs clean. No callouts."
        )

    return callouts
