import pandas as pd
from urllib.parse import quote_plus
import sys

def fetch_fred(sid):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={quote_plus(sid)}"
    print(f"Fetching {url}...")
    try:
        # Mimic the app's behavior exactly
        df = pd.read_csv(url)
        print("Success!")
        print(df.head())
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    fetch_fred("CPIAUCSL")