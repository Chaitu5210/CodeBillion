import csv
import os
from typing import TypedDict, Optional, Dict
from collections import defaultdict

import pandas as pd

from StrategyTestBed import strategy_logic  # type: ignore


"""
Intraday Backtesting Engine (Minute Data)

Features:
- Previous-day OHLC reference
- Bucket-based capital allocation
- Proper capital debit/credit
- Slippage on all executions
- Brokerage per order
- SL / Target handling
- Forced exit
- ROI before & after tax
- Max drawdown tracking
"""

# ================= DATA STRUCTURES =================
class OHLCVRecord(TypedDict):
    open: float
    high: float
    low: float
    close: float


# ================= CONFIG =================
START_CAPITAL = 100000
BUCKETS = 5
CAPITAL_PER_BUCKET = START_CAPITAL / BUCKETS

DATA_DIR = "Pure_Data"
PREV_DAY_FILE = "Resources/ohlcv_2025-12-23.txt"

FORCE_EXIT_TIME = "15-00-00"
BROKERAGE_PER_ORDER = 40
SLIPPAGE_PCT = 0.0005  # 0.05%


# ================= HELPERS =================
def clean_name(name: str) -> str:
    return name.strip().upper()


def is_header_or_separator(line: str) -> bool:
    s = line.strip().lower()
    return not s or s.startswith("company") or all(c in "-=" for c in s)


def validate_ohlcv(o, h, l, c) -> bool:
    return h >= l and all(v >= 0 for v in (o, h, l, c))


# ================= LOAD PREV DAY DATA =================
def load_prev_day_ohlc(filepath: str) -> Dict[str, OHLCVRecord]:
    prev = {}
    with open(filepath, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="|")
        for row in reader:
            if len(row) < 5:
                continue
            name = row[0].strip()
            if is_header_or_separator(name):
                continue
            try:
                stock = clean_name(name)
                o, h, l, c = map(float, row[1:5])
                if validate_ohlcv(o, h, l, c):
                    prev[stock] = {"open": o, "high": h, "low": l, "close": c}
            except:
                continue
    print(f"[INFO] Loaded prev-day OHLC for {len(prev)} stocks")
    return prev


prev_day_data = load_prev_day_ohlc(PREV_DAY_FILE)


# ================= STOCK NAME MAPPING =================
def build_stock_mapping(prev_dict):
    mapping = {}
    for name in prev_dict:
        base = (
            name.replace(" LIMITED", "")
            .replace(" LTD.", "")
            .replace(" LTD", "")
            .strip()
        )
        mapping[name] = name
        mapping[base] = name
    return mapping


stock_mapping = build_stock_mapping(prev_day_data)


def get_prev_day_data(stock: str) -> Optional[OHLCVRecord]:
    s = stock.upper().strip()
    if s in prev_day_data:
        return prev_day_data[s]
    if s in stock_mapping:
        return prev_day_data.get(stock_mapping[s])
    return None


# ================= TRADE ENGINE =================
def run_strategy(strategy_id: int):
    capital = START_CAPITAL
    open_positions = {}
    trade_log = []
    market_state = defaultdict(dict)
    last_price = {}

    used_buckets = 0
    stop_trading = False
    force_exit_done = False

    peak_capital = START_CAPITAL
    max_drawdown = 0

    def update_drawdown():
        nonlocal peak_capital, max_drawdown, capital
        peak_capital = max(peak_capital, capital)
        dd = (peak_capital - capital) / peak_capital * 100
        max_drawdown = max(max_drawdown, dd)

    def can_open_new_trade():
        return used_buckets < BUCKETS and not stop_trading

    def position_size(price):
        return int(CAPITAL_PER_BUCKET / price)

    def execute_buy(time, stock, price, sl, target):
        nonlocal capital, used_buckets
        exec_price = price * (1 + SLIPPAGE_PCT)
        qty = position_size(exec_price)
        cost = exec_price * qty
        if qty <= 0 or capital < cost:
            return

        capital -= cost
        open_positions[stock] = {
            "entry": exec_price,
            "qty": qty,
            "sl": sl,
            "target": target,
        }
        used_buckets += 1
        trade_log.append([time, stock, "BUY", exec_price, qty, 0.0, capital, used_buckets])

    def execute_sell(time, stock, price, action="SELL"):
        nonlocal capital, used_buckets
        pos = open_positions[stock]
        exec_price = price * (1 - SLIPPAGE_PCT)
        proceeds = exec_price * pos["qty"]
        pnl = proceeds - (pos["entry"] * pos["qty"])

        capital += proceeds
        trade_log.append(
            [time, stock, action, exec_price, pos["qty"], pnl, capital, used_buckets - 1]
        )
        del open_positions[stock]
        used_buckets -= 1
        update_drawdown()

    # ================= MAIN LOOP =================
    for file in sorted(os.listdir(DATA_DIR)):
        time_key = file.replace(".txt", "")
        h, m, *_ = map(int, time_key.split("-"))
        normalized_time = f"{h:02d}-{m:02d}-00"

        rows = []
        with open(os.path.join(DATA_DIR, file)) as f:
            for line in f:
                s = line.rsplit(":", 1)
                if len(s) == 2 and s[1].strip() != "NA":
                    try:
                        rows.append((s[0].strip(), float(s[1])))
                    except:
                        continue

        df = pd.DataFrame(rows, columns=["stock", "price"])

        for _, r in df.iterrows():
            last_price[r["stock"]] = r["price"]

        # ===== FORCE EXIT =====
        if normalized_time == FORCE_EXIT_TIME and not force_exit_done:
            for stock in list(open_positions):
                execute_sell(normalized_time, stock, last_price.get(stock, open_positions[stock]["entry"]), "FORCED_SELL")
            stop_trading = True
            force_exit_done = True
            continue

        if stop_trading:
            continue

        # ===== STRATEGY EXECUTION =====
        for _, r in df.iterrows():
            stock, price = r["stock"], r["price"]

            # SL / TARGET CHECK
            if stock in open_positions:
                pos = open_positions[stock]
                if pos["sl"] and price <= pos["sl"]:
                    execute_sell(normalized_time, stock, price, "SL_HIT")
                    continue
                if pos["target"] and price >= pos["target"]:
                    execute_sell(normalized_time, stock, price, "TARGET_HIT")
                    continue

            prev_ohlc = get_prev_day_data(stock)

            signal, sl, target = strategy_logic(
                time_key=normalized_time,
                hour=h,
                minute=m,
                second=0,
                stock=stock,
                price=price,
                position=open_positions.get(stock),
                market_state=market_state,
                can_trade=can_open_new_trade(),
                prev_day=prev_ohlc,
                strategy_id=strategy_id,
            )

            if signal == "BUY" and stock not in open_positions:
                execute_buy(normalized_time, stock, price, sl, target)
            elif signal == "SELL" and stock in open_positions:
                execute_sell(normalized_time, stock, price)

    # ===== FINAL EXIT =====
    for stock in list(open_positions):
        execute_sell("END", stock, last_price.get(stock, open_positions[stock]["entry"]), "FINAL_SELL")

    # ================= RESULTS =================
    df_trades = pd.DataFrame(
        trade_log,
        columns=["Time", "Stock", "Action", "Price", "Qty", "PnL", "Capital", "Used_Buckets"],
    )

    num_orders = len(df_trades)
    brokerage = num_orders * BROKERAGE_PER_ORDER
    amount_after_tax = capital - brokerage

    roi_before = ((capital - START_CAPITAL) / START_CAPITAL) * 100
    roi_after = ((amount_after_tax - START_CAPITAL) / START_CAPITAL) * 100

    return {
        "strategy_id": strategy_id,
        "final_capital": capital,
        "final_after_tax": amount_after_tax,
        "roi_before": roi_before,
        "roi_after": roi_after,
        "orders": num_orders,
        "brokerage": brokerage,
        "max_drawdown": max_drawdown,
    }


# ================= RUN =================
print("\n" + "="*80)
print("TESTING STRATEGY 9 ONLY".center(80))
print("="*80 + "\n")

results = []
for strategy_id in [9]:  # Only test strategy 9
    print(f"\n[INFO] Testing Strategy {strategy_id}...")
    result = run_strategy(strategy_id=strategy_id)
    results.append(result)
    
    print(f"\n      ROI (before tax): {result['roi_before']:.2f}%")
    print(f"      ROI (after tax):  {result['roi_after']:.2f}%")
    print(f"      Final Capital:    ${result['final_capital']:.2f}")
    print(f"      Max Drawdown:     {result['max_drawdown']:.2f}%")

print("\n" + "="*80)
print("SUMMARY - STRATEGIES RANKED BY ROI (AFTER TAX)".center(80))
print("="*80 + "\n")

# Sort by ROI after tax
sorted_results = sorted(results, key=lambda x: x['roi_after'], reverse=True)

print(f"{'Rank':<6} {'Strategy':<10} {'ROI %':<10} {'Capital':<15} {'Drawdown %':<12} {'Status':<15}")
print("-" * 80)

for rank, result in enumerate(sorted_results, 1):
    strategy_id = result['strategy_id']
    roi = result['roi_after']
    capital = result['final_after_tax']
    drawdown = result['max_drawdown']
    status = "✓ GOOD" if roi > 0.5 else "✗ POOR" if roi < -0.5 else "→ NEUTRAL"
    print(f"{rank:<6} {strategy_id:<10} {roi:>8.2f}%  ${capital:>13,.2f}  {drawdown:>10.2f}%  {status:<15}")

print("\n" + "="*80)
print("STRATEGIES PERFORMING BETTER THAN 0.5%".center(80))
print("="*80 + "\n")

good_strategies = [r for r in sorted_results if r['roi_after'] > 0.5]

if good_strategies:
    for result in good_strategies:
        print(f"\n✓ Strategy {result['strategy_id']}: {result['roi_after']:.2f}% ROI")
        print(f"  - Final Capital: ${result['final_after_tax']:.2f}")
        print(f"  - Orders: {result['orders']}")
        print(f"  - Brokerage: ${result['brokerage']:.2f}")
        print(f"  - Max Drawdown: {result['max_drawdown']:.2f}%")
else:
    print("No strategies performed better than 0.5% ROI")
    best = sorted_results[0]
    print(f"\nBest performing strategy is #{best['strategy_id']} with {best['roi_after']:.2f}% ROI")

print("\n" + "="*80)