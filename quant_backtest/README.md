# 美股均线趋势策略回测项目

这是一个使用 **Python + pandas / numpy / matplotlib / yfinance** 实现的可运行美股量化回测项目，目标是回测“均线趋势策略”，并输出：

- 总收益率
- 年化收益率
- 最大回撤
- 交易记录 CSV
- 账户净值曲线图
- 代表性股票买卖点示意图

> **重要提示：当前使用“当前时点的 S&P 500 成分股列表”回测历史区间，存在明显幸存者偏差（survivorship bias）。**

## 项目结构

```text
quant_backtest/
├── backtest.py         # 回测主循环、订单撮合、结果输出
├── data_loader.py      # 标普500列表获取、行情下载、财报接口
├── main.py             # 命令行入口
├── metrics.py          # 收益/回撤指标计算
├── README.md           # 运行说明
├── requirements.txt    # Python 依赖
└── strategy.py         # 均线趋势策略与信号筛选
```

## 策略说明

### 市场与数据
- 交易市场：美股
- 股票池：当前标普 500 成分股
- 基准过滤：SPY
- K 线周期：日线
- 默认回测区间：`2020-01-01` 到 `2025-03-21`

### 买入条件
1. 个股 `MA5` 上穿 `MA20`
2. `SPY` 收盘价高于其 `MA20`
3. 当日成交量高于 `20` 日平均成交量
4. 财报日前后 `3` 个交易日不允许开仓
5. 若同日候选超过可买名额，则按 `MA5 / MA20 - 1` 偏离度从高到低排序

### 卖出条件
1. 个股 `MA5` 下穿 `MA20`
2. 单笔亏损达到 `7%` 止损
3. 单笔盈利达到 `20%` 止盈

### 仓位与成本
- 最多持有 `5` 只股票
- 单只股票最大仓位 `20%`
- 手续费：`0.1%`
- 滑点：`0.05%`

## 实现细节

### 1. 避免未来函数
- 均线、成交量、SPY 趋势过滤全部基于 **当日收盘后** 的已知信息计算信号。
- 所有由收盘信号触发的交易都在 **下一交易日开盘** 执行。
- 止损/止盈使用日线的 `high/low` 做触发判断；这是日线级别回测中的近似处理。

### 2. 财报日期接口可替换
`data_loader.py` 中定义了 `EarningsCalendarProvider` 接口，并提供了 `YFinanceEarningsCalendarProvider` 作为默认实现。

由于 **yfinance 的财报日期接口并不总是稳定**，代码里做了如下处理：
- 优先尝试从 yfinance 拉取财报日期
- 将财报日期缓存到本地 `quant_backtest/cache/earnings/`
- 若某只股票无法获得财报日期，则记录 warning，并默认 **不启用该股票的财报黑名单限制**

如果你后续有更稳定的数据源（如 Polygon、Finnhub、WRDS、自建数据库），只需替换该 provider 即可。

### 3. 容错处理
代码已对以下情况做容错：
- 行情缺失
- 停牌或某日无交易数据
- 财报日期缺失
- 某些股票历史长度不足，自动跳过
- 下载结果为空时抛出明确异常

## 安装依赖

建议使用虚拟环境：

```bash
cd quant_backtest
python -m venv .venv
source .venv/bin/activate   # Windows 可改为 .venv\Scripts\activate
pip install -r requirements.txt
```

## 运行方式

### 默认运行

```bash
cd quant_backtest
python main.py
```

默认参数：
- 开始日期：`2020-01-01`
- 结束日期：`2025-03-22`
  - 注意：yfinance 的 `end` 参数通常是**右开区间**，所以这里使用 `2025-03-22` 来覆盖到 `2025-03-21`
- 初始资金：`100000`
- 输出目录：项目目录下的 `output/`

### 自定义参数

```bash
cd quant_backtest
python main.py --start 2020-01-01 --end 2025-03-22 --capital 100000 --output-dir output
```

## 输出文件

运行完成后会生成：

- `trade_log.csv`：交易记录
- `equity_curve.csv`：每日净值曲线数据
- `equity_curve.png`：账户净值曲线图
- `representative_trade.png`：代表性个股买卖点示意图

## 关键说明

1. **幸存者偏差**：当前成分股列表回测历史数据，会高估策略表现。
2. **执行价格近似**：收盘信号次日开盘执行；止盈止损使用日线高低价触发，属于常见简化。
3. **数据依赖外网**：首次运行需要联网下载 yfinance 行情和 Wikipedia 成分股列表。
4. **财报数据质量**：若 yfinance 财报接口不可用，策略会继续运行，但财报过滤会变弱。

## 可扩展方向

- 将股票池改成“按历史日期还原的 S&P 500 成分股”
- 增加更真实的调仓规则（如最小交易单位、现金缓冲）
- 引入更稳定的财报日历与企业行为数据
- 增加多进程下载与本地行情缓存
- 输出更多指标：Sharpe、Sortino、胜率、盈亏比等
