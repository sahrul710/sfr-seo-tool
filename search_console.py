import os
import time
from datetime import date, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
SITE_URL = "https://sfrcreativeid.blogspot.com/"

# =========================
# CACHE
# =========================
CACHE_DURATION = 600  # 10 menit

_summary_cache = None
_summary_cache_time = 0

_query_cache = None
_query_cache_time = 0

_page_cache = None
_page_cache_time = 0


# =========================
# KONEKSI GOOGLE SEARCH CONSOLE
# =========================
def get_search_console_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build(
        "searchconsole",
        "v1",
        credentials=creds
    )


# =========================
# PERIODE DATA
# =========================
def get_date_range():
    end_date = date.today() - timedelta(days=2)
    start_date = end_date - timedelta(days=27)

    return start_date, end_date


# =========================
# RINGKASAN SEARCH CONSOLE
# =========================
def get_search_console_summary():
    global _summary_cache
    global _summary_cache_time

    current_time = time.time()

    if (
        _summary_cache is not None
        and current_time - _summary_cache_time < CACHE_DURATION
    ):
        return _summary_cache

    service = get_search_console_service()

    start_date, end_date = get_date_range()

    query_body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat()
    }

    response = service.searchanalytics().query(
        siteUrl=SITE_URL,
        body=query_body
    ).execute()

    rows = response.get("rows", [])

    if not rows:
        data = {
            "site_url": SITE_URL,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "clicks": 0,
            "impressions": 0,
            "ctr": 0,
            "position": 0
        }

    else:
        row = rows[0]

        data = {
            "site_url": SITE_URL,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": round(row.get("ctr", 0) * 100, 2),
            "position": round(row.get("position", 0), 2)
        }

    _summary_cache = data
    _summary_cache_time = current_time

    return data


# =========================
# QUERY PENCARIAN TERATAS
# =========================
def get_top_queries(limit=10):
    global _query_cache
    global _query_cache_time

    current_time = time.time()

    if (
        _query_cache is not None
        and current_time - _query_cache_time < CACHE_DURATION
    ):
        return _query_cache

    service = get_search_console_service()

    start_date, end_date = get_date_range()

    query_body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["query"],
        "rowLimit": limit
    }

    response = service.searchanalytics().query(
        siteUrl=SITE_URL,
        body=query_body
    ).execute()

    rows = response.get("rows", [])

    queries = []

    for row in rows:
        query_name = ""

        if row.get("keys"):
            query_name = row["keys"][0]

        queries.append({
            "query": query_name,
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": round(row.get("ctr", 0) * 100, 2),
            "position": round(row.get("position", 0), 2)
        })

    _query_cache = queries
    _query_cache_time = current_time

    return queries


# =========================
# HALAMAN TERATAS
# =========================
def get_top_pages(limit=10):
    global _page_cache
    global _page_cache_time

    current_time = time.time()

    if (
        _page_cache is not None
        and current_time - _page_cache_time < CACHE_DURATION
    ):
        return _page_cache

    service = get_search_console_service()

    start_date, end_date = get_date_range()

    query_body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["page"],
        "rowLimit": limit
    }

    response = service.searchanalytics().query(
        siteUrl=SITE_URL,
        body=query_body
    ).execute()

    rows = response.get("rows", [])

    pages = []

    for row in rows:
        page_url = ""

        if row.get("keys"):
            page_url = row["keys"][0]

        pages.append({
            "page": page_url,
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": round(row.get("ctr", 0) * 100, 2),
            "position": round(row.get("position", 0), 2)
        })

    _page_cache = pages
    _page_cache_time = current_time

    return pages


# =========================
# TEST DI TERMINAL
# =========================
if __name__ == "__main__":

    summary = get_search_console_summary()

    print("\n===== GOOGLE SEARCH CONSOLE =====")
    print("Website:", summary["site_url"])
    print(
        "Periode:",
        summary["start_date"],
        "-",
        summary["end_date"]
    )

    print("\nClicks:", summary["clicks"])
    print("Impressions:", summary["impressions"])
    print("CTR:", str(summary["ctr"]) + "%")
    print("Average Position:", summary["position"])

    print("\n===== QUERY PENCARIAN TERATAS =====")

    queries = get_top_queries()

    if not queries:
        print("Belum ada data query.")

    else:
        for item in queries:
            print(
                item["query"],
                "| Clicks:", item["clicks"],
                "| Impressions:", item["impressions"],
                "| CTR:", str(item["ctr"]) + "%",
                "| Position:", item["position"]
            )

    print("\n===== HALAMAN TERATAS =====")

    pages = get_top_pages()

    if not pages:
        print("Belum ada data halaman.")

    else:
        for item in pages:
            print(
                item["page"],
                "| Clicks:", item["clicks"],
                "| Impressions:", item["impressions"],
                "| CTR:", str(item["ctr"]) + "%",
                "| Position:", item["position"]
            )