import yfinance as yf
import pandas as pd
import streamlit as st
import hashlib
import requests
from bs4 import BeautifulSoup

class WeddingApp:
    def __init__(self):
        self.sp500 = None

    def load_sp500(self):
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "constituents"})
        df = pd.read_html(str(table))[0]
        df = df[['Symbol', 'Security', 'GICS Sector']]
        df.columns = ['Ticker', 'Name', 'Sector']
        df['Ticker'] = df['Ticker'].str.replace('.', '-', regex=False)
        self.sp500 = df
        return df

    @st.cache_data
    def get_last_prices(self, tickers):
        data = yf.download(tickers=tickers, period="1d")['Adj Close']
        if isinstance(data, pd.Series):
            data = data.to_frame()
        return data.iloc[-1].to_dict()

    @st.cache_data
    def get_history(self, ticker):
        df = yf.download(ticker, period="10y", interval="1mo")['Adj Close']
        return df

    def encode_transfer_code(self, selections):
        """
        selections: list of tuples (ticker, shares)
        """
        raw = ",".join([f"{t}:{s}" for t, s in selections])
        hashcode = hashlib.sha256(raw.encode()).hexdigest()[:10].upper()
        return hashcode

    def decode_transfer_code(self, code):
        # placeholder: in real case, store mapping
        return f"Decoded code {code}, actual mapping requires backend"

    def sectors_from_quiz(self, answers):
        # simple mapping example
        mapping = {
            "tech": ["Information Technology"],
            "green": ["Utilities", "Energy"],
            "classic": ["Financials", "Consumer Staples"]
        }
        sectors = []
        for ans in answers:
            sectors.extend(mapping.get(ans, []))
        return list(set(sectors))
