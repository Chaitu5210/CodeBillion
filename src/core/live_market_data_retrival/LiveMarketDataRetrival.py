import time
from typing import List, Dict

import upstox_client
from upstox_client.rest import ApiException
from Compute import start_computation
ACCESS_TOKEN = ""

INSTRUMENT_FILE = "stocks_only.txt"

OUTPUT_FILE = "ltp_latest.txt"

CHUNK_SIZE = 200
API_VERSION = "2.0"
SLEEP_BETWEEN_CALLS = 0.25

def load_instruments(path: str) -> (List[str], Dict[str, str]):
    keys: List[str] = []
    key_to_name: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if ":" not in line:
                continue
            left, right = line.split(":", 1)

            left = left.strip()
            right = right.strip().rstrip(",")
            if left.startswith('"') and left.endswith('"'):
                inst_key = left[1:-1]
            else:
                inst_key = left
            if right.startswith('"') and right.endswith('"'):
                company_name = right[1:-1]
            else:
                company_name = right
            keys.append(inst_key)
            key_to_name[inst_key] = company_name

    return keys, key_to_name


def chunked(items: List[str], n: int):
    """Yield successive n-sized chunks from a list."""
    for i in range(0, len(items), n):
        yield items[i:i + n]

def make_upstox_client() -> upstox_client.MarketQuoteApi:
    configuration = upstox_client.Configuration()
    configuration.access_token = ACCESS_TOKEN
    api_client = upstox_client.ApiClient(configuration)
    quote_api = upstox_client.MarketQuoteApi(api_client)
    return quote_api

def fetch_all_ltp_once(
    quote_api: upstox_client.MarketQuoteApi,
    instrument_keys: List[str]
) -> Dict[str, float]:
    all_prices: Dict[str, float] = {}
    for keys_chunk in chunked(instrument_keys, CHUNK_SIZE):
        symbol_param = ",".join(keys_chunk)
        try:
            resp = quote_api.ltp(symbol=symbol_param, api_version=API_VERSION)
        except ApiException as e:
            print(f"[ERROR] LTP API failed for chunk: {e}")
            continue
        data = getattr(resp, "data", None)
        if data is None:
            try:
                data = resp.to_dict().get("data", {})
            except Exception:
                data = {}
        for _, obj in data.items():
            if hasattr(obj, "to_dict"):
                obj_dict = obj.to_dict()
            else:
                 obj_dict = obj
            inst_token = obj_dict.get("instrument_token")
            ltp = obj_dict.get("last_price")
            if inst_token is not None:
                all_prices[inst_token] = ltp
        time.sleep(SLEEP_BETWEEN_CALLS)
    return all_prices


def write_prices_to_file(
    output_path: str,
    prices: Dict[str, float],
    key_to_name: Dict[str, str],
    instrument_keys: List[str]
) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        for key in instrument_keys:
            name = key_to_name.get(key, key)
            price = prices.get(key)

            if price is None:
                line = f"{name} : NA\n"
            else:
                line = f"{name} : {price}\n"
            f.write(line)
def main():
    instrument_keys, key_to_name = load_instruments(INSTRUMENT_FILE)
    print(f"Loaded {len(instrument_keys)} instrument keys from {INSTRUMENT_FILE}")

    if not instrument_keys:
        raise RuntimeError("No instrument_keys found. Check your file path/format.")

    quote_api = make_upstox_client()

    while True:
        loop_start = time.time()

        prices = fetch_all_ltp_once(quote_api, instrument_keys)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Got LTP for {len(prices)} instruments")
        write_prices_to_file(OUTPUT_FILE, prices, key_to_name, instrument_keys)
        print(f"Wrote latest LTPs to {OUTPUT_FILE}")
        start_computation()
        elapsed = time.time() - loop_start
        sleep_for = max(0, 60 - elapsed)
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()
