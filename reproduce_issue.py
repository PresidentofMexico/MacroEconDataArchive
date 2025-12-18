import pandas as pd
from urllib.parse import quote_plus
import requests
import io

def fetch_fred(sid):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={quote_plus(sid)}"
    print(f"Fetching {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        print("Success!")
        print(df.head())
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    fetch_fred("CPIAUCSL")