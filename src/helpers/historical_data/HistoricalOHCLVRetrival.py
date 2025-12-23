import os
import time
import upstox_client
from upstox_client.rest import ApiException

ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
API_VERSION = "2.0"

REQUEST_DELAY = 0.35   # ~3 requests/sec (SAFE)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = os.path.join(BASE_DIR, "Resources")
STOCK_FILE = os.path.join(RESOURCES_DIR, "stock_names.txt")


def load_instrument_keys(path):
    instruments = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if ":" not in line:
                continue
            k, v = line.strip().split(":", 1)
            instruments[k.strip().strip('"')] = v.strip().strip('"')
    return instruments


def fetch_ohlcv(instrument_key, date, history_api):
    try:
        resp = history_api.get_historical_candle_data(
            instrument_key,
            "day",
            date,
            API_VERSION
        )

        candles = resp.data.candles
        if not candles:
            return None

        c = candles[0]
        return c[1], c[2], c[3], c[4], c[5]

    except ApiException:
        return None


def fetch_all_ohlcv(date):
    config = upstox_client.Configuration()
    config.access_token = ACCESS_TOKEN
    client = upstox_client.ApiClient(config)
    history_api = upstox_client.HistoryApi(client)

    instruments = load_instrument_keys(STOCK_FILE)

    output_file = os.path.join(RESOURCES_DIR, f"ohlcv_{date}.txt")

    with open(output_file, "w", encoding="utf-8") as out:
        out.write("Company | Open | High | Low | Close | Volume\n")
        out.write("-" * 80 + "\n")

        for i, (inst_key, name) in enumerate(instruments.items(), 1):
            data = fetch_ohlcv(inst_key, date, history_api)

            if data is None:
                out.write(f"{name} | NA | NA | NA | NA | NA\n")
            else:
                o, h, l, c, v = data
                out.write(f"{name} | {o} | {h} | {l} | {c} | {v}\n")

            # 🔒 RATE LIMIT CONTROL
            time.sleep(REQUEST_DELAY)

            if i % 50 == 0:
                print(f"Fetched {i}/{len(instruments)} stocks")

    print(f"✅ Saved safely to {output_file}")

fetch_all_ohlcv("2025-12-19")
