"""
Envisoft API client using Playwright-based 2-layer authentication.

Follows the working pattern from capture_all_data.py:
  Layer 1: HTTP Basic Auth (tw-admin / tw-admin)
  Layer 2: Web form login inside an iframe (duongngocbach / 1234567890!@#$%^&*())

The F5 BIG-IP WAF requires Chromium's TLS stack — Python requests always gets 403.
Using Playwright keeps everything in Chromium's browser context, preserving the WAF
session cookies and the dual-token auth flow.

Token capture:
  - JWT from POST /api/auth/users/eos-login response body
  - tenantToken from GET /web/eos/admin/dashboard?eos_province_code=1&tenantToken=... redirect URL
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from playwright.async_api import (
    AsyncBrowserContext,
    AsyncPage,
    async_playwright,
)

from ..config import config

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Field name mapping: API response key → column name
# ──────────────────────────────────────────────────────────────────────────────
# Many EnviSoft API responses use keys like "no2", "no2_value", "NO2", etc.
# Normalize to snake_case column names.
FIELD_MAP: dict[str, str] = {
    # Time
    "getTime": "measured_at",
    "get_time": "measured_at",
    # Pollutants
    "pm25": "pm25",
    "PM25": "pm25",
    "pm25_value": "pm25",
    "pm10": "pm10",
    "PM10": "pm10",
    "pm10_value": "pm10",
    "no2": "no2",
    "NO2": "no2",
    "no2_value": "no2",
    "so2": "so2",
    "SO2": "so2",
    "so2_value": "so2",
    "co": "co",
    "CO": "co",
    "co_value": "co",
    "o3": "o3",
    "O3": "o3",
    "o3_value": "o3",
    "no_value": "no_value",
    "NO": "no_value",
    "nox_value": "nox_value",
    "NOX": "nox_value",
    # AQI
    "aqi": "aqi",
    "AQI": "aqi",
    "aqi_category": "aqi_category",
    # Environmental
    "temperature": "temperature",
    "temp": "temperature",
    "humidity": "humidity",
    "humi": "humidity",
    # Wind
    "wind_speed": "wind_speed",
    "winsp": "wind_speed",
    "wind_direction": "wind_direction",
    "windir": "wind_direction",
    # Additional
    "total_pollutant": "total_pollutant",
    "atmospheric_pressure": "atmospheric_pressure",
    "pressure": "atmospheric_pressure",
    "noise_level": "noise_level",
}


def _normalize_field(key: str) -> str:
    """Normalize an API field name to our canonical column name."""
    return FIELD_MAP.get(key, key.lower())


def _normalize_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize field names and convert types in a single API record."""
    record: dict[str, Any] = {}

    for key, value in raw.items():
        col = _normalize_field(key)
        if col in ("measured_at",) and value:
            try:
                # Handle ISO datetime strings
                record[col] = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                record[col] = None
        elif col in ("aqi",) and value is not None:
            try:
                record[col] = int(float(value))
            except (ValueError, TypeError):
                record[col] = None
        elif col in (
            "pm25", "pm10", "no2", "so2", "co", "o3",
            "no_value", "nox_value", "total_pollutant",
            "atmospheric_pressure", "noise_level",
            "temperature", "humidity", "wind_speed", "wind_direction",
        ) and value is not None:
            try:
                record[col] = float(value)
            except (ValueError, TypeError):
                record[col] = None
        elif col == "station_name":
            record[col] = str(value) if value else None
        elif col == "station_code":
            record[col] = str(value) if value else None
        else:
            record[col] = value

    return record


# ──────────────────────────────────────────────────────────────────────────────
# EnvisoftClient
# ──────────────────────────────────────────────────────────────────────────────

class EnvisoftClient:
    """Playwright-based client for Envisoft API with iframe login.

    Authentication flow (matches capture_all_data.py):
      1. Launch Chromium with HTTP Basic Auth credentials
      2. Navigate to BASE_URL — loads inside an iframe
      3. Fill login form INSIDE the iframe
      4. Click ĐĂNG NHẬP → redirects to admin dashboard
      5. Capture JWT from eos-login POST response body
      6. Capture tenantToken from dashboard redirect URL
    """

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context: AsyncBrowserContext | None = None
        self._page: AsyncPage | None = None
        self._jwt: str | None = None
        self._tenant_token: str | None = None

    async def __aenter__(self) -> "EnvisoftClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    # ──────────────────────────────────────────────────────────────────────────
    # Authentication — mirrors capture_all_data.py exactly
    # ──────────────────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Launch Playwright, authenticate via iframe form, capture tokens."""
        logger.info("[AUTH] Starting Playwright and authenticating...")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )

        self._context = await self._browser.new_context(
            http_credentials={
                "username": config.ENVISOFT_BASIC_USER,
                "password": config.ENVISOFT_BASIC_PASS,
            }
        )

        # Capture tokens via response interceptor
        await self._context.on(
            "response", self._on_auth_response
        )

        self._page = await self._context.new_page()

        # ── Step 1: Go to EnviSoft login page ──────────────────────────────
        logger.info("[AUTH] Step 1: Navigating to EnviSoft...")
        await self._page.goto(
            f"{config.ENVISOFT_BASE_URL}/",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        await self._page.wait_for_timeout(3000)

        # ── Step 2: Fill login form inside iframe ──────────────────────────
        logger.info("[AUTH] Step 2: Filling login form inside iframe...")
        frame = self._page.frame_locator("iframe")
        await frame.get_by_role("textbox", name="Tên người dùng").fill(
            config.ENVISOFT_FORM_USER
        )
        await frame.get_by_role("textbox", name="Mật khẩu").fill(
            config.ENVISOFT_FORM_PASS
        )

        # ── Step 3: Click login — page redirects immediately ───────────────
        logger.info("[AUTH] Step 3: Clicking ĐĂNG NHẬP...")
        try:
            await frame.get_by_role("button", name="ĐĂNG NHẬP").click(timeout=5000)
        except Exception as exc:
            logger.info(f"[AUTH] Page redirected (expected): {exc}")

        # ── Step 4: Wait for dashboard ─────────────────────────────────────
        logger.info("[AUTH] Step 4: Waiting for dashboard to load...")
        try:
            await self._page.wait_for_url("**/dashboard/**", timeout=15000)
        except Exception:
            pass
        await self._page.wait_for_timeout(3000)

        # Verify tokens were captured
        if not self._jwt:
            logger.warning("[AUTH] JWT not captured — eos-login may have failed")
        if not self._tenant_token:
            logger.warning("[AUTH] tenantToken not captured — dashboard redirect may have failed")

        # Log session cookies
        cookies = await self._context.cookies()
        admin_cookies = [
            c for c in cookies
            if "admin-qttd" in c.get("domain", "")
        ]
        logger.info(
            f"[AUTH] admin-qttd cookies: {[c['name'] for c in admin_cookies]}"
        )

        auth_ok = bool(self._jwt or self._tenant_token)
        logger.info(f"[AUTH] ✓ Authentication {'successful' if auth_ok else 'FAILED'}")
        if self._jwt:
            logger.info(f"[AUTH]   JWT: {self._jwt[:40]}...")
        if self._tenant_token:
            logger.info(f"[AUTH]   tenantToken: {self._tenant_token[:40]}...")

    async def _on_auth_response(self, response) -> None:
        """Intercept responses to capture JWT and tenantToken."""
        url = response.url

        # 1. tenantToken from dashboard redirect URL (check URL first — no body read)
        if (
            self._tenant_token is None
            and "web/eos/admin/dashboard" in url
        ):
            match = re.search(r"tenantToken=([^&\s]+)", url)
            if match:
                self._tenant_token = match.group(1)
                logger.info(f"[AUTH] Captured tenantToken: {self._tenant_token[:40]}...")

        # 2. JWT from eos-login POST response body
        if self._jwt is None and "eos-login" in url:
            try:
                body = response.text()
                if body and '"token"' in body:
                    match = re.search(r'"token"\s*:\s*"([^"]+)"', body)
                    if match:
                        self._jwt = match.group(1)
                        logger.info(f"[AUTH] Captured JWT: {self._jwt[:40]}...")
            except Exception:
                pass

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("[AUTH] Browser closed")

    # ──────────────────────────────────────────────────────────────────────────
    # Data fetching
    # ──────────────────────────────────────────────────────────────────────────

    async def fetch_station_data(
        self,
        station_id: str,
        station_name: str,
        from_date: str,
        to_date: str,
        view_type: str = "hour",
    ) -> list[dict[str, Any]]:
        """Fetch hourly pollutant data for one station.

        Uses the aqi_hour API endpoint (confirmed working in browser capture).

        Args:
            station_id: EnviSoft station ID
            station_name: Human-readable station name
            from_date: YYYY-MM-DD
            to_date: YYYY-MM-DD
            view_type: hour | minute | 8hour | day

        Returns:
            List of normalized records with station metadata.
        """
        params = {
            "stationId": station_id,
            "from": f"{from_date}T00:00:00",
            "to": f"{to_date}T23:59:59",
        }

        try:
            data = await self._fetch_json(
                f"{config.ENVISOFT_API_BASE_URL}/api/aqi_hour/search/"
                "findByStationIdAndGetTimeBetweenOrderByGetTimeDesc",
                params=params,
            )
        except Exception as exc:
            logger.warning(f"[FETCH] aqi_hour API failed for {station_name}: {exc}")
            # Fallback to exceed-by-time endpoint
            try:
                data = await self._fetch_json(
                    f"{config.ENVISOFT_API_BASE_URL}/api/eos/data-average-by-time/exceed-by-time",
                    params={
                        "stationId": station_id,
                        "fromDate": f"{from_date}T00:00:00",
                        "toDate": f"{to_date}T23:59:59",
                        "viewType": view_type,
                        "dataType": "1",
                        "page": "0",
                        "size": "500",
                    },
                )
            except Exception as exc2:
                logger.warning(f"[FETCH] exceed-by-time fallback also failed: {exc2}")
                return []

        # Parse response — various shapes
        rows = []
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict):
            if "_embedded" in data:
                key = list(data["_embedded"].keys())[0]
                rows = data["_embedded"][key]
            elif "content" in data:
                rows = data["content"]
            else:
                rows = [data] if data else []

        # Normalize each row
        records = []
        for row in rows:
            record = _normalize_record(row)
            record["station_id"] = station_id
            record["station_name"] = station_name
            records.append(record)

        logger.info(f"[FETCH] {station_name}: got {len(records)} records")
        return records

    async def fetch_all_stations_data(
        self,
        from_date: str,
        to_date: str,
        view_type: str = "hour",
    ) -> list[dict[str, Any]]:
        """Fetch hourly data for all configured stations.

        Args:
            from_date: YYYY-MM-DD
            to_date: YYYY-MM-DD
            view_type: Data averaging period

        Returns:
            Combined list of records from all stations.
        """
        all_records = []
        stations = config.TARGET_STATIONS

        for idx, station in enumerate(stations, 1):
            station_id = station["station_id"]
            station_name = station["name"]

            logger.info(
                f"[{idx}/{len(stations)}] Fetching {station_name} "
                f"({station_id})..."
            )

            try:
                records = await self.fetch_station_data(
                    station_id=station_id,
                    station_name=station_name,
                    from_date=from_date,
                    to_date=to_date,
                    view_type=view_type,
                )
                all_records.extend(records)

                if records:
                    logger.info(f"  → {len(records)} records")
                else:
                    logger.warning(f"  → No data returned")

            except Exception as exc:
                logger.error(f"  → Error: {exc}")
                continue

        logger.info(f"[DONE] Total records fetched: {len(all_records)}")
        return all_records

    async def _fetch_json(
        self, url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | list:
        """Navigate browser to JSON URL and parse response.

        Uses browser navigation to keep WAF session alive.
        """
        from urllib.parse import urlencode

        full_url = url + ("?" + urlencode(params) if params else "")

        response = await self._page.goto(full_url, wait_until="domcontentloaded", timeout=60000)

        if response is None:
            raise RuntimeError(f"No response for {full_url}")

        if response.status == 404:
            raise RuntimeError("404 Not Found")

        if response.status not in (200, 302):
            raise RuntimeError(f"HTTP {response.status}: {full_url}")

        text = await response.text()

        # Sometimes the browser redirects to login or blank page
        if not text.strip() or text.strip() in ("", "<html></html>", "<!DOCTYPE html>"):
            raise RuntimeError(f"Empty/invalid response from {full_url}")

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Non-JSON response from {full_url}: {text[:200]}")
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Excel export
    # ──────────────────────────────────────────────────────────────────────────

    def save_to_excel(
        self,
        records: list[dict[str, Any]],
        filename: str,
        sheet_name: str = "Air Quality Data",
    ) -> Path | None:
        """Save records to a styled Excel file.

        Args:
            records: List of data dictionaries.
            filename: Output filename.
            sheet_name: Excel sheet name (max 31 chars).

        Returns:
            Path to saved file, or None if no records.
        """
        if not records:
            logger.warning("No records to save to Excel")
            return None

        df = pd.DataFrame(records)

        # Reorder: metadata first, then data fields
        meta_cols = ["station_id", "station_name", "measured_at"]
        data_cols = [c for c in df.columns if c not in meta_cols]
        df = df[meta_cols + data_cols]

        # Rename columns for readability
        rename = {
            "station_id": "Station ID",
            "station_name": "Station Name",
            "measured_at": "Measured At",
            "pm25": "PM2.5 (µg/m³)",
            "pm10": "PM10 (µg/m³)",
            "no2": "NO₂ (µg/m³)",
            "so2": "SO₂ (µg/m³)",
            "co": "CO (µg/m³)",
            "o3": "O₃ (µg/m³)",
            "aqi": "AQI",
            "aqi_category": "AQI Category",
            "temperature": "Temperature (°C)",
            "humidity": "Humidity (%)",
            "wind_speed": "Wind Speed (m/s)",
            "wind_direction": "Wind Direction (°)",
            "no_value": "NO (µg/m³)",
            "nox_value": "NOₓ (µg/m³)",
            "total_pollutant": "Total Pollutant",
            "atmospheric_pressure": "Atmospheric Pressure (hPa)",
            "noise_level": "Noise Level (dB)",
        }
        df.rename(columns=rename, inplace=True)
        sheet_name = sheet_name[:31]

        output_path = config.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(str(output_path), engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
            ws = writer.sheets[sheet_name]

            from openpyxl.styles import Alignment, Font, PatternFill

            header_fill = PatternFill("solid", fgColor="1F6AA5")
            header_font = Font(bold=True, color="FFFFFF")

            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            for col in ws.columns:
                max_len = max(
                    (len(str(cell.value or "")) for cell in col), default=10
                )
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 45)

        logger.info(f"[EXCEL] Saved {output_path.name} ({len(df)} rows)")
        return output_path
