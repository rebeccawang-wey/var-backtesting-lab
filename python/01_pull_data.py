import duckdb
import yfinance as yf
import pandas as pd

START = "2007-01-01"
TICKERS = {
    1: ("SPY",      "SPDR S&P 500",          "equity",    "USD"),
    2: ("XIC.TO",   "iShares TSX Capped",    "equity",    "CAD"),
    3: ("TLT",      "20Y Treasury Bond",     "rates",     "USD"), 
    4: ("HYG",      "High Yield Corp Bond",  "credit",    "USD"),
    5: ("CAD=X",    "USD/CAD FX",            "fx",        "CAD"),
    6: ("GLD",      "Gold",                  "commodity", "USD"),
}

con = duckdb.connect("data/market.duckdb")
con.execute(open("sql/01_schema.sql").read())

for iid, (ticker, name, aclass, ccy) in TICKERS.items(): 
    df = yf.download(ticker, start = START, progress = False, auto_adjust = False)
    if df.empty:
        print(f"WARNING: {ticker} returned no data — skipping")
        continue
    if isinstance(df.columns, pd.MultiIndex): 
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns = {"Adj Close": "adj_close", "Open": "open", 
                              "High": "high", "Low": "low", 
                              "Close": "close", "Volume": "volume"})
    df = df.reset_index().rename(columns = {"Date": "date"})
    df["instrument_id"] = iid
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df[["instrument_id", "date", "open", "high", "low", 
             "close", "adj_close", "volume"]].dropna(subset = ["adj_close"])

    con.execute("INSERT INTO instruments VALUES (?, ?, ?, ?, ?)",
                [iid, ticker, name, aclass, ccy])

    con.execute("INSERT INTO prices SELECT * FROM df")
    print(f"{ticker}: {len(df)} rows, {df['date'].min()} -> {df['date'].max()}")

con.close()
print("done.")