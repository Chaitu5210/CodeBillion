import csv
import os
import math
import statistics
from datetime import datetime
from typing import TypedDict, Optional, Dict
from collections import defaultdict

import pandas as pd

from core.strategy_testing.StrategyTestBed import strategy_logic

"""
Backtests multiple intraday trading strategies using minute-level price data.

The script:
- Loads previous-day OHLC data for reference
- Simulates intraday trades with bucket-based capital allocation
- Applies slippage and brokerage costs
- Tests strategy IDs 1–81
- Forces exit at a fixed time
- Computes profit, ROI (before/after tax), and max drawdown
- Identifies the best-performing strategy

Input data is read from text files, and results are printed to the console.
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

# ✅ FORCE prev-day file (uploaded)
PREV_DAY_FILE = "Resources/ohlcv_2025-12-19.txt"

FORCE_EXIT_TIME = "11-00-00"
BROKERAGE_PER_TRADE = 40
SLIPPAGE_PCT = 0.0005  # 0.05% slippage per execution (Entry & Exit)

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
    if not os.path.exists(filepath):
        print(f"[ERROR] Prev-day file not found: {filepath}")
        return prev

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

def get_prev_day_data(stock: str, prev_dict, mapping) -> Optional[OHLCVRecord]:
    s = stock.upper().strip()
    if s in prev_dict:
        return prev_dict[s]
    if s in mapping and mapping[s] in prev_dict:
        return prev_dict[mapping[s]]
    return None

# ================= STATE =================
capital = START_CAPITAL
open_positions = {}
trade_log = []
market_state = defaultdict(dict)

used_buckets = 0
stop_trading = False
force_exit_done = False
last_price = {}

peak_capital = START_CAPITAL
max_drawdown = 0

# ================= TRADE HELPERS =================
def position_size(price):
    return int(CAPITAL_PER_BUCKET / price)

def can_open_new_trade():
    return used_buckets < BUCKETS and not stop_trading

def update_drawdown():
    global peak_capital, max_drawdown
    peak_capital = max(peak_capital, capital)
    dd = (peak_capital - capital) / peak_capital * 100
    max_drawdown = max(max_drawdown, dd)

def execute_trade(time, stock, price, signal, sl=None, target=None):
    global capital, used_buckets

    # ===== BUY =====
    if signal == "BUY":
        if stock in open_positions or not can_open_new_trade():
            return

        # APPLY SLIPPAGE: You usually buy slightly higher than the signal price
        execution_price = price * (1 + SLIPPAGE_PCT)
        
        qty = position_size(execution_price)
        if qty <= 0:
            return

        # ✅ STORE sl & target (FIXES KeyError)
        open_positions[stock] = {
            "entry": execution_price,
            "qty": qty,
            "sl": sl,
            "target": target
        }

        used_buckets += 1
        trade_log.append([time, stock, "BUY", round(execution_price, 2), qty, 0.0, capital, used_buckets])

    # ===== SELL =====
    elif signal == "SELL" and stock in open_positions:
        pos = open_positions[stock]
        
        # APPLY SLIPPAGE: You usually sell slightly lower than the signal price
        execution_price = price * (1 - SLIPPAGE_PCT)
        
        pnl = (execution_price - pos["entry"]) * pos["qty"]
        capital += pnl

        trade_log.append([
            time, stock, "SELL", round(execution_price, 2),
            pos["qty"], round(pnl, 2), capital, used_buckets - 1
        ])

        del open_positions[stock]
        used_buckets -= 1
        update_drawdown()

# ================= STRATEGY TESTING LOOP =================
strategy_results = []
best_strategy = None
best_roi = -float('inf')
target_roi = 1.0  # 1%
target_profit = START_CAPITAL * (target_roi / 100)  # 1000 for 100,000

print("\n" + "="*70)
print("TESTING ALL STRATEGIES (1-81) WITH SLIPPAGE (0.05% per execution)")
print("="*70)

for strategy_id in range(1, 82):
    print(f"\n🔄 Testing Strategy {strategy_id}...")
    
    # Reset state for each strategy
    capital = START_CAPITAL
    open_positions = {}
    trade_log = []
    market_state = defaultdict(dict)
    used_buckets = 0
    stop_trading = False
    force_exit_done = False
    last_price = {}
    peak_capital = START_CAPITAL
    max_drawdown = 0

    # ================= MAIN LOOP =================
    files = sorted(os.listdir(DATA_DIR))

    for file in files:
        time_key = file.replace(".txt", "")
        parts = time_key.split("-")
        hour, minute, second = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0
        
        # Create a normalized time_key for strategy matching (09-20-00 format)
        normalized_time_key = f"{hour:02d}-{minute:02d}-00"

        rows = []
        with open(os.path.join(DATA_DIR, file)) as f:
            for line in f:
                parts = line.rsplit(":", 1)
                if len(parts) == 2 and parts[1].strip() != "NA":
                    try:
                        rows.append((parts[0].strip(), float(parts[1])))
                    except:
                        continue

        df = pd.DataFrame(rows, columns=["stock", "price"])

        for _, r in df.iterrows():
            last_price[r["stock"]] = r["price"]

        # ===== FORCE EXIT =====
        if normalized_time_key == FORCE_EXIT_TIME and not force_exit_done:
            for stock, pos in list(open_positions.items()):
                price = last_price.get(stock, pos["entry"])
                pnl = (price - pos["entry"]) * pos["qty"]
                capital += pnl

                trade_log.append([
                    normalized_time_key, stock, "FORCED_SELL", price,
                    pos["qty"], round(pnl, 2), capital, used_buckets - 1
                ])

                del open_positions[stock]
                used_buckets -= 1
                update_drawdown()

            stop_trading = True
            force_exit_done = True
            continue

        if stop_trading:
            continue

        # ===== STRATEGY =====
        for _, row in df.iterrows():
            stock = row["stock"]
            price = row["price"]

            prev_ohlc = get_prev_day_data(stock, prev_day_data, stock_mapping)

            signal, sl, target = strategy_logic(
                time_key=normalized_time_key,
                hour=hour,
                minute=minute,
                second=second,
                stock=stock,
                price=price,
                position=open_positions.get(stock),
                market_state=market_state,
                can_trade=can_open_new_trade(),
                prev_day=prev_ohlc,
                strategy_id=strategy_id  # Pass strategy_id here
            )

            if signal:
                execute_trade(time_key, stock, price, signal, sl, target)

    # ================= FINAL EXIT =================
    for stock, pos in list(open_positions.items()):
        price = last_price.get(stock, pos["entry"])
        pnl = (price - pos["entry"]) * pos["qty"]
        capital += pnl

        trade_log.append([
            "END", stock, "FINAL_SELL", price,
            pos["qty"], round(pnl, 2), capital, used_buckets - 1
        ])

        del open_positions[stock]
        used_buckets -= 1
        update_drawdown()

    # ================= CALCULATE RESULTS =================
    df_trades = pd.DataFrame(trade_log, columns=[
        "Time", "Stock", "Action", "Price", "Qty", "PnL", "Capital", "Used_Buckets"
    ])
    
    closed = df_trades[df_trades["Action"].isin(["SELL", "FORCED_SELL", "FINAL_SELL"])]
    num_trades = len(closed)
    total_pnl = closed["PnL"].sum() if len(closed) > 0 else 0.0

    # Calculate tax/brokerage (2 trades per round trip)
    total_brokerage = BROKERAGE_PER_TRADE * num_trades
    amount_after_tax = capital - total_brokerage
    
    # ROI after tax
    roi_after_tax = ((amount_after_tax - START_CAPITAL) / START_CAPITAL) * 100
    roi_before_tax = ((capital - START_CAPITAL) / START_CAPITAL) * 100
    profit_after_tax = amount_after_tax - START_CAPITAL
    profit_before_tax = capital - START_CAPITAL

    strategy_results.append({
        'strategy_id': strategy_id,
        'capital': capital,
        'profit': profit_before_tax,
        'roi': roi_before_tax,
        'profit_after_tax': profit_after_tax,
        'roi_after_tax': roi_after_tax,
        'num_trades': num_trades,
        'total_pnl': total_pnl,
        'tax': total_brokerage,
        'amount_after_tax': amount_after_tax,
        'max_drawdown': max_drawdown
    })

    print(f"   Strategy {strategy_id}: ROI = {roi_after_tax:.2f}% (after tax) | Capital = ₹{amount_after_tax:.2f}")

    # Check if ROI > 1% (after tax)
    if roi_after_tax > target_roi:
        print(f"\n✅ FOUND! Strategy {strategy_id} achieved ROI > {target_roi}% (after tax)")
        best_strategy = strategy_id
        best_roi = roi_after_tax
        break

# ================= RESULTS SUMMARY =================
print("\n" + "="*70)
print("STRATEGY TEST SUMMARY (WITH TAXES)")
print("="*70)

for result in strategy_results:
    roi_after_tax = result['roi_after_tax']
    status = "✅ PASSED" if roi_after_tax > target_roi else "❌"
    print(f"\nStrategy {result['strategy_id']}:")
    print(f"  Final Capital (before tax) : ₹{result['capital']:.2f}")
    print(f"  Final Capital (after tax)  : ₹{result['amount_after_tax']:.2f}")
    print(f"  Profit (before tax)        : ₹{result['profit']:.2f}")
    print(f"  Profit (after tax)         : ₹{result['profit_after_tax']:.2f}")
    print(f"  Brokerage Cost             : ₹{result['tax']:.2f}")
    print(f"  ROI (before tax)           : {result['roi']:.2f}%")
    print(f"  ROI (after tax)            : {roi_after_tax:.2f}%")
    print(f"  Trades                     : {result['num_trades']}")
    print(f"  Max Drawdown               : {result['max_drawdown']:.2f}%")
    print(f"  Status                     : {status}")

print("\n" + "="*70)
if best_strategy:
    best_result = strategy_results[best_strategy-1]
    print(f"🏆 BEST STRATEGY: Strategy {best_strategy}")
    print(f"   ROI (after tax): {best_result['roi_after_tax']:.2f}%")
    print(f"   Final Capital (after tax): ₹{best_result['amount_after_tax']:.2f}")
    print(f"   Profit (after tax): ₹{best_result['profit_after_tax']:.2f}")
else:
    print("⚠️  No strategy achieved ROI > 1% (after tax)")
    best_idx = max(range(len(strategy_results)), key=lambda i: strategy_results[i]['roi_after_tax'])
    best_res = strategy_results[best_idx]
    print(f"   Best strategy: {best_res['strategy_id']} with ROI {best_res['roi_after_tax']:.2f}% (after tax)")
print("="*70)
