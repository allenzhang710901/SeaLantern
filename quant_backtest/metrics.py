from __future__ import annotations

import numpy as np
import pandas as pd



def calculate_total_return(equity_curve: pd.Series) -> float:
    if equity_curve.empty:
        return 0.0
    return float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1.0)



def calculate_annualized_return(equity_curve: pd.Series) -> float:
    if equity_curve.empty or len(equity_curve) < 2:
        return 0.0
    start = equity_curve.index[0]
    end = equity_curve.index[-1]
    years = max((end - start).days / 365.25, 1 / 365.25)
    cumulative = equity_curve.iloc[-1] / equity_curve.iloc[0]
    return float(cumulative ** (1 / years) - 1.0)



def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    if equity_curve.empty:
        return 0.0
    values = equity_curve.to_numpy(dtype=float)
    running_max = np.maximum.accumulate(values)
    drawdown = values / running_max - 1.0
    return float(drawdown.min())



def summarize_metrics(equity_curve: pd.Series) -> dict:
    return {
        "total_return": calculate_total_return(equity_curve),
        "annualized_return": calculate_annualized_return(equity_curve),
        "max_drawdown": calculate_max_drawdown(equity_curve),
    }
