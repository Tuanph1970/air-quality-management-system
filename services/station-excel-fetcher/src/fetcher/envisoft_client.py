"""
Envisoft API client with Playwright-based 2-layer authentication.

Layer 1: HTTP Basic Auth (tw-admin / tw-admin)
Layer 2: Web form login (duongngocbach / 1234567890!@#$%^&*())

The F5 BIG-IP WAF ties authentication to the TLS fingerprint + cookie pair.
Python requests uses a different TLS stack and always gets 403.
Using Playwright's context keeps everything in Chromium's network stack.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import pandas as pd
from playwright.async_api import AsyncBrowserContext, AsyncPage, async_playwright

from .config import config

logger = logging.getLogger(__name__)


class EnvisoftClient:
    """Client for fetching air quality data from Envisoft (tw-envisoft.tedp.vn).

    Uses Playwright to handle 2-layer authentication:
    - Layer 1: HTTP Basic Auth
    - Layer 2: Web form login

    The established session is reused for all API calls via browser navigation,
    which preserves the WAF session cookies.
    """

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context: Optional[AsyncBrowserContext] = None
        self._page: Optional[AsyncPage] = None
        self._stations_cache: Optional[List[Dict[str, Any]]] = None

    async def __aenter__(self) -> "EnvisoftClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def start(self) -> None:
        """Initialize Playwright, start browser, and authenticate."""
        logger.info("[AUTH] Starting Playwright and authenticating to Envisoft...")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )

        # Create context with HTTP Basic Auth
        self._context = await self._browser.new_context(
            http_credentials={
                "username": config.ENVISOFT_BASIC_USER,
                "password": config.ENVISOFT_BASIC_PASS,
            }
        )

        # Set realistic browser headers
        await self._context.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
        })

        self._page = await self._context.new_page()

        # Layer 1: Navigate with Basic Auth embedded in URL
        logger.info("[AUTH] Step 1: HTTP Basic Auth...")
        await self._page.goto(
            f"https://{config.ENVISOFT_BASIC_USER}:{config.ENVISOFT_BASIC_PASS}@"
            f"{config.ENVISOFT_BASE_URL.replace('https://', '')}/",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        await self._page.wait_for_timeout(1500)

        # Layer 2: Web form login
        logger.info("[AUTH] Step 2: Web form login...")
        try:
            await self._page.wait_for_selector(".blockUI", state="hidden", timeout=15000)
        except Exception:
            pass  # Block UI might not appear

        # Fill login form - selectors may need adjustment based on actual page
        try:
            # Try common username field selectors
            username_field = await self._page.query_selector(
                'input[name="username"], input[id="username"], input[type="text"]:first-of-type'
            )
            if username_field:
                await username_field.fill(config.ENVISOFT_FORM_USER)

            password_field = await self._page.query_selector(
                'input[name="password"], input[id="password"], input[type="password"]'
            )
            if password_field:
                await password_field.fill(config.ENVISOFT_FORM_PASS)

            # Submit
            submit_btn = await self._page.query_selector(
                'input[type="submit"], button[type="submit"], button:has-text("Login")'
            )
            if submit_btn:
                await submit_btn.click()
            else:
                # Fallback: evaluate JS click
                await self._page.evaluate(
                    "document.querySelector('input[type=submit']?.click() || "
                    "document.querySelector('form')?.submit()"
                )
        except Exception as e:
            logger.warning(f"Form login attempt failed: {e}")

        await self._page.wait_for_load_state("domcontentloaded")

        # Wait for redirect to admin-qttd.tedp.vn
        logger.info("[AUTH] Waiting for redirect to admin portal...")
        await self._page.wait_for_timeout(10000)

        # Navigate to data page to establish WAF session
        logger.info("[AUTH] Establishing WAF session...")
        await self._page.goto(
            f"{config.ENVISOFT_BASE_URL}/eos/view_log/average_data_by_time",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        await self._page.wait_for_timeout(5000)

        # Log session info
        cookies = await self._context.cookies()
        admin_cookies = [c for c in cookies if "admin-qttd" in c.get("domain", "")]
        logger.info(
            f"[AUTH] Session established. admin-qttd.tedp.vn cookies: "
            f"{[c['name'] for c in admin_cookies]}"
        )

        logger.info("[AUTH] ✓ Authentication complete")

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("[AUTH] ✓ Browser closed")

    # ─────────────────────────────────────────────────────────────────────────
    # API helpers
    # ─────────────────────────────────────────────────────────────────────────
    async def _api_get(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Navigate browser to API URL and parse JSON response.

        Uses browser navigation to preserve WAF session.
        """
        full_url = url + ("?" + urlencode(params) if params else "")
        logger.debug(f"API GET: {full_url[:100]}...")

        response = await self._page.goto(
            full_url, wait_until="domcontentloaded", timeout=60000
        )

        if response is None:
            raise RuntimeError(f"Navigation returned no response: {full_url}")

        if response.status not in (200, 404):
            raise RuntimeError(f"HTTP {response.status}: {full_url}")

        if response.status == 404:
            raise RuntimeError("404")

        text = await response.text()
        return json.loads(text)

    # ─────────────────────────────────────────────────────────────────────────
    # Station API
    # ─────────────────────────────────────────────────────────────────────────
    async def get_all_stations(
        self,
        station_type: str = "KK",
        province_id: str = "",
    ) -> List[Dict[str, Any]]:
        """Fetch all stations filtered by type and province.

        Args:
            station_type: Station type (KK=Air, NT=Wastewater, NM=Surface water)
            province_id: Province filter

        Returns:
            List of station dictionaries
        """
        if self._stations_cache is not None:
            logger.info("Using cached station list")
            return self._stations_cache

        all_stations = []
        page_num = 0

        logger.info(f"[STATIONS] Fetching stations (type={station_type})...")

        while True:
            params = {
                "stationType": station_type,
                "stationName": "",
                "areaIds": province_id,
                "page": page_num,
                "size": 50,
            }

            try:
                data = await self._api_get(
                    config.ENVISOFT_STATIONS_ENDPOINT, params
                )
            except Exception as e:
                logger.error(f"[ERROR] Stations API failed: {e}")
                break

            stations = data.get("_embedded", {}).get("stations", [])
            if not stations:
                break

            all_stations.extend(stations)
            page_info = data.get("page", {})
            total_pages = page_info.get("totalPages", 1)
            logger.info(f"  Page {page_num + 1}/{total_pages}: {len(stations)} stations")

            if page_num >= total_pages - 1:
                break
            page_num += 1

        logger.info(f"[STATIONS] Total found: {len(all_stations)}")
        self._stations_cache = all_stations
        return all_stations

    # ─────────────────────────────────────────────────────────────────────────
    # Data API
    # ─────────────────────────────────────────────────────────────────────────
    async def fetch_station_data(
        self,
        station: Dict[str, Any],
        from_date: str,
        to_date: str,
        view_type: str = "hour",
        data_type: int = 1,
    ) -> List[Dict[str, Any]]:
        """Fetch average data for a single station.

        Args:
            station: Station dictionary with id, name, stationCode
            from_date: Start date YYYY-MM-DD
            to_date: End date YYYY-MM-DD
            view_type: 'minute' | 'hour' | '8hour' | 'day' | 'month'
            data_type: 1 = original data

        Returns:
            List of data records
        """
        station_id = station.get("id", "")
        station_name = station.get("stationName") or station.get("name") or station_id

        all_rows = []
        page_num = 0

        # API expects datetime in ISO format
        from_dt = f"{from_date}T00:00:00"
        to_dt = f"{to_date}T23:59:59"

        while True:
            params = {
                "stationId": station_id,
                "fromDate": from_dt,
                "toDate": to_dt,
                "viewType": view_type,
                "dataType": data_type,
                "page": page_num,
                "size": config.ENVISOFT_PAGE_SIZE,
            }

            try:
                data = await self._api_get(
                    config.ENVISOFT_DATA_ENDPOINT, params
                )
            except json.JSONDecodeError:
                # Non-JSON response (404) means no data
                break
            except Exception as e:
                logger.warning(f"Request failed for {station_name}: {e}")
                break

            # Handle paginated response shapes
            if isinstance(data, list):
                rows = data
                total_pages = 1
            elif "content" in data:
                rows = data["content"]
                total_pages = data.get("totalPages", 1)
            elif "_embedded" in data:
                key = list(data["_embedded"].keys())[0]
                rows = data["_embedded"][key]
                total_pages = data.get("page", {}).get("totalPages", 1)
            else:
                rows = [data] if data else []
                total_pages = 1

            # Annotate each row with station metadata
            for row in rows:
                row["station_name"] = station_name
                row["station_id"] = station_id
                row["station_code"] = station.get("stationCode") or station.get("code") or ""

            all_rows.extend(rows)

            if page_num >= total_pages - 1:
                break
            page_num += 1

        logger.debug(f"  Fetched {len(all_rows)} rows for {station_name}")
        return all_rows

    async def fetch_all_stations_data(
        self,
        from_date: str,
        to_date: str,
        station_type: str = "KK",
        view_type: str = "hour",
    ) -> List[Dict[str, Any]]:
        """Fetch data for all stations in a date range.

        Args:
            from_date: Start date YYYY-MM-DD
            to_date: End date YYYY-MM-DD
            station_type: Filter by station type
            view_type: Data averaging period

        Returns:
            Combined list of all records from all stations
        """
        # First get all stations
        stations = await self.get_all_stations(station_type=station_type)

        if not stations:
            logger.warning("No stations found")
            return []

        all_records = []

        for idx, station in enumerate(stations, 1):
            station_name = station.get("stationName") or station.get("name") or "Unknown"
            logger.info(f"[{idx:>3}/{len(stations)}] Fetching: {station_name}")

            try:
                records = await self.fetch_station_data(
                    station=station,
                    from_date=from_date,
                    to_date=to_date,
                    view_type=view_type,
                )
                all_records.extend(records)

                if records:
                    logger.info(f"  → {len(records)} records")
                else:
                    logger.info(f"  → No data")

            except Exception as e:
                logger.warning(f"  → Error: {e}")
                continue

        logger.info(f"[DONE] Total records fetched: {len(all_records)}")
        return all_records

    # ─────────────────────────────────────────────────────────────────────────
    # Excel Export
    # ─────────────────────────────────────────────────────────────────────────
    def save_to_excel(
        self,
        records: List[Dict[str, Any]],
        filename: str,
        sheet_name: str = "Data",
    ) -> Path:
        """Save records to Excel file with styling.

        Args:
            records: List of data dictionaries
            filename: Output filename (without path)
            sheet_name: Excel sheet name

        Returns:
            Path to saved file
        """
        if not records:
            logger.warning("No records to save")
            return Path("")

        df = pd.DataFrame(records)

        # Move station metadata columns to front
        meta_cols = [c for c in ["station_name", "station_code", "station_id"] if c in df.columns]
        other_cols = [c for c in df.columns if c not in meta_cols]
        df = df[meta_cols + other_cols]

        # Rename for better readability
        df.rename(columns={
            "station_name": "Station Name",
            "station_code": "Station Code",
            "station_id": "Station ID",
        }, inplace=True)

        # Sheet name max 31 chars
        sheet_name = sheet_name[:31]

        output_path = config.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with styling
        with pd.ExcelWriter(str(output_path), engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)

            ws = writer.sheets[sheet_name]

            # Style header
            from openpyxl.styles import Font, PatternFill, Alignment

            header_fill = PatternFill("solid", fgColor="1F6AA5")
            header_font = Font(bold=True, color="FFFFFF")

            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            # Auto-width columns
            for col in ws.columns:
                max_len = max(
                    (len(str(cell.value or "")) for cell in col), default=10
                )
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 45)

        logger.info(f"[SAVED] {output_path.name} ({len(df)} rows)")
        return output_path