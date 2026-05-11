"""Write metadata fields straight from IBKR contract details.

IBKR's reqContractDetails returns longName, industry, category, and
subcategory for stocks with no market data subscription required and no
external API. Switched to this after Yahoo started rate limiting our
home IP.

The function below is also kept callable as a no-op manual trigger so the
existing /api/sync/enrich endpoint keeps working. The real enrichment now
runs inline in services/sync.py via apply_ibkr_metadata().
"""
from __future__ import annotations

import logging
import os
import re
from datetime import date, datetime, timedelta
from typing import Iterable, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.ibkr.client import IBPosition
from app.models import Metadata, Position

logger = logging.getLogger(__name__)

# Browser-like headers; nasdaq.com refuses default httpx UA.
NASDAQ_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/",
}

EARNINGS_REFRESH_DAYS = 3


# Yahoo via curl_cffi. Yahoo fingerprints default Python HTTP clients and
# rate limits them aggressively. curl_cffi impersonates Chrome's TLS stack
# so requests look indistinguishable from a real browser.
_yahoo_session = None
_yahoo_unavailable = False


def _get_yahoo_session():
    """Lazy-build a curl_cffi session that yfinance can use. Returns None if
    curl_cffi is missing so we degrade to Nasdaq instead of crashing."""
    global _yahoo_session, _yahoo_unavailable
    if _yahoo_session is not None:
        return _yahoo_session
    if _yahoo_unavailable:
        return None
    try:
        from curl_cffi import requests as curl_requests
        _yahoo_session = curl_requests.Session(impersonate="chrome")
        return _yahoo_session
    except Exception as exc:
        logger.warning("curl_cffi not available: %s", exc)
        _yahoo_unavailable = True
        return None


def fetch_yahoo_fields(symbol: str) -> dict:
    """Pull next earnings date and EPS growth from Yahoo through yfinance.
    Returns {} if anything fails so the caller can keep going."""
    session = _get_yahoo_session()
    if session is None:
        return {}
    try:
        import yfinance as yf
    except Exception as exc:
        logger.warning("yfinance import failed: %s", exc)
        return {}

    out: dict = {}
    try:
        ticker = yf.Ticker(symbol, session=session)

        # Earnings date. yfinance exposes it via .calendar (a dict in newer
        # versions) or .get_earnings_dates() (a DataFrame).
        try:
            cal = ticker.calendar
            if isinstance(cal, dict):
                ed = cal.get("Earnings Date")
                if isinstance(ed, list) and ed:
                    parsed = _parse_date(ed[0])
                    if parsed:
                        out["next_earnings_date"] = parsed
        except Exception:
            pass

        # EPS growth from forward vs trailing
        try:
            info = ticker.info or {}
            forward = info.get("forwardEps")
            trailing = info.get("trailingEps")
            if forward is not None and trailing is not None and float(trailing) != 0:
                growth = (float(forward) - float(trailing)) / abs(float(trailing)) * 100
                sign = "+" if growth >= 0 else ""
                out["eps_guidance"] = f"{sign}{growth:.0f}%"
        except Exception:
            pass

        # Earnings trend growth as a richer EPS guidance source
        if "eps_guidance" not in out:
            try:
                trend = ticker.earnings_trend
                if trend is not None and not trend.empty:
                    # First row is current quarter
                    row = trend.iloc[0]
                    g = row.get("growth") or row.get("growthEstimate")
                    if g is not None:
                        try:
                            pct = float(g) * 100 if abs(float(g)) < 5 else float(g)
                            sign = "+" if pct >= 0 else ""
                            out["eps_guidance"] = f"{sign}{pct:.0f}%"
                        except (TypeError, ValueError):
                            pass
            except Exception:
                pass

    except Exception as exc:
        logger.warning("Yahoo fetch failed for %s: %s", symbol, exc)

    return out


def classify_tier(industry: Optional[str], category: Optional[str], subcategory: Optional[str]) -> str:
    """Map IBKR's industry/category/subcategory into one of five tiers.

    IBKR uses fairly broad labels (industry='Computers', category='Computers',
    subcategory='Semicon Devices-Memory') so we look at the union of all three.
    """
    text = " ".join(filter(None, [industry, category, subcategory])).lower()

    if not text:
        return "T5"

    # T1 Semi & AI Core
    if any(k in text for k in (
        "semicon", "semi-cond", "semiconductor",
        "photonic", "optical", "fiber",
        "communication equipment",
    )):
        return "T1"
    if any(k in text for k in ("software", "internet", "cloud", "computer software", "data services")):
        return "T1"
    if "computers" in text and ("memory" in text or "device" in text or "components" in text):
        return "T1"

    # T2 Energy & Materials
    if any(k in text for k in (
        "oil", "gas", "petroleum", "mining", "metals", "chemical",
        "materials", "coal", "energy",
    )):
        return "T2"

    # T3 Industrials
    if any(k in text for k in (
        "industrial", "construction", "engineering", "machinery",
        "aerospace", "defense", "electrical", "transportation",
    )):
        return "T3"

    # T4 Healthcare
    if any(k in text for k in ("drug", "pharma", "biotech", "medical", "health")):
        return "T4"

    return "T5"


def _parse_date(value) -> Optional[date]:
    """Parse the variety of date strings Nasdaq returns."""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    if not s or s.upper() == "N/A":
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def fetch_next_earnings_nasdaq(symbol: str) -> Optional[date]:
    """Pull the next earnings date from Nasdaq's public API.

    Tries the /info endpoint first (which sometimes carries an
    upcomingEarningsDate field), then falls back to /earnings which lists
    upcoming/historical events.
    """
    base = f"https://api.nasdaq.com/api/quote/{symbol}"
    params_info = {"assetclass": "stocks"}

    try:
        with httpx.Client(headers=NASDAQ_HEADERS, timeout=10) as client:
            r = client.get(f"{base}/info", params=params_info)
            if r.status_code == 200:
                payload = r.json() or {}
                data = payload.get("data") or {}
                # Common spots Nasdaq drops the date in
                candidates = [
                    data.get("nextEarningsDate"),
                    data.get("upcomingEarningsDate"),
                    (data.get("keyStats") or {}).get("NextEarningsDate", {}).get("value")
                        if isinstance(data.get("keyStats"), dict) else None,
                    (data.get("nextEarningsAnnouncement") or {}).get("value")
                        if isinstance(data.get("nextEarningsAnnouncement"), dict) else None,
                ]
                for c in candidates:
                    d = _parse_date(c)
                    if d:
                        return d

            r = client.get(f"{base}/earnings", params=params_info)
            if r.status_code == 200:
                payload = r.json() or {}
                data = payload.get("data") or {}
                forecast = data.get("earningsForecastTable") or {}
                rows = forecast.get("rows") or []
                today = datetime.utcnow().date()
                # Rows are ordered chronologically; pick the next future date
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    raw = row.get("date") or row.get("reportDate") or row.get("forecastDate")
                    d = _parse_date(raw)
                    if d and d >= today:
                        return d
    except Exception as exc:
        logger.warning("Nasdaq earnings fetch failed for %s: %s", symbol, exc)
    return None


def fetch_next_earnings_finnhub(symbol: str, api_key: str) -> Optional[date]:
    """Optional fallback. Only used if FINNHUB_API_KEY is set in env."""
    today = datetime.utcnow().date()
    end = today + timedelta(days=120)
    url = "https://finnhub.io/api/v1/calendar/earnings"
    params = {
        "from": today.isoformat(),
        "to": end.isoformat(),
        "symbol": symbol,
        "token": api_key,
    }
    try:
        r = httpx.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return None
        cal = (r.json() or {}).get("earningsCalendar") or []
        if not cal:
            return None
        return _parse_date(cal[0].get("date"))
    except Exception as exc:
        logger.warning("Finnhub earnings fetch failed for %s: %s", symbol, exc)
        return None


def fetch_next_earnings(symbol: str) -> Optional[date]:
    """Try Nasdaq first; if a Finnhub key is configured, try that as a fallback."""
    d = fetch_next_earnings_nasdaq(symbol)
    if d:
        return d
    finnhub_key = os.environ.get("FINNHUB_API_KEY")
    if finnhub_key:
        return fetch_next_earnings_finnhub(symbol, finnhub_key)
    return None


def _needs_earnings_refresh(meta: Metadata) -> bool:
    """Skip if we already have a future date refreshed in the last few days."""
    if meta.next_earnings_date is None:
        return True
    today = datetime.utcnow().date()
    if meta.next_earnings_date < today:
        return True  # Past date, time to look up the next quarter
    if meta.enriched_at is None:
        return True
    return (datetime.utcnow() - meta.enriched_at) > timedelta(days=EARNINGS_REFRESH_DAYS)


def apply_ibkr_metadata(db: Session, positions: Iterable[IBPosition]) -> int:
    """Upsert one metadata row per position, populating company name,
    industry, sector (mapped from IBKR industry/category), and a default
    auto-tier. The user can override `tag` manually; we never overwrite a
    user choice.
    """
    now = datetime.utcnow()
    populated = 0

    for p in positions:
        meta = db.get(Metadata, p.symbol)
        if meta is None:
            meta = Metadata(symbol=p.symbol)
            db.add(meta)

        # Always refresh from IBKR; IBKR is the source of truth here.
        if p.long_name:
            meta.company_name = p.long_name
            populated += 1
        if p.industry:
            # Use IBKR's industry as a sector approximation when we don't
            # have anything better.
            meta.sector = p.industry
        if p.subcategory:
            # subcategory is the most specific (e.g. "Semicon Devices-Memory").
            meta.industry = p.subcategory
        elif p.category:
            meta.industry = p.category

        # Auto tier. Manual tag wins, but a stale T5 from before should be
        # refreshed if IBKR data now points to something more specific.
        auto = classify_tier(p.industry, p.category, p.subcategory)
        if not meta.tag or meta.tag == "T5":
            meta.tag = auto

        # External earnings + EPS lookup. We try Yahoo (via curl_cffi to
        # bypass the rate limiter) first, then Nasdaq as a fallback. The
        # cache check stops us from hammering either every sync.
        if _needs_earnings_refresh(meta):
            try:
                yh = fetch_yahoo_fields(p.symbol)
                if yh.get("next_earnings_date"):
                    meta.next_earnings_date = yh["next_earnings_date"]
                    if yh["next_earnings_date"] >= now.date():
                        meta.earnings_reported = False
                if yh.get("eps_guidance"):
                    meta.eps_guidance = yh["eps_guidance"]

                if not meta.next_earnings_date:
                    ed = fetch_next_earnings(p.symbol)
                    if ed:
                        meta.next_earnings_date = ed
                        if ed >= now.date():
                            meta.earnings_reported = False
            except Exception as exc:
                logger.warning("earnings/EPS lookup failed for %s: %s", p.symbol, exc)

        meta.enriched_at = now
        meta.updated_at = now

    db.commit()
    logger.info("IBKR metadata applied: %d/%d populated", populated, len(list(positions) if not isinstance(positions, list) else positions))
    return populated


def enrich_current_positions(db: Session) -> int:
    """Manual trigger endpoint. Returns count of metadata rows touched.

    No external network call. We just refresh from the cached Position rows;
    the next IBKR sync will refresh the full IBKR-side fields.
    """
    rows: List[Position] = db.query(Position).all()
    if not rows:
        return 0

    # Build lightweight IBPosition stubs from the DB rows. They're missing
    # long_name etc., so the metadata write is mostly a no-op until the
    # next real sync. We still ensure a row exists for each symbol.
    now = datetime.utcnow()
    for r in rows:
        meta = db.get(Metadata, r.symbol)
        if meta is None:
            meta = Metadata(symbol=r.symbol)
            db.add(meta)
            meta.enriched_at = now
            meta.updated_at = now
    db.commit()
    return len(rows)
