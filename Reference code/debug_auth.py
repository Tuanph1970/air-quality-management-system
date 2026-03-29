#!/usr/bin/env python3
"""
Diagnostic script to capture the exact auth headers/tokens the browser uses
when calling admin-qttd.tedp.vn after logging in via tw-envisoft.tedp.vn.

Run this, then inspect the output to see:
  - What Authorization headers are sent
  - What tokens are in localStorage / sessionStorage
  - What the actual request headers look like for a successful stations call
"""

import json
import time
from playwright.sync_api import sync_playwright

MAIN_URL   = "https://tw-envisoft.tedp.vn"
API_BASE   = "https://admin-qttd.tedp.vn"
BASIC_USER = "tw-admin"
BASIC_PASS = "tw-admin"
FORM_USER  = "duongngocbach"
FORM_PASS  = "1234567890!@#$%^&*()"

captured_requests  = []
captured_responses = []

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            http_credentials={"username": BASIC_USER, "password": BASIC_PASS}
        )
        page = context.new_page()

        # Intercept every request/response to admin-qttd.tedp.vn
        def on_request(request):
            if "admin-qttd.tedp.vn" in request.url:
                captured_requests.append({
                    "url":     request.url,
                    "method":  request.method,
                    "headers": dict(request.headers),
                })

        def on_response(response):
            if "admin-qttd.tedp.vn" in response.url:
                print(f"[NET] {response.status} {response.request.method} {response.url[:120]}")
                # Capture API responses for inspection
                if "/api/" in response.url and response.status == 200:
                    try:
                        body = response.text()
                        captured_responses.append({"url": response.url, "body": body[:600]})
                    except Exception:
                        pass

        page.on("request",  on_request)
        page.on("response", on_response)

        # ── Login ──────────────────────────────────────────────────────────────
        print("[1] Navigating to login page ...")
        page.goto(
            f"https://{BASIC_USER}:{BASIC_PASS}@tw-envisoft.tedp.vn/",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(2000)

        print("[2] Filling login form ...")
        try:
            page.wait_for_selector(".blockUI", state="hidden", timeout=10000)
        except Exception:
            pass
        page.get_by_role("textbox", name="Tên người dùng:").fill(FORM_USER)
        page.get_by_role("textbox", name="Mật khẩu:").fill(FORM_PASS)
        page.evaluate("document.querySelector('input[type=submit]').click()")
        page.wait_for_load_state("domcontentloaded")
        print("[3] Logged in, waiting 10 s for SPA to initialise ...")
        page.wait_for_timeout(10000)

        # ── Navigate to the page that loads station data ───────────────────────
        print("[4] Navigating to average data page ...")
        page.goto(
            f"{MAIN_URL}/eos/view_log/average_data_by_time",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        page.wait_for_timeout(8000)   # let XHR calls fire

        # ── Dump localStorage / sessionStorage ────────────────────────────────
        print("\n[5] Checking localStorage on tw-envisoft.tedp.vn ...")
        ls = page.evaluate("() => { const d={}; for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i); d[k]=localStorage.getItem(k);} return d; }")
        for k, v in ls.items():
            print(f"   localStorage[{k!r}] = {v[:120] if v else None}")

        print("\n[6] Checking sessionStorage on tw-envisoft.tedp.vn ...")
        ss = page.evaluate("() => { const d={}; for(let i=0;i<sessionStorage.length;i++){const k=sessionStorage.key(i); d[k]=sessionStorage.getItem(k);} return d; }")
        for k, v in ss.items():
            print(f"   sessionStorage[{k!r}] = {v[:120] if v else None}")

        # ── Show all cookies ───────────────────────────────────────────────────
        print("\n[7] All cookies:")
        for c in context.cookies():
            print(f"   {c['name']!r:40s}  domain={c['domain']!r:30s}  value={c['value'][:40]!r}")

        # ── Show full URLs for API calls (untruncated) ────────────────────────
        print(f"\n[8] API requests to admin-qttd.tedp.vn (full URLs):")
        for req in captured_requests:
            if "/api/" in req["url"]:
                print(f"\n  {req['method']} {req['url']}")
                for h, v in req["headers"].items():
                    if h.lower() in ("authorization", "x-auth-token", "x-access-token",
                                      "cookie", "x-tenant-code", "x-tenant-id", "tenant-id",
                                      "x-api-key"):
                        print(f"    {h}: {v[:200]}")

        # ── Show tenant-context response ───────────────────────────────────────
        print("\n[8b] Captured API responses:")
        for r in captured_responses:
            if "tenant-context" in r["url"] or "stations" in r["url"]:
                print(f"\n  URL:  {r['url']}")
                print(f"  Body: {r['body'][:300]}")

        # ── Try fetching tenant-context from page JS context ──────────────────
        print("\n[9] Fetching tenant-context from page JS context ...")
        tc_result = page.evaluate(f"""
            async () => {{
                try {{
                    const r = await fetch('{API_BASE}/api/tenant-context');
                    return {{ status: r.status, body: await r.text() }};
                }} catch(e) {{ return {{ error: String(e) }}; }}
            }}
        """)
        print(f"  status: {tc_result.get('status')}")
        print(f"  body:   {str(tc_result.get('body', ''))[:400]}")

        # ── Try stations with tenantCode extracted from page ──────────────────
        print("\n[10] Trying stations endpoint with full parameters from page context ...")
        stations_result = page.evaluate(f"""
            async () => {{
                // First get the tenantCode from tenant-context
                let tenantCode = '';
                try {{
                    const tc = await fetch('{API_BASE}/api/tenant-context');
                    const tcData = await tc.json();
                    tenantCode = tcData.tenantCode || tcData.code || tcData.tenant_code || '';
                    console.log('tenantCode:', tenantCode, 'full:', JSON.stringify(tcData).substring(0,200));
                }} catch(e) {{
                    console.log('tenant-context error:', e);
                }}

                const url = '{API_BASE}/api/stations/search/findByStationTypeAndProvinceIdAndFtpConnectionStatusAndStatusAndUsingStatusAndStationNameAndTenantCode'
                    + '?stationType=KK&provinceId=&ftpConnectionStatus=&status=1&usingStatus=1&stationName=&tenantCode=' + tenantCode + '&page=0&size=5';
                console.log('stations url:', url);
                try {{
                    const r = await fetch(url);
                    return {{ status: r.status, body: await r.text(), tenantCode }};
                }} catch(e) {{ return {{ error: String(e), tenantCode }}; }}
            }}
        """)
        print(f"  tenantCode: {stations_result.get('tenantCode')!r}")
        print(f"  status:     {stations_result.get('status')}")
        print(f"  body:       {str(stations_result.get('body', ''))[:400]}")

        # ── Console messages (to see console.log output) ───────────────────────
        print("\n[11] Collecting console output for 2s ...")
        page.wait_for_timeout(2000)

        browser.close()

    print("\n[DONE] Review output above to find the auth mechanism.")


if __name__ == "__main__":
    main()
