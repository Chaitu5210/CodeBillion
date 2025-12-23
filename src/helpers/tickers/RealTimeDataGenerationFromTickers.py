import yfinance as yf
import pandas as pd
import os

"""
Fetches live 1-minute intraday stock data and saves closing prices to files.
For each NSE ticker, the script downloads today’s 1-minute data,
filters prices between 09:15 and 10:00 IST, and stores the close values
line-by-line in separate text files inside the 'live_data' folder.
"""

def live_data_generator(ticker):
    data = yf.download(ticker, period="1d", interval="1m", progress=False)
    if data.empty:
        raise SystemExit("No data returned — check ticker or network.")
    if data.index.tz is None:
        data.index = data.index.tz_localize("UTC").tz_convert("Asia/Kolkata")
    else:
        data.index = data.index.tz_convert("Asia/Kolkata")
    minute_df = data.between_time("09:15", "10:00")
    close_series = minute_df[["Close"]].squeeze()
    close_values = close_series.tolist()
    os.makedirs("live_data", exist_ok=True)
    out_file = f"live_data/{ticker}.txt"
    with open(out_file, "w") as f:
        for v in close_values:
            f.write(f"{v}\n")
    print(f"Saved {len(close_values)} values to {out_file}")

tickers = [
    "BALAXI.NS",
    "ABAN.NS",
    "BHARTIARTL.NS",
    "TARIL.NS",
    "AXISBANK.NS",
    "UNITEDPOLY.NS",
    "NIBE.NS",
    "DSSL.NS",
    "HINDUNILVR.NS",
    "GLFL.NS",
    "KOTAKBANK.NS",
    "WIPRO.NS",
    "SBIN.NS",
    "KSR.NS",
    "DIVISLAB.NS",
    "AERONEU.NS",
    "LOKESHMACH.NS",
    "VLSFINANCE.NS",
    "PATELEG-RE.NS",
    "EUROTEXIND.NS",
    "SMCGLOBAL.NS",
    "PANACEABIO.NS",
    "LOTUSEYE.NS",
    "ITC.NS",
    "MASKINVEST.NS",
    "VINNY.NS",
    "TVVISION.NS",
    "MAHAPEXLTD.NS",
    "CEWATER.NS",
    "INFY.NS",
    "SHAREINDIA.NS",
    "ASMS.NS",
    "RAJSREESUG.NS",
    "ULTRACEMCO.NS",
    "HDFCBANK.NS",
    "REFEX.NS",
    "ADANIENT.NS",
    "ROLLT.NS",
    "DJML.NS",
    "KRITINUT.NS",
    "BHARTIARTL.NS",
    "S&SPOWER.NS",
    "SIKKO.NS",
    "RELIANCE.NS",
    "TCS.NS",
    "SADHNANIQ.NS",
    "HCC-RE1.NS",
    "MARUTI.NS",
    "CAMLINFINE.NS",
    "DMART.NS"
]

for ticker in tickers:
    live_data_generator(ticker)
