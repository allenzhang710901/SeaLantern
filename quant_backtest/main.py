from __future__ import annotations

import argparse
import logging
from pathlib import Path

from backtest import Backtester
from data_loader import load_market_bundle
from strategy import StrategyConfig


DEFAULT_START = "2020-01-01"
DEFAULT_END = "2025-03-22"
BASE_DIR = Path(__file__).resolve().parent



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="US stock moving-average trend backtest")
    parser.add_argument("--start", default=DEFAULT_START, help="Backtest start date, inclusive (YYYY-MM-DD)")
    parser.add_argument(
        "--end",
        default=DEFAULT_END,
        help="Backtest end date, exclusive for yfinance download. Use 2025-03-22 to cover 2025-03-21.",
    )
    parser.add_argument("--capital", type=float, default=100_000.0, help="Initial capital")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser



def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = BASE_DIR / output_dir

    bundle = load_market_bundle(start=args.start, end=args.end)
    backtester = Backtester(
        price_data=bundle["prices"],
        benchmark_frame=bundle["benchmark"],
        earnings_provider=bundle["earnings_provider"],
        config=StrategyConfig(),
        initial_capital=args.capital,
        output_dir=str(output_dir),
    )
    results = backtester.run()

    metrics = results["metrics"]
    print("=== Backtest Summary ===")
    print(f"Output directory: {output_dir.resolve()}")
    print(f"Total return: {metrics['total_return']:.2%}")
    print(f"Annualized return: {metrics['annualized_return']:.2%}")
    print(f"Max drawdown: {metrics['max_drawdown']:.2%}")
    print(f"Trade log CSV: {results['trades_path']}")
    print(f"Equity curve CSV: {results['equity_curve_path']}")
    print(f"Equity curve plot: {results['equity_plot_path']}")
    print(f"Representative trade plot: {results['representative_plot_path']}")
    print("NOTE: Current S&P 500 constituent backtests may suffer from survivorship bias.")


if __name__ == "__main__":
    main()
