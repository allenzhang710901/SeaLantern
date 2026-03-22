from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd
import yfinance as yf

LOGGER = logging.getLogger(__name__)
WIKIPEDIA_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
BASE_DIR = Path(__file__).resolve().parent


class EarningsCalendarProvider:
    """Replaceable earnings-calendar interface.

    Notes:
        yfinance's earnings endpoints are not always stable enough for a full
        S&P 500 historical backtest. This interface is intentionally separated
        so it can be swapped for Polygon, Finnhub, Alpha Vantage, WRDS, etc.
    """

    def get_earnings_dates(
        self,
        symbol: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> pd.DatetimeIndex:
        return pd.DatetimeIndex([])


@dataclass
class YFinanceEarningsCalendarProvider(EarningsCalendarProvider):
    """Best-effort earnings-date provider with local caching."""

    cache_dir: Path = BASE_DIR / "cache" / "earnings"
    _memory_cache: Dict[str, pd.DatetimeIndex] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_earnings_dates(
        self,
        symbol: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> pd.DatetimeIndex:
        if symbol not in self._memory_cache:
            self._memory_cache[symbol] = self._load_symbol(symbol)

        dates = self._memory_cache[symbol]
        if dates.empty:
            return dates
        mask = (dates >= start.normalize()) & (dates <= end.normalize())
        return dates[mask]

    def _load_symbol(self, symbol: str) -> pd.DatetimeIndex:
        cache_path = self.cache_dir / f"{symbol}.csv"
        if cache_path.exists():
            try:
                cached = pd.read_csv(cache_path)
                dates = pd.to_datetime(cached["earnings_date"], utc=False).tz_localize(None)
                return pd.DatetimeIndex(sorted(pd.Series(dates).dropna().unique()))
            except Exception as exc:  # pragma: no cover - defensive cache handling
                LOGGER.warning("Failed to read earnings cache for %s: %s", symbol, exc)

        dates_index = pd.DatetimeIndex([])
        try:
            ticker = yf.Ticker(symbol)
            earnings = ticker.get_earnings_dates(limit=24)
            if earnings is not None and not earnings.empty:
                raw_index = pd.to_datetime(earnings.index, utc=False)
                if getattr(raw_index, "tz", None) is not None:
                    raw_index = raw_index.tz_localize(None)
                dates_index = pd.DatetimeIndex(sorted(pd.Series(raw_index).normalize().dropna().unique()))
        except Exception as exc:
            LOGGER.warning(
                "Unable to fetch earnings dates for %s from yfinance. "
                "The backtest will allow entries when dates are unavailable. Error: %s",
                symbol,
                exc,
            )

        if not dates_index.empty:
            pd.DataFrame({"earnings_date": dates_index.strftime("%Y-%m-%d")}).to_csv(cache_path, index=False)
        return dates_index


def get_current_sp500_symbols() -> List[str]:
    """Fetch the current S&P 500 constituents.

    Warning:
        Using the *current* constituent list for a historical backtest introduces
        survivorship bias. This is explicitly left visible because the user asked
        for an S&P 500 universe and a current constituent fetch function.
    """

    tables = pd.read_html(WIKIPEDIA_SP500_URL)
    constituents = tables[0]
    symbols = constituents["Symbol"].astype(str).str.replace(".", "-", regex=False).tolist()
    return sorted(dict.fromkeys(symbols))



def _normalize_download_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame

    frame = frame.rename(columns=str.lower)
    expected = ["open", "high", "low", "close", "volume"]
    available = [column for column in expected if column in frame.columns]
    normalized = frame[available].copy()
    normalized.index = pd.to_datetime(normalized.index).tz_localize(None)
    normalized = normalized.sort_index()
    normalized = normalized[~normalized.index.duplicated(keep="last")]
    return normalized



def download_ohlcv_data(
    symbols: Iterable[str],
    start: str,
    end: str,
    auto_adjust: bool = True,
) -> Dict[str, pd.DataFrame]:
    data: Dict[str, pd.DataFrame] = {}
    tickers = list(dict.fromkeys(symbols))
    if not tickers:
        return data

    raw = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=auto_adjust,
        progress=False,
        group_by="ticker",
        threads=True,
    )

    if raw.empty:
        return data

    if isinstance(raw.columns, pd.MultiIndex):
        for symbol in tickers:
            if symbol not in raw.columns.get_level_values(0):
                continue
            symbol_frame = raw[symbol].dropna(how="all")
            normalized = _normalize_download_frame(symbol_frame)
            if normalized.empty:
                continue
            data[symbol] = normalized
    else:
        symbol = tickers[0]
        normalized = _normalize_download_frame(raw.dropna(how="all"))
        if not normalized.empty:
            data[symbol] = normalized

    return data



def load_market_bundle(
    start: str,
    end: str,
    benchmark_symbol: str = "SPY",
    earnings_provider: EarningsCalendarProvider | None = None,
) -> dict:
    universe = get_current_sp500_symbols()
    all_symbols = [*universe, benchmark_symbol]
    LOGGER.info("Downloading %s symbols from yfinance. This may take a while.", len(all_symbols))
    price_data = download_ohlcv_data(all_symbols, start=start, end=end)

    benchmark = price_data.pop(benchmark_symbol, pd.DataFrame())
    if benchmark.empty:
        raise RuntimeError(f"Unable to download benchmark data for {benchmark_symbol}.")

    cleaned_prices = {
        symbol: frame
        for symbol, frame in price_data.items()
        if not frame.empty and {"open", "high", "low", "close", "volume"}.issubset(frame.columns)
    }

    LOGGER.info("Downloaded %s stock histories and benchmark %s.", len(cleaned_prices), benchmark_symbol)
    return {
        "universe": universe,
        "prices": cleaned_prices,
        "benchmark": benchmark,
        "benchmark_symbol": benchmark_symbol,
        "earnings_provider": earnings_provider or YFinanceEarningsCalendarProvider(),
    }
