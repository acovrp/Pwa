"""
SleepyCat SP-API Module
Pulls listings status, sales & traffic from Amazon SP-API.
Pulls Search Term reports from Amazon Advertising API.
Generates daily health callouts.
"""

import csv
import gzip
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
        import gzip as _gzip
        resp = requests.get(
            f"{self.BASE_URL}/reports/2021-06-30/documents/{doc_id}",
            headers=self._headers(),
        )
        resp.raise_for_status()
        doc_info = resp.json()
        url = doc_info["url"]
        compression = doc_info.get("compressionAlgorithm", "")
        # stream=False, don't let requests auto-decompress
        data_resp = requests.get(url, stream=False)
        data_resp.raise_for_status()
        content = data_resp.content
        print(f"[SP-API] {len(content)} bytes, compression={compression or 'none'}")
        # Decompress if GZIP (check both field and magic bytes)
        if compression == "GZIP" or content[:2] == b'\x1f\x8b':
            content = _gzip.decompress(content)
        # Decode, stripping BOM if present
        return content.decode("utf-8-sig")

    def get_listings(self):
        """Returns {asin: {status, sku, title, qty}}"""
        print("[SP-API] Requesting listings report...")
        report_id = self._request_report("GET_MERCHANT_LISTINGS_ALL_DATA")
        doc_id = self._poll_report(report_id)
        raw = self._download_document(doc_id)

        raw = raw.replace(chr(13), "")  # strip \r
        reader = csv.DictReader(io.StringIO(raw), delimiter="\t")
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

    def get_brand_analytics_sqp(self, granularity='MONTH', start_date=None, end_date=None,
                                brand_asins=None):
        """
        Pull Brand Analytics Search Terms report.
        Returns all rows (or only rows where clickedAsin is in brand_asins if provided).
        Each row: term, rank, position (1-3), asin, asin_name, click_share%, conv_share%
        Returns (filtered_rows, raw_data).
        """
        print(f"[BA] Requesting BA report ({granularity} {start_date} to {end_date})...")
        report_id = self._request_report(
            'GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT',
            options={'reportPeriod': granularity},
            start=start_date + 'T00:00:00Z' if start_date else None,
            end=end_date + 'T23:59:59Z' if end_date else None,
        )
        doc_id = self._poll_report(report_id, timeout=600)
        raw_text = self._download_document(doc_id)
        raw = json.loads(raw_text)

        items = raw if isinstance(raw, list) else (
            raw.get('dataByDepartmentAndSearchTerm') or
            raw.get('data') or []
        )

        rows = []
        for item in items:
            asin = item.get('clickedAsin', '').strip()
            if brand_asins and asin not in brand_asins:
                continue
            term = item.get('searchTerm', '').strip()
            if not term:
                continue
            rows.append({
                'term': term,
                'rank': int(item.get('searchFrequencyRank') or 0),
                'position': int(item.get('clickShareRank') or 0),
                'asin': asin,
                'asin_name': item.get('clickedItemName', ''),
                'click_share': round(float(item.get('clickShare') or 0) * 100, 2),
                'conv_share': round(float(item.get('conversionShare') or 0) * 100, 2),
            })

        print(f"[BA] Got {len(rows)} SC rows ({granularity})")
        return rows, raw

    def get_sales_and_traffic(self, date_str=None):
        """Returns {asin: {sessions, page_views, buy_box_pct, cvr, units, revenue}}"""
        if not date_str:
            date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            date_str = date_str[:10]  # strip time component if passed

        print(f"[SP-API] Requesting sales & traffic for {date_str}...")
        report_id = self._request_report(
            "GET_SALES_AND_TRAFFIC_REPORT",
            options={"dateGranularity": "DAY", "asinGranularity": "CHILD"},
            start=date_str + "T00:00:00Z",
            end=date_str + "T23:59:59Z",
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


class AdsAPIClient:
    """Amazon Advertising API client — Search Term reports."""
    BASE_URL = "https://advertising-api-eu.amazon.com"
    TOKEN_URL = "https://api.amazon.com/auth/o2/token"

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

    def _headers(self, profile_id=None):
        h = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
            "Amazon-Advertising-API-ClientId": self.client_id,
        }
        if profile_id:
            h["Amazon-Advertising-API-Scope"] = str(profile_id)
        return h

    def get_india_profile_id(self):
        """Auto-discover the Amazon India advertising profile ID."""
        resp = requests.get(f"{self.BASE_URL}/v2/profiles", headers=self._headers())
        resp.raise_for_status()
        for p in resp.json():
            country = (p.get("countryCode") or "").upper()
            if country == "IN":
                pid = p.get("profileId")
                print(f"[Ads API] Found India profile: {pid}")
                return pid
        raise Exception("[Ads API] No India (IN) profile found in /v2/profiles")

    def request_search_term_report(self, profile_id, start_date, end_date):
        """
        Request a v3 SP Search Term report.
        start_date / end_date: 'YYYY-MM-DD'
        Returns reportId.
        """
        body = {
            "name": f"ST_{start_date}_{end_date}",
            "startDate": start_date,
            "endDate": end_date,
            "configuration": {
                "adProduct": "SPONSORED_PRODUCTS",
                "groupBy": ["searchTerm"],
                "columns": [
                    "date", "campaignName", "adGroupName", "matchType",
                    "customerSearchTerm", "impressions", "clicks", "spend",
                    "sales14d", "orders14d",
                ],
                "reportTypeId": "spSearchTerm",
                "timeUnit": "DAILY",
                "format": "GZIP_JSON",
            },
        }
        resp = requests.post(
            f"{self.BASE_URL}/reporting/reports",
            headers=self._headers(profile_id),
            json=body,
        )
        resp.raise_for_status()
        report_id = resp.json()["reportId"]
        print(f"[Ads API] Search Term report requested: {report_id}")
        return report_id

    def poll_report(self, profile_id, report_id, timeout=600):
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = requests.get(
                f"{self.BASE_URL}/reporting/reports/{report_id}",
                headers=self._headers(profile_id),
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "")
            print(f"[Ads API] Report {report_id} status: {status}")
            if status == "COMPLETED":
                url = data.get("url")
                if not url:
                    raise Exception(f"[Ads API] Report COMPLETED but no download URL in response")
                return url
            if status in ("FAILED", "CANCELLED"):
                raise Exception(f"[Ads API] Report {report_id} failed: {status} — {data.get('statusDetails','')}")
            time.sleep(30)
        raise TimeoutError(f"[Ads API] Report {report_id} timed out after {timeout}s")

    def download_report_json(self, url):
        """Download GZIP_JSON report, decompress, return list of dicts."""
        resp = requests.get(url, stream=False)
        resp.raise_for_status()
        content = resp.content
        if content[:2] == b'\x1f\x8b':
            content = gzip.decompress(content)
        return json.loads(content.decode("utf-8"))

    def get_search_term_csv(self, profile_id, start_date, end_date):
        """Full pipeline: request → poll → download → return CSV text."""
        report_id = self.request_search_term_report(profile_id, start_date, end_date)
        url = self.poll_report(profile_id, report_id)
        records = self.download_report_json(url)
        print(f"[Ads API] Downloaded {len(records)} search term records")
        if not records:
            return None
        # Normalise field names to match buildKeywordsFromRows() expectations
        field_map = {
            "customerSearchTerm": "customer_search_term",
            "impressions": "impressions",
            "clicks": "clicks",
            "spend": "spend",
            "sales14d": "14_day_total_sales",
            "orders14d": "14_day_total_orders",
            "matchType": "match_type",
            "date": "date",
            "campaignName": "campaign_name",
            "adGroupName": "ad_group_name",
        }
        buf = io.StringIO()
        headers = list(field_map.values())
        writer = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            row = {field_map[k]: rec[k] for k in field_map if k in rec}
            writer.writerow(row)
        return buf.getvalue()


def _month_range(year, month):
    """Return ('YYYY-MM-DD', 'YYYY-MM-DD') for first and last day of given month."""
    import calendar
    last = calendar.monthrange(year, month)[1]
    return f'{year}-{month:02d}-01', f'{year}-{month:02d}-{last:02d}'


def _load_sc_asins():
    """Parse ASIN_MAP from pwa-push/index.html to get SleepyCat ASIN set."""
    import re
    html_path = Path(r'C:\Users\User\Downloads\pwa-push\index.html')
    if not html_path.exists():
        return set()
    text = html_path.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'var ASIN_MAP = (\{[^}]+\})', text)
    if not m:
        return set()
    asin_map = json.loads(m.group(1))
    return set(asin_map.keys()), asin_map


def pull_brand_analytics(config, months=2):
    """
    Pull BA Search Terms report for last `months` complete months.
    Filters for SleepyCat ASINs. Compares month-over-month.
    Saves structured JSON to agent_data/ba_sqp.json.
    Returns output path or None on error.
    """
    sp = SPAPIClient(
        client_id=config['spapi_client_id'],
        client_secret=config['spapi_client_secret'],
        refresh_token=config['spapi_refresh_token'],
    )
    agent_data = Path(__file__).parent / 'agent_data'
    agent_data.mkdir(exist_ok=True)

    # Load SC ASINs from dashboard
    try:
        sc_asins, asin_map = _load_sc_asins()
        print(f'[BA] Loaded {len(sc_asins)} SC ASINs from ASIN_MAP')
    except Exception as e:
        print(f'[BA] Could not load ASIN_MAP: {e} — will pull full data')
        sc_asins, asin_map = set(), {}

    # Determine which months to pull
    now = datetime.now()
    pull_months = []
    for i in range(1, months + 1):
        # Go back i months from current month
        mo = now.month - i
        yr = now.year
        while mo <= 0:
            mo += 12
            yr -= 1
        pull_months.append((yr, mo))
    pull_months.reverse()  # chronological order: oldest first

    result = {
        'generated': now.strftime('%Y-%m-%d'),
        'periods': [],
        'terms': {},
    }

    for (yr, mo) in pull_months:
        label = f'{yr}-{mo:02d}'
        start, end = _month_range(yr, mo)
        print(f'[BA] Pulling {label} ({start} to {end})...')
        try:
            rows, raw = sp.get_brand_analytics_sqp('MONTH', start, end,
                                                    brand_asins=sc_asins if sc_asins else None)
            # Save raw sample for debugging
            (agent_data / f'ba_raw_{label}.json').write_text(
                json.dumps({'spec': raw.get('reportSpecification', {}),
                            'sample': (raw.get('dataByDepartmentAndSearchTerm') or raw or [])[:5]},
                           indent=2), encoding='utf-8')

            result['periods'].append(label)
            for r in rows:
                t = r['term']
                product = asin_map.get(r['asin'], r['asin'])
                if t not in result['terms']:
                    result['terms'][t] = {'term': t, 'rank': r['rank'], 'by_period': {}}
                entry = result['terms'][t]
                # Keep lowest rank seen (most popular search term = rank 1)
                if r['rank'] and (not entry['rank'] or r['rank'] < entry['rank']):
                    entry['rank'] = r['rank']
                # If multiple SC ASINs appear for same term+period, keep highest position (pos 1 > 2 > 3)
                existing = entry['by_period'].get(label)
                if not existing or r['position'] < existing['position']:
                    entry['by_period'][label] = {
                        'position': r['position'],
                        'click_share': r['click_share'],
                        'conv_share': r['conv_share'],
                        'asin': r['asin'],
                        'product': product,
                    }
        except Exception as e:
            print(f'[BA] Pull failed for {label}: {e}')

    if not result['terms']:
        print('[BA] No SC terms found — skipping save')
        return None

    # Sort by best rank (lower = more popular search term)
    terms_list = sorted(result['terms'].values(), key=lambda x: x['rank'] or 999999)
    result['terms'] = terms_list

    out = agent_data / 'ba_sqp.json'
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'[BA] Saved {len(terms_list)} SC terms to {out}')
    return out


def pull_search_term_report(config, days_back=30):
    """
    Pull last `days_back` days of Search Term data via Advertising API.
    Saves to agent_data/st_report.csv. Returns path or None on error.
    """
    client_id = config.get("spapi_client_id")
    client_secret = config.get("spapi_client_secret")
    refresh_token = config.get("spapi_refresh_token")
    if not all([client_id, client_secret, refresh_token]):
        print("[Ads API] Missing credentials — skipping")
        return None

    ads = AdsAPIClient(client_id, client_secret, refresh_token)
    try:
        profile_id = config.get("ads_profile_id") or ads.get_india_profile_id()
        end = datetime.now() - timedelta(days=1)
        start = end - timedelta(days=days_back - 1)
        csv_text = ads.get_search_term_csv(
            profile_id,
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d"),
        )
        if not csv_text:
            print("[Ads API] Empty report — skipping save")
            return None
        out_path = Path(__file__).parent / "agent_data" / "st_report.csv"
        out_path.parent.mkdir(exist_ok=True)
        out_path.write_text(csv_text, encoding="utf-8")
        print(f"[Ads API] Saved {out_path}")
        return out_path
    except Exception as e:
        print(f"[Ads API] Search Term pull failed: {e}")
        return None


BR_HISTORY_PATH = Path(__file__).parent / "agent_data" / "br_history.csv"
BR_FIELDS = ["asin", "date", "sessions", "units ordered",
             "ordered product sales", "page views", "buy box percentage"]


def _append_to_br_history(traffic: dict, date_str: str):
    """Append one day's traffic data to br_history.csv. Skips if date already present."""
    BR_HISTORY_PATH.parent.mkdir(exist_ok=True)
    # Dedup: skip if this date already in file
    if BR_HISTORY_PATH.exists():
        content = BR_HISTORY_PATH.read_text(encoding="utf-8")
        if f",{date_str}," in content:
            print(f"[SP-API] br_history already has {date_str} - skipping append")
            return
    write_header = not BR_HISTORY_PATH.exists()
    with open(BR_HISTORY_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=BR_FIELDS)
        if write_header:
            writer.writeheader()
        for asin, t in traffic.items():
            writer.writerow({
                "asin": asin,
                "date": date_str,
                "sessions": t.get("sessions", 0),
                "units ordered": t.get("units", 0),
                "ordered product sales": round(t.get("revenue", 0), 2),
                "page views": t.get("page_views", 0),
                "buy box percentage": t.get("buy_box_pct", 0),
            })
    print(f"[SP-API] Appended {len(traffic)} ASINs to br_history.csv for {date_str}")


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
        traffic_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        data_out["traffic_date"] = traffic_date
        data_out["traffic_updated"] = datetime.now().isoformat()
        _append_to_br_history(traffic, traffic_date)
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
