# extract_time_close.py
# Reads a raw OHLC text file and writes only Time + Close price

INPUT_FILE = "prices.txt"        # raw OHLC file
OUTPUT_FILE = "time_close.txt"   # output file

with open(INPUT_FILE, "r") as fin, open(OUTPUT_FILE, "w") as fout:
    for line in fin:
        line = line.strip()

        # skip headers / separators
        if not line or line.startswith("Timestamp") or line.startswith("-"):
            continue

        # split columns
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 5:
            continue

        timestamp = parts[0]          # full timestamp
        close_price = parts[4]        # Close column

        # extract time only (HH:MM:SS)
        time_only = timestamp.split("T")[1].split("+")[0]

        fout.write(f"{time_only},{close_price}\n")

print("✅ Extracted time and close price into time_close.txt")
