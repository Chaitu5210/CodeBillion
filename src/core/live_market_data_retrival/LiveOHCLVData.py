import json
import time
import os
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Thread, Lock

import websocket

# ================= CONFIG =================
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0VkFHVVEiLCJqdGkiOiI2OTRiNWY4NDZhNjY4YjU1YTdmMThjNDYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzY2NTQ3MzMyLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NjY2MTM2MDB9.jpoZjSo9CHPBZOTXs-5gE0ySIAZEnXEkGu6G92Fercc"
INSTRUMENT_FILE = "StockNamesWithSymbols.txt"

PURE_DATA_DIR = "OHCLV_Data"
os.makedirs(PURE_DATA_DIR, exist_ok=True)

WS_URL = "wss://api.upstox.com/v2/feed/market-data-feed"

BATCH_SIZE = 200
FLUSH_INTERVAL = 60

# ================= GLOBAL STATE =================
candles = defaultdict(dict)      # minute -> instrument -> ohlcv
last_volume = {}                 # instrument -> last seen volume
candles_lock = Lock()

instrument_to_name = {}

# ================= HELPERS =================
def load_instruments(path):
    keys = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if ":" not in line:
                continue
            k, v = line.strip().rstrip(",").split(":", 1)
            inst = k.strip().strip('"')
            name = v.strip().strip('"')
            keys.append(inst)
            instrument_to_name[inst] = name
    return keys

def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def minute_key(dt=None):
    if not dt:
        dt = datetime.now()
    return dt.strftime("%H-%M-00")

# ================= WEBSOCKET WORKER =================
def ws_worker(instrument_batch):

    def on_open(ws):
        ws.send(json.dumps({
            "guid": "sub",
            "method": "sub",
            "data": {
                "mode": "ltpc",
                "instrumentKeys": instrument_batch
            }
        }))
        print(f"✅ WS subscribed: {len(instrument_batch)}")

    def on_message(ws, message):
        try:
            payload = json.loads(message)
            data = payload.get("data", {})
            minute = minute_key()

            with candles_lock:
                for inst, tick in data.items():
                    ltp = tick.get("ltp")
                    total_vol = tick.get("volume")

                    if ltp is None or total_vol is None:
                        continue

                    prev_vol = last_volume.get(inst, total_vol)
                    delta_vol = max(0, total_vol - prev_vol)
                    last_volume[inst] = total_vol

                    c = candles[minute].get(inst)
                    if not c:
                        candles[minute][inst] = {
                            "open": ltp,
                            "high": ltp,
                            "low": ltp,
                            "close": ltp,
                            "volume": delta_vol
                        }
                    else:
                        c["high"] = max(c["high"], ltp)
                        c["low"] = min(c["low"], ltp)
                        c["close"] = ltp
                        c["volume"] += delta_vol
        except Exception as e:
            print("❌ WS message error:", e)

    while True:
        ws = websocket.WebSocketApp(
            WS_URL,
            header={"Authorization": ACCESS_TOKEN},
            on_open=on_open,
            on_message=on_message
        )

        ws.run_forever(ping_interval=20, ping_timeout=10)
        print("🔁 WS reconnecting...")
        time.sleep(2)

# ================= FLUSH LOOP =================
def flush_loop():
    while True:
        time.sleep(FLUSH_INTERVAL)

        flush_minute = minute_key(datetime.now() - timedelta(minutes=1))

        with candles_lock:
            data = candles.pop(flush_minute, None)

        if not data:
            continue

        file_path = os.path.join(PURE_DATA_DIR, f"{flush_minute}.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            for inst, c in data.items():
                name = instrument_to_name.get(inst, inst)
                f.write(
                    f"{name} : "
                    f"{c['open']},"
                    f"{c['high']},"
                    f"{c['low']},"
                    f"{c['close']},"
                    f"{c['volume']}\n"
                )

        print(f"[{flush_minute}] ✔ OHLCV written")

# ================= MAIN =================
def main():
    instruments = load_instruments(INSTRUMENT_FILE)
    print(f"Loaded {len(instruments)} instruments")

    Thread(target=flush_loop, daemon=True).start()

    for batch in chunk(instruments, BATCH_SIZE):
        Thread(target=ws_worker, args=(batch,), daemon=True).start()
        time.sleep(0.4)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
