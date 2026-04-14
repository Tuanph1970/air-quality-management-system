"""
Envisoft data fetcher using Playwright-based Excel export.

Authentication flow:
  Layer 1: HTTP Basic Auth (tw-admin / tw-admin) on tw-envisoft.tedp.vn
  Layer 2: Web form login inside iframe (duongngocbach / 1234567890!@#$%^&*())

Data flow:
  1. Login via iframe → captures tenantToken from iframe src URL
  2. Navigate to "Dữ liệu trung bình theo thời gian" page
  3. For each station: set date range → wait for data to load
  4. Click "XUẤT FILE" → Playwright captures the download
  5. Parse Excel with openpyxl → transform to DB records
  6. Batch insert into MySQL

Excel columns (5-minute intervals):
  TT | THỜI GIAN ĐO | NO | O3 | Radiation | CO | WD | NO2 | P | PM2.5 | Temp | RH | NOx | SO2 | PM10
"""

from __future__ import annotations

import asyncio
import logging
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import openpyxl
import pandas as pd
from playwright.async_api import (
    BrowserContext,
    Page,
    async_playwright,
    Error as PlaywrightError,
)

from ..config import config

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Excel column → canonical field name
# ──────────────────────────────────────────────────────────────────────────────
# The Envisoft Excel export has Vietnamese headers with units embedded.
# Parse them by matching the pollutant name prefix.
_EXCEL_COLUMN_MAP: list[tuple[str, str | None]] = [
    # (header_prefix, canonical_field)
    ("TT", None),                        # Row index — skip
    ("THỜI GIAN ĐO", "measured_at"),     # Datetime
    ("NO (µg/Nm3)", "no_value"),
    ("O3 (µg/Nm3)", "o3"),
    ("Radiation (W/m2)", "radiation"),
    ("CO (µg/Nm3)", "co"),
    ("WD (degree)", "wind_direction"),
    ("NO2 (µg/Nm3)", "no2"),
    ("P (hPa)", "atmospheric_pressure"),
    ("PM205 (µg/Nm3)", "pm25"),          # PM2.5 in Excel header
    ("PM25", "pm25"),                    # fallback
    ("Temp (oC)", "temperature"),
    ("RH (%)", "humidity"),
    ("NOx (µg/Nm3)", "nox_value"),
    ("SO2 (µg/Nm3)", "so2"),
    ("PM10 (µg/Nm3)", "pm10"),
]


def _parse_excel_headers(headers: list[str]) -> dict[int, str]:
    """Map Excel column index → canonical field name."""
    mapping: dict[int, str] = {}
    for col_idx, header in enumerate(headers, start=1):
        for prefix, field in _EXCEL_COLUMN_MAP:
            if header.startswith(prefix):
                if field is None:
                    break  # skip this column
                mapping[col_idx] = field
                break
    return mapping


def _parse_excel_datetime(value: Any) -> datetime | None:
    """Parse Excel datetime to Python datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        value = value.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                pass
    return None


def _parse_float(value: Any) -> float | None:
    """Parse numeric value, return None if not convertible."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value != "" else None
    s = str(value).strip()
    if s in ("", "-", "N/A", "null"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_excel_to_records(
    excel_path: str | Path,
    station_id: str,
    station_name: str,
) -> list[dict[str, Any]]:
    """Parse an Envisoft Excel export into normalized record dicts.

    Args:
        excel_path: Path to the downloaded Excel file.
        station_id: Station ID from config.
        station_name: Station display name from config.

    Returns:
        List of record dicts ready for DB insertion.
    """
    wb = openpyxl.load_workbook(str(excel_path), data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        logger.warning(f"[EXCEL] Empty sheet: {excel_path}")
        return []

    header_row = [str(c) if c is not None else "" for c in rows[0]]
    col_map = _parse_excel_headers(header_row)
    logger.info(f"[EXCEL] Column map: {col_map}")

    records: list[dict[str, Any]] = []
    for row_idx, row in enumerate(rows[1:], start=2):
        measured_at = None
        record: dict[str, Any] = {"station_id": station_id, "station_name": station_name}

        for col_idx, field in col_map.items():
            try:
                raw = row[col_idx - 1]  # openpyxl is 1-based
            except IndexError:
                continue

            if field == "measured_at":
                measured_at = _parse_excel_datetime(raw)
                if measured_at:
                    record["measured_at"] = measured_at
            elif field in (
                "no_value", "nox_value", "so2", "no2", "o3", "co",
                "pm25", "pm10", "temperature", "humidity",
                "wind_speed", "wind_direction",
                "atmospheric_pressure", "radiation",
            ):
                record[field] = _parse_float(raw)
            else:
                record[field] = raw

        if measured_at is None:
            logger.warning(f"[EXCEL] Row {row_idx}: no valid measured_at, skipping")
            continue

        records.append(record)

    wb.close()
    logger.info(f"[EXCEL] Parsed {len(records)} records from {Path(excel_path).name}")
    return records


# ──────────────────────────────────────────────────────────────────────────────
# EnvisoftClient
# ──────────────────────────────────────────────────────────────────────────────

class EnvisoftClient:
    """Playwright-based client that exports Envisoft Excel files per station.

    Workflow:
      1. Login via iframe → capture tenantToken from iframe src URL
      2. Navigate to "Dữ liệu trung bình theo thời gian" page
      3. For each station:
         a. Open province dropdown → select TP. Hồ Chí Minh
         b. Open station dropdown → select target station
         c. Set date range
         d. Wait for data table to load
         e. Click XUẤT FILE → capture download
      4. Parse Excel → records → return
    """

    # CSS selectors inside the iframe
    # The page uses Ant Design v5 .ant-select with .ant-select-selector clickable areas.
    # 0=Data type, 1=Province, 2=Station, 3=Data subtype, 4=Air type
    _SEL_DATA_TYPE    = ".ant-select-selector"  # nth=0: minute / hourly / raw
    _SEL_PROVINCE     = ".ant-select-selector"  # nth=1: province (TP. Hà Nội)
    _SEL_STATION      = ".ant-select-selector"  # nth=2: station dropdown
    _SEL_DATA_TYPE_2  = ".ant-select-selector"  # nth=3: data sub-type
    _SEL_AIR_TYPE     = ".ant-select-selector"  # nth=4: air type (Không khí)
    _SEL_START_DATE   = '[placeholder="Ngày bắt đầu"]'   # textbox: start date
    _SEL_END_DATE     = '[placeholder="Ngày kết thúc"]'   # textbox: end date
    _SEL_EXPORT_BTN   = "button:has-text('XUẤT FILE')"   # button: XUẤT FILE
    _SEL_TABLE        = "table"           # data table
    # Ant Design DatePicker calendar cells (always visible once picker is open)
    _SEL_CALENDAR     = ".ant-picker-panel"        # calendar panel
    _SEL_DATE_CELL    = ".ant-picker-cell"         # any date cell
    _SEL_DATE_INPUT   = ".ant-picker-input input"  # date input fields inside picker

    def __init__(self):
        self._pw = None
        self._browser = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._tenant_token: str | None = None
        self._download_count = 0

    # ──────────────────────────────────────────────────────────────────────────
    # Context manager
    # ──────────────────────────────────────────────────────────────────────────

    async def __aenter__(self) -> "EnvisoftClient":
        await self.start()
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    # ──────────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────────────────────────────────

    NAV_TIMEOUT = 120_000   # 2 minutes — container CPU can be slow
    MAX_RETRIES = 3          # retry on transient network/timeout failures

    async def start(self) -> None:
        """Launch Playwright, authenticate, navigate to data page (with retries)."""
        logger.info("[AUTH] Starting Playwright and authenticating...")
        last_error: Exception | None = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            logger.info(f"[AUTH] Attempt {attempt}/{self.MAX_RETRIES}...")
            try:
                self._pw = await async_playwright().start()
                self._browser = await self._pw.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                self._context = await self._browser.new_context(
                    http_credentials={
                        "username": config.ENVISOFT_BASIC_USER,
                        "password": config.ENVISOFT_BASIC_PASS,
                    }
                )
                self._page = await self._context.new_page()

                await self._login_via_iframe()
                await self._navigate_to_data_page()

                auth_ok = bool(self._tenant_token)
                logger.info(f"[AUTH] ✓ Authentication {'successful' if auth_ok else 'FAILED'}")
                return  # success

            except Exception as exc:
                last_error = exc
                logger.warning(f"[AUTH] Attempt {attempt} failed: {exc}")
                # Clean up partial state before retry
                if self._browser:
                    try:
                        await self._browser.close()
                    except Exception:
                        pass
                if self._pw:
                    try:
                        await self._pw.stop()
                    except Exception:
                        pass
                self._pw = None
                self._browser = None
                self._context = None
                self._page = None
                self._tenant_token = None
                if attempt < self.MAX_RETRIES:
                    wait = attempt * 5
                    logger.info(f"[AUTH] Retrying in {wait}s...")
                    await asyncio.sleep(wait)

        # All retries exhausted
        raise RuntimeError(
            f"Failed to start after {self.MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        ) from last_error

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
        logger.info("[AUTH] Browser closed")

    # ──────────────────────────────────────────────────────────────────────────
    # Authentication helpers
    # ──────────────────────────────────────────────────────────────────────────

    async def _login_via_iframe(self) -> None:
        """Complete 2-layer auth via iframe form."""
        logger.info("[AUTH] Navigating to base URL...")
        await self._page.goto(
            f"{config.ENVISOFT_BASE_URL}/",
            wait_until="domcontentloaded",
            timeout=self.NAV_TIMEOUT,
        )
        await self._page.wait_for_timeout(2000)

        frame = self._page.frame_locator("iframe")
        logger.info("[AUTH] Filling login form in iframe...")
        await frame.get_by_role("textbox", name="Tên người dùng").fill(
            config.ENVISOFT_FORM_USER
        )
        await frame.get_by_role("textbox", name="Mật khẩu").fill(
            config.ENVISOFT_FORM_PASS
        )

        logger.info("[AUTH] Clicking ĐĂNG NHẬP...")
        try:
            async with self._page.expect_navigation(timeout=self.NAV_TIMEOUT):
                await frame.get_by_role("button", name="ĐĂNG NHẬP").click()
        except Exception as exc:
            logger.warning(f"[AUTH] Navigation timeout (may have redirected): {exc}")

        await self._page.wait_for_timeout(3000)
        logger.info(f"[AUTH] URL after login: {self._page.url}")

    async def _navigate_to_data_page(self) -> None:
        """Navigate to the average-data-by-time page and wait for it to load."""
        # The data page URL includes eos_province_code=1 (Hanoi/TP) and typeTime=minute
        data_url = (
            f"{config.ENVISOFT_BASE_URL}/eos/view_log/average_data_by_time"
        )
        logger.info(f"[NAV] Navigating to {data_url}...")
        await self._page.goto(data_url, wait_until="domcontentloaded", timeout=self.NAV_TIMEOUT)
        await self._page.wait_for_timeout(3000)

        # Capture tenantToken from iframe src attribute
        iframe_el = self._page.locator("iframe")
        iframe_src = await iframe_el.get_attribute("src")
        if iframe_src:
            m = re.search(r"tenantToken=([^&\s]+)", iframe_src)
            if m:
                self._tenant_token = m.group(1)
                logger.info(f"[AUTH] tenantToken captured from iframe src: {self._tenant_token[:30]}...")

        logger.info(f"[NAV] Current URL: {self._page.url}")

    # ──────────────────────────────────────────────────────────────────────────
    # Ant Design dropdown helpers (click → wait for menu → select)
    # ──────────────────────────────────────────────────────────────────────────

    async def _open_dropdown(self, selector: str, nth: int = 0) -> None:
        """Open an Ant Design combobox dropdown."""
        frame = self._page.frame_locator("iframe")
        await frame.locator(selector).nth(nth).click()
        await self._page.wait_for_timeout(800)

    async def _select_dropdown_option_by_index(self, index: int) -> bool:
        """Select a dropdown option by its 1-based index using keyboard navigation.

        Opens the virtualized Ant Design dropdown menu, then presses Down arrow
        N-1 times followed by Enter to pick the option.
        """
        frame = self._page.frame_locator("iframe")
        try:
            # Press Down (index - 1) times to reach the target option, then Enter
            for _ in range(index - 1):
                await self._page.keyboard.press("ArrowDown")
                await self._page.wait_for_timeout(100)
            await self._page.keyboard.press("Enter")
            await self._page.wait_for_timeout(500)
            logger.info(f"[DROPDOWN] Selected option #{index}")
            return True
        except PlaywrightError as exc:
            logger.warning(f"[DROPDOWN] Failed to select index {index}: {exc}")
            return False

    async def _wait_for_table_load(self, timeout: int = 15000) -> bool:
        """Wait until the data table has rows (non-header rows)."""
        frame = self._page.frame_locator("iframe")
        try:
            await frame.locator("table tbody tr").first.wait_for(timeout=timeout)
            return True
        except PlaywrightError:
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Station export — the core workflow
    # ──────────────────────────────────────────────────────────────────────────

    async def _pre_select_province_and_data_type(self) -> None:
        """Called once before looping stations: select "theo phút" + TP. Hà Nội by index."""
        logger.info("[PAGE] Pre-selecting data type: Dữ liệu theo phút (option #1)...")
        await self._open_dropdown(self._SEL_DATA_TYPE, nth=0)
        await self._select_dropdown_option_by_index(1)  # "Dữ liệu theo phút" = option 1
        await self._page.wait_for_timeout(500)

        logger.info("[PAGE] Pre-selecting province: TP. Hà Nội (option #1)...")
        await self._open_dropdown(self._SEL_PROVINCE, nth=1)
        await self._select_dropdown_option_by_index(1)  # "TP. Hà Nội" = option 1
        await self._page.wait_for_timeout(1000)

    async def _set_ant_design_date_picker(
        self,
        picker_placeholder: str,
        date_str: str,
        frame,
    ) -> None:
        """Fill an Ant Design DatePicker by interacting with the calendar UI.

        Ant Design DatePickers use an internal onChange handler — .fill() on the
        visible input bypasses it and the picker never updates. Instead we:
          1. Click the input to open the calendar panel
          2. Click a specific date cell to confirm the selection (fires onChange)

        The date_str is YYYY-MM-DD; the calendar panel shows month+year as its
        title and day cells from the 1st to the last of that month.
        """
        from datetime import datetime

        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        year, month, day = parsed.year, parsed.month, parsed.day

        # Open the picker
        input_el = frame.locator(f'[placeholder="{picker_placeholder}"]')
        await input_el.click()
        await self._page.wait_for_timeout(800)

        # Loop until the calendar shows the target month
        for _ in range(13):  # max 12 month-change clicks
            title_el = frame.locator(".ant-picker-header")
            title_text = await title_el.inner_text()
            logger.info(f"[CALENDAR] Panel title: {title_text}")

            # Check if the calendar already shows the correct month+year
            # Ant Design header format is e.g. "Tháng 4 2026" or "April 2026"
            if str(month) in title_text and str(year) in title_text:
                logger.info(f"[CALENDAR] Month/year matches — selecting day {day}")
                break

            # Navigate to the correct month by clicking prev/next arrows
            # Try both button directions to find the right one
            next_btn = frame.locator(".ant-picker-next-icon").first
            prev_btn = frame.locator(".ant-picker-prev-icon").first

            current_month_text = title_text.lower()

            # Determine direction: if target month is ahead, click next; else prev
            # Parse current month from title
            if any(m in current_month_text for m in ["january", "february", "march",
                                                       "janvier", "febrero", "märz",
                                                       "tháng 1", "tháng 2", "tháng 3",
                                                       "1月", "jan"]):
                cur_m = 1
            elif any(m in current_month_text for m in ["april", "avril", "abril", "apr",
                                                          "tháng 4", "tháng 5", "tháng 6",
                                                          "4月", "may", "mai"]):
                cur_m = 4
            elif any(m in current_month_text for m in ["july", "juillet", "julio", "jul",
                                                         "tháng 7", "tháng 8", "tháng 9",
                                                         "7月"]):
                cur_m = 7
            elif any(m in current_month_text for m in ["october", "octobre", "oktober",
                                                           "tháng 10", "tháng 11", "tháng 12",
                                                           "10月", "11月", "12月"]):
                cur_m = 10
            else:
                # Try to parse the month number from title
                import re
                m_match = re.search(r"(\d{1,2})[/.](\d{4})", title_text)
                if m_match:
                    cur_m = int(m_match.group(1))
                else:
                    # Fallback: just try next
                    cur_m = month + 1  # force a click

            # Click next or prev depending on whether target month is ahead
            if month > cur_m:
                await next_btn.click()
            else:
                await prev_btn.click()

            await self._page.wait_for_timeout(500)
        else:
            logger.warning(f"[CALENDAR] Could not navigate to {month}/{year} in 12 clicks")

        # Click the target day cell
        # Ant Design cells show the day number as aria-label like "2026-04-13"
        target_label = f"{year}-{month:02d}-{day:02d}"
        day_cell = frame.locator(f'.ant-picker-cell[aria-label="{target_label}"]')
        if await day_cell.count() > 0:
            await day_cell.click()
            logger.info(f"[CALENDAR] Selected {target_label}")
        else:
            # Fallback: click by inner text matching the day number
            all_cells = frame.locator(".ant-picker-content td")
            for cell in all_cells.all():
                text = await cell.inner_text()
                if text.strip() == str(day):
                    await cell.click()
                    logger.info(f"[CALENDAR] Selected day {day} by text fallback")
                    break
            else:
                logger.warning(f"[CALENDAR] Day {day} cell not found — trying fill() fallback")
                await input_el.fill(date_str)

        await self._page.wait_for_timeout(500)

    async def _select_station_and_date(
        self,
        station_index: int,
        from_date: str,
        to_date: str,
    ) -> None:
        """Select station by dropdown index + set date range (province already pre-selected)."""
        frame = self._page.frame_locator("iframe")

        # 1. Open station dropdown and select by index
        logger.info(f"[PAGE] Selecting station by index {station_index}...")
        await self._open_dropdown(self._SEL_STATION, nth=2)
        await self._select_dropdown_option_by_index(station_index)
        await self._page.wait_for_timeout(1000)

        # 2. Set date range using proper calendar UI interaction
        logger.info(f"[PAGE] Setting date range: {from_date} → {to_date}...")
        await self._set_ant_design_date_picker("Ngày bắt đầu", from_date, frame)
        await self._set_ant_design_date_picker("Ngày kết thúc", to_date, frame)
        await self._page.wait_for_timeout(1000)

        # 3. Wait for data table to load
        logger.info("[PAGE] Waiting for data table to load...")
        loaded = await self._wait_for_table_load(timeout=45000)
        if loaded:
            rows = await frame.locator("table tbody tr").all()
            logger.info(f"[PAGE] Data table loaded with {len(rows)} rows")
        else:
            logger.warning("[PAGE] Data table did not load within timeout")

    async def _export_single_station(
        self,
        output_dir: Path,
    ) -> Path | None:
        """Click XUẤT FILE, wait for download, return the file path."""
        self._download_count += 1
        download_path = output_dir / f"station_export_{self._download_count}.xlsx"

        frame = self._page.frame_locator("iframe")

        async with frame.page.expect_download(timeout=60000) as dl_info:
            await frame.locator(self._SEL_EXPORT_BTN).click()
            logger.info("[EXPORT] Waiting for download...")

        download = await dl_info.value
        await download.save_as(str(download_path))
        logger.info(f"[EXPORT] Downloaded: {download_path.name}")
        return download_path

    async def export_station_data(
        self,
        station_id: str,
        station_name: str,
        station_index: int,
        from_date: str,
        to_date: str,
        output_dir: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Export 5-minute data for one station (province already pre-selected).

        Args:
            station_id: Envisoft station ID from config.
            station_name: Station display name for logging.
            station_index: 0-based index in the station dropdown.
            from_date: Start date YYYY-MM-DD.
            to_date: End date YYYY-MM-DD.
            output_dir: Directory to save the raw Excel.

        Returns:
            List of normalized data records ready for DB insertion.
        """
        if output_dir is None:
            output_dir = config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        await self._select_station_and_date(station_index, from_date, to_date)

        excel_path = await self._export_single_station(output_dir)
        if excel_path is None or not excel_path.exists():
            logger.error(f"[EXPORT] Download failed for {station_name}")
            return []

        records = parse_excel_to_records(excel_path, station_id, station_name)
        logger.info(f"[EXPORT] {station_name}: {len(records)} records parsed")
        return records

    async def export_all_stations_data(
        self,
        from_date: str,
        to_date: str,
        output_dir: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Export 5-minute data for all configured Hà Nội stations.

        Args:
            from_date: YYYY-MM-DD
            to_date: YYYY-MM-DD

        Returns:
            Combined list of records from all stations.
        """
        all_records: list[dict[str, Any]] = []
        stations = config.TARGET_STATIONS

        # ── Select province + data type ONCE before looping ─────────────────
        await self._pre_select_province_and_data_type()

        for idx, station in enumerate(stations, 1):
            station_id = station["station_id"]
            station_name = station["name"]
            station_index = idx  # 1-based index matching dropdown order

            logger.info(
                f"[{idx}/{len(stations)}] Exporting {station_name} "
                f"({station_id}) at index {station_index}, from {from_date} to {to_date}..."
            )

            try:
                records = await self.export_station_data(
                    station_id=station_id,
                    station_name=station_name,
                    station_index=station_index,
                    from_date=from_date,
                    to_date=to_date,
                    output_dir=output_dir,
                )
                all_records.extend(records)
                logger.info(f"  → {len(records)} records")
            except Exception as exc:
                logger.error(f"  → Error: {exc}", exc_info=True)
                continue

            if idx < len(stations):
                await self._page.wait_for_timeout(2000)

        logger.info(f"[DONE] Total records from all stations: {len(all_records)}")
        return all_records
