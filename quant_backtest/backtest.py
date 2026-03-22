from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd

from metrics import summarize_metrics
from strategy import StrategyConfig, add_indicators, prepare_universe, rank_entry_candidates

LOGGER = logging.getLogger(__name__)


@dataclass
class Position:
    symbol: str
    shares: int
    entry_date: pd.Timestamp
    entry_price: float
    signal_date: pd.Timestamp


class Backtester:
    def __init__(
        self,
        price_data: Dict[str, pd.DataFrame],
        benchmark_frame: pd.DataFrame,
        earnings_provider,
        config: StrategyConfig,
        initial_capital: float = 100_000.0,
        output_dir: str = "output",
    ) -> None:
        self.config = config
        self.initial_capital = initial_capital
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.prepared_prices = prepare_universe(price_data)
        self.benchmark = add_indicators(benchmark_frame)
        self.earnings_provider = earnings_provider

        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.pending_buys: Dict[pd.Timestamp, List[dict]] = defaultdict(list)
        self.pending_sells: Dict[pd.Timestamp, List[dict]] = defaultdict(list)
        self.trades: List[dict] = []
        self.equity_records: List[dict] = []

        all_dates = set(self.benchmark.index)
        for frame in self.prepared_prices.values():
            all_dates.update(frame.index)
        self.calendar = sorted(all_dates)

    def run(self) -> dict:
        LOGGER.info("Starting backtest over %s trading days.", len(self.calendar))
        for idx, trade_date in enumerate(self.calendar):
            next_trade_date = self.calendar[idx + 1] if idx + 1 < len(self.calendar) else None
            self._execute_open_orders(trade_date)
            self._check_intraday_risk_exits(trade_date)
            self._record_equity(trade_date)
            if next_trade_date is not None:
                self._schedule_close_based_orders(trade_date, next_trade_date)

        equity_curve = pd.DataFrame(self.equity_records).set_index("date")["equity"]
        metrics = summarize_metrics(equity_curve)

        trades_df = pd.DataFrame(self.trades)
        equity_df = equity_curve.rename("equity").to_frame()
        trades_path = self.output_dir / "trade_log.csv"
        equity_path = self.output_dir / "equity_curve.csv"
        trades_df.to_csv(trades_path, index=False)
        equity_df.to_csv(equity_path)

        equity_plot_path = self.output_dir / "equity_curve.png"
        representative_plot_path = self.output_dir / "representative_trade.png"
        self._plot_equity_curve(equity_curve, equity_plot_path)
        self._plot_representative_trade(representative_plot_path)

        return {
            "metrics": metrics,
            "trades_path": trades_path,
            "equity_curve_path": equity_path,
            "equity_plot_path": equity_plot_path,
            "representative_plot_path": representative_plot_path,
            "equity_curve": equity_curve,
            "trades": trades_df,
        }

    def _execute_open_orders(self, trade_date: pd.Timestamp) -> None:
        sell_orders = self.pending_sells.pop(trade_date, [])
        for order in sell_orders:
            symbol = order["symbol"]
            if symbol not in self.positions:
                continue
            frame = self.prepared_prices.get(symbol)
            if frame is None or trade_date not in frame.index:
                continue
            open_price = float(frame.loc[trade_date, "open"])
            execution_price = open_price * (1 - self.config.slippage_rate)
            self._close_position(symbol, trade_date, execution_price, order["reason"])

        buy_orders = self.pending_buys.pop(trade_date, [])
        if not buy_orders:
            return

        available_slots = max(self.config.max_positions - len(self.positions), 0)
        orders_to_fill = buy_orders[:available_slots]
        for order in orders_to_fill:
            symbol = order["symbol"]
            frame = self.prepared_prices.get(symbol)
            if frame is None or trade_date not in frame.index or symbol in self.positions:
                continue
            open_price = float(frame.loc[trade_date, "open"])
            if pd.isna(open_price) or open_price <= 0:
                continue

            equity_before_fill = self._portfolio_value(trade_date)
            target_value = min(
                equity_before_fill * self.config.max_position_weight,
                self.cash,
            )
            if target_value <= 0:
                continue

            execution_price = open_price * (1 + self.config.slippage_rate)
            per_share_cost = execution_price * (1 + self.config.commission_rate)
            shares = int(target_value // per_share_cost)
            if shares <= 0:
                continue

            total_cost = shares * per_share_cost
            self.cash -= total_cost
            self.positions[symbol] = Position(
                symbol=symbol,
                shares=shares,
                entry_date=trade_date,
                entry_price=execution_price,
                signal_date=order["signal_date"],
            )
            self.trades.append(
                {
                    "symbol": symbol,
                    "side": "BUY",
                    "signal_date": order["signal_date"].strftime("%Y-%m-%d"),
                    "trade_date": trade_date.strftime("%Y-%m-%d"),
                    "price": round(execution_price, 4),
                    "shares": shares,
                    "gross_amount": round(shares * execution_price, 2),
                    "net_amount": round(total_cost, 2),
                    "reason": "ma_cross_up",
                }
            )

    def _check_intraday_risk_exits(self, trade_date: pd.Timestamp) -> None:
        symbols = list(self.positions.keys())
        for symbol in symbols:
            position = self.positions.get(symbol)
            frame = self.prepared_prices.get(symbol)
            if position is None or frame is None or trade_date not in frame.index:
                continue
            if trade_date <= position.entry_date:
                continue

            bar = frame.loc[trade_date]
            stop_price = position.entry_price * (1 - self.config.stop_loss_pct)
            take_price = position.entry_price * (1 + self.config.take_profit_pct)
            if float(bar["low"]) <= stop_price:
                execution_price = stop_price * (1 - self.config.slippage_rate)
                self._close_position(symbol, trade_date, execution_price, "stop_loss")
                continue
            if float(bar["high"]) >= take_price:
                execution_price = take_price * (1 - self.config.slippage_rate)
                self._close_position(symbol, trade_date, execution_price, "take_profit")

    def _schedule_close_based_orders(self, trade_date: pd.Timestamp, next_trade_date: pd.Timestamp) -> None:
        exiting_symbols: set[str] = set()
        for symbol, position in list(self.positions.items()):
            frame = self.prepared_prices.get(symbol)
            if frame is None or trade_date not in frame.index:
                continue
            row = frame.loc[trade_date]
            if bool(row.get("cross_down", False)):
                self.pending_sells[next_trade_date].append(
                    {
                        "symbol": symbol,
                        "signal_date": trade_date,
                        "reason": "ma_cross_down",
                    }
                )
                exiting_symbols.add(symbol)

        held_symbols = set(self.positions.keys())
        expected_holdings = len(held_symbols - exiting_symbols)
        available_slots = max(self.config.max_positions - expected_holdings, 0)
        if available_slots <= 0:
            return

        candidates = rank_entry_candidates(
            trade_date=trade_date,
            prepared_prices=self.prepared_prices,
            benchmark_frame=self.benchmark,
            held_symbols=held_symbols,
            exiting_symbols=exiting_symbols,
            earnings_provider=self.earnings_provider,
            config=self.config,
        )
        for candidate in candidates[:available_slots]:
            self.pending_buys[next_trade_date].append(candidate)

    def _close_position(self, symbol: str, trade_date: pd.Timestamp, execution_price: float, reason: str) -> None:
        position = self.positions.pop(symbol, None)
        if position is None:
            return

        net_proceeds = position.shares * execution_price * (1 - self.config.commission_rate)
        gross_proceeds = position.shares * execution_price
        self.cash += net_proceeds
        pnl_pct = execution_price / position.entry_price - 1.0

        self.trades.append(
            {
                "symbol": symbol,
                "side": "SELL",
                "signal_date": position.signal_date.strftime("%Y-%m-%d"),
                "trade_date": trade_date.strftime("%Y-%m-%d"),
                "price": round(execution_price, 4),
                "shares": position.shares,
                "gross_amount": round(gross_proceeds, 2),
                "net_amount": round(net_proceeds, 2),
                "reason": reason,
                "pnl_pct": round(pnl_pct, 4),
                "holding_days": int((trade_date - position.entry_date).days),
            }
        )

    def _portfolio_value(self, trade_date: pd.Timestamp) -> float:
        total = self.cash
        for symbol, position in self.positions.items():
            frame = self.prepared_prices.get(symbol)
            if frame is None or trade_date not in frame.index:
                continue
            total += position.shares * float(frame.loc[trade_date, "close"])
        return total

    def _record_equity(self, trade_date: pd.Timestamp) -> None:
        equity = self._portfolio_value(trade_date)
        self.equity_records.append({"date": trade_date, "equity": equity, "cash": self.cash})

    def _plot_equity_curve(self, equity_curve: pd.Series, output_path: Path) -> None:
        plt.figure(figsize=(12, 6))
        plt.plot(equity_curve.index, equity_curve.values, label="Equity")
        plt.title("Moving Average Trend Strategy Equity Curve")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value")
        plt.grid(alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

    def _plot_representative_trade(self, output_path: Path) -> None:
        buy_trades = [trade for trade in self.trades if trade.get("side") == "BUY"]
        if not buy_trades:
            LOGGER.warning("No buy trades were generated; creating a placeholder representative plot.")
            plt.figure(figsize=(10, 4))
            plt.text(0.5, 0.5, "No buy/sell trades generated in this backtest window.", ha="center", va="center")
            plt.axis("off")
            plt.tight_layout()
            plt.savefig(output_path, dpi=150)
            plt.close()
            return

        representative_symbol = buy_trades[0]["symbol"]
        frame = self.prepared_prices[representative_symbol].copy()
        frame = frame.reset_index().rename(columns={"index": "date"})
        symbol_trades = [trade for trade in self.trades if trade.get("symbol") == representative_symbol]
        trade_df = pd.DataFrame(symbol_trades)
        if not trade_df.empty:
            trade_df["trade_date"] = pd.to_datetime(trade_df["trade_date"])

        plt.figure(figsize=(14, 7))
        plt.plot(frame["date"], frame["close"], label="Close", alpha=0.9)
        plt.plot(frame["date"], frame["ma_short"], label="MA5", alpha=0.8)
        plt.plot(frame["date"], frame["ma_long"], label="MA20", alpha=0.8)

        if not trade_df.empty:
            buys = trade_df[trade_df["side"] == "BUY"]
            sells = trade_df[trade_df["side"] == "SELL"]
            plt.scatter(buys["trade_date"], buys["price"], marker="^", color="green", s=90, label="Buy")
            plt.scatter(sells["trade_date"], sells["price"], marker="v", color="red", s=90, label="Sell")

        plt.title(f"Representative Buy/Sell Points: {representative_symbol}")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.grid(alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
