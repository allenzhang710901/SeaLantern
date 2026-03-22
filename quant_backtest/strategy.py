from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from data_loader import EarningsCalendarProvider

LOGGER = logging.getLogger(__name__)


@dataclass
class StrategyConfig:
    short_window: int = 5
    long_window: int = 20
    volume_window: int = 20
    stop_loss_pct: float = 0.07
    take_profit_pct: float = 0.20
    max_positions: int = 5
    max_position_weight: float = 0.20
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005
    earnings_blackout_days: int = 3



def add_indicators(price_frame: pd.DataFrame) -> pd.DataFrame:
    enriched = price_frame.copy()
    enriched["ma_short"] = enriched["close"].rolling(5, min_periods=5).mean()
    enriched["ma_long"] = enriched["close"].rolling(20, min_periods=20).mean()
    enriched["volume_ma"] = enriched["volume"].rolling(20, min_periods=20).mean()
    enriched["cross_up"] = (
        (enriched["ma_short"] > enriched["ma_long"])
        & (enriched["ma_short"].shift(1) <= enriched["ma_long"].shift(1))
    )
    enriched["cross_down"] = (
        (enriched["ma_short"] < enriched["ma_long"])
        & (enriched["ma_short"].shift(1) >= enriched["ma_long"].shift(1))
    )
    enriched["deviation"] = (enriched["ma_short"] / enriched["ma_long"]) - 1.0
    return enriched



def prepare_universe(price_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    prepared: Dict[str, pd.DataFrame] = {}
    for symbol, frame in price_data.items():
        if len(frame) < 25:
            LOGGER.warning("Skipping %s because it does not have enough daily bars.", symbol)
            continue
        prepared[symbol] = add_indicators(frame)
    return prepared



def benchmark_allows_entry(benchmark_frame: pd.DataFrame, trade_date: pd.Timestamp) -> bool:
    if trade_date not in benchmark_frame.index:
        return False
    row = benchmark_frame.loc[trade_date]
    if pd.isna(row.get("ma_long")):
        return False
    return bool(row["close"] > row["ma_long"])



def is_in_earnings_blackout(
    symbol: str,
    trade_date: pd.Timestamp,
    earnings_provider: EarningsCalendarProvider,
    config: StrategyConfig,
) -> bool:
    window_start = trade_date - pd.offsets.BDay(config.earnings_blackout_days)
    window_end = trade_date + pd.offsets.BDay(config.earnings_blackout_days)
    earnings_dates = earnings_provider.get_earnings_dates(symbol, window_start, window_end)
    return not earnings_dates.empty



def rank_entry_candidates(
    trade_date: pd.Timestamp,
    prepared_prices: Dict[str, pd.DataFrame],
    benchmark_frame: pd.DataFrame,
    held_symbols: set[str],
    exiting_symbols: set[str],
    earnings_provider: EarningsCalendarProvider,
    config: StrategyConfig,
) -> List[dict]:
    if not benchmark_allows_entry(benchmark_frame, trade_date):
        return []

    candidates: List[dict] = []
    for symbol, frame in prepared_prices.items():
        if symbol in held_symbols or symbol in exiting_symbols:
            continue
        if trade_date not in frame.index:
            continue

        row = frame.loc[trade_date]
        if pd.isna(row.get("ma_long")) or pd.isna(row.get("volume_ma")):
            continue
        if not bool(row.get("cross_up", False)):
            continue
        if not bool(row["volume"] > row["volume_ma"]):
            continue
        if is_in_earnings_blackout(symbol, trade_date, earnings_provider, config):
            continue

        candidates.append(
            {
                "symbol": symbol,
                "signal_date": trade_date,
                "deviation": float(row.get("deviation", 0.0)),
                "close": float(row["close"]),
            }
        )

    candidates.sort(key=lambda item: item["deviation"], reverse=True)
    return candidates
