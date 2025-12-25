import os
import upstox_client
from upstox_client.rest import ApiException

ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
API_VERSION = "2.0"

INSTRUMENT_KEY = "NSE_EQ|INE849A01020"   # RELIANCE INDUSTRIES
TARGET_DATE = "2025-12-23"              # yyyy-mm-dd ONLY


def save_1min_candles_to_file():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resources_dir = os.path.join(base_dir, "TemporaryResources")
    os.makedirs(resources_dir, exist_ok=True)

    output_file = os.path.join(resources_dir, "prices.txt")

    config = upstox_client.Configuration()
    config.access_token = ACCESS_TOKEN
    client = upstox_client.ApiClient(config)
    history_api = upstox_client.HistoryApi(client)

    try:
        # ⚠️ SDK supports ONLY to_date
        resp = history_api.get_historical_candle_data(
            INSTRUMENT_KEY,
            "1minute",
            TARGET_DATE,      # treated as TO_DATE
            API_VERSION
        )

        candles = resp.data.candles or []
        if not candles:
            print("No data returned")
            return

        candles.reverse()  # chronological order

        # ✅ FILTER ONLY REQUIRED DATE
        day_candles = [
            c for c in candles
            if c[0].startswith(TARGET_DATE)
        ]

        if not day_candles:
            print("No candles for target date")
            return

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Timestamp | Open | High | Low | Close | Volume\n")
            f.write("-" * 70 + "\n")

            for c in day_candles:
                f.write(
                    f"{c[0]} | {c[1]} | {c[2]} | {c[3]} | {c[4]} | {c[5]}\n"
                )

        print(f"✅ Saved {len(day_candles)} candles for {TARGET_DATE}")

    except ApiException as e:
        print("API Error:", e)


if __name__ == "__main__":
    save_1min_candles_to_file()
