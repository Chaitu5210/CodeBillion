import pandas as pd

"""
Downloads the NSE equity list and saves all stock tickers to a text file.
The script reads the official NSE equity CSV, appends '.NS' to each symbol,
and writes them line-by-line into 'nse_tickers.txt'.
"""


# NSE official equity list CSV
url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"

# Read CSV
df = pd.read_csv(url)

# Extract symbols + add .NS
tickers = df["SYMBOL"].astype(str).str.upper() + ".NS"

# Save to text file
output_file = "nse_tickers.txt"

with open(output_file, "w") as f:
    for t in tickers:
        f.write(t + "\n")

print(f"Saved {len(tickers)} tickers to {output_file}")
