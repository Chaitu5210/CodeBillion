from datetime import datetime

# ================= CONFIG =================
DATA_FILE = "time_close.txt"

START_CAPITAL = 100000
RISK_PER_TRADE = 0.003          # 0.3%
MAX_DAILY_LOSS_PCT = 0.02       # 2%
BROKERAGE = 40

ORB_START = "09:15:00"
ORB_END   = "09:30:00"
TRADE_START = "09:30:00"
TRADE_END   = "14:45:00"

# ================= HELPERS =================
def parse_time(t):
    return datetime.strptime(t, "%H:%M:%S")

def in_range(t, start, end):
    return start <= t <= end

def calculate_atr(prices, period=14):
    if len(prices) < period + 1:
        return None
    return sum(abs(prices[i] - prices[i-1]) for i in range(-period, 0)) / period

# ================= BACKTEST =================
def run_backtest():
    capital = START_CAPITAL
    day_start_capital = START_CAPITAL
    daily_loss_limit = START_CAPITAL * MAX_DAILY_LOSS_PCT

    prices = []
    trade_log = []

    orb_prices = []
    orb_high = orb_low = None
    position = None

    with open(DATA_FILE) as f:
        for line in f:
            time_str, price = line.strip().split(",")
            price = float(price)
            t = parse_time(time_str)

            prices.append(price)

            # -------- ORB COLLECTION --------
            if in_range(t, parse_time(ORB_START), parse_time(ORB_END)):
                orb_prices.append(price)
                continue

            if orb_prices and orb_high is None:
                orb_high = max(orb_prices)
                orb_low = min(orb_prices)

            if orb_high is None:
                continue

            # -------- TIME FILTER --------
            if not in_range(t, parse_time(TRADE_START), parse_time(TRADE_END)):
                continue

            atr = calculate_atr(prices)
            if atr is None:
                continue

            # -------- EXIT --------
            if position:
                pnl = (price - position["entry"]) * position["qty"]

                if price <= position["sl"] or price >= position["target"]:
                    capital += pnl - BROKERAGE
                    trade_log.append({
                        "time": time_str,
                        "action": "SELL",
                        "price": round(price, 2),
                        "qty": position["qty"],
                        "pnl": round(pnl, 2),
                        "capital": round(capital, 2)
                    })
                    position = None

                if day_start_capital - capital >= daily_loss_limit:
                    print("\n⚠️ Daily loss limit hit. Trading stopped.\n")
                    break
                continue

            # -------- ENTRY --------
            if len(prices) < 5:
                continue

            breakout = price > orb_high
            momentum = (price - prices[-5]) > 0.5 * atr

            if not (breakout and momentum):
                continue

            sl = price - atr
            risk_per_unit = price - sl
            if risk_per_unit <= 0:
                continue

            risk_amount = capital * RISK_PER_TRADE
            qty = int(risk_amount / risk_per_unit)
            if qty <= 0:
                continue

            target = price + (1.5 * atr)

            trade_log.append({
                "time": time_str,
                "action": "BUY",
                "price": round(price, 2),
                "qty": qty,
                "pnl": 0,
                "capital": round(capital, 2)
            })

            position = {
                "entry": price,
                "sl": sl,
                "target": target,
                "qty": qty
            }

        # -------- FORCE EOD EXIT --------
        if position:
            last_price = prices[-1]
            pnl = (last_price - position["entry"]) * position["qty"]
            capital += pnl - BROKERAGE
            trade_log.append({
                "time": "EOD",
                "action": "SELL",
                "price": round(last_price, 2),
                "qty": position["qty"],
                "pnl": round(pnl, 2),
                "capital": round(capital, 2)
            })

    generate_report(trade_log, capital)

# ================= REPORT =================
def generate_report(trades, final_capital):
    print("\n========== TRADE LOG ==========\n")
    for t in trades:
        print(
            f'{t["time"]} | {t["action"]:4} | '
            f'Price: {t["price"]:.2f} | '
            f'Qty: {t["qty"]} | '
            f'PnL: {t["pnl"]:.2f} | '
            f'Capital: {t["capital"]:.2f}'
        )

    sells = len([t for t in trades if t["action"] == "SELL"])
    net_pnl = final_capital - START_CAPITAL

    print("\n========== SUMMARY ==========\n")
    print(f"Starting Capital : ₹ {START_CAPITAL}")
    print(f"Final Capital    : ₹ {round(final_capital,2)}")
    print(f"Net PnL          : ₹ {round(net_pnl,2)}")
    print(f"Trades Closed    : {sells}")
    print(f"ROI              : {round((net_pnl/START_CAPITAL)*100,2)} %")

# ================= RUN =================
if __name__ == "__main__":
    run_backtest()
