# c_wedding_app.py
from __future__ import annotations
import re
import os
import time
import json
import random
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Tuple
import pandas as pd

try:
    import yfinance as yf
except Exception:
    yf = None  # optional

# -------------------------
# Minimal i18n dictionary
# -------------------------
I18N = {
    "it": {
        "app_title": "Gioco degli Auguri • Wedding App",
        "welcome_title": "Benvenuto! 🎉",
        "welcome_sub": "Trasforma il tuo regalo in simboli di buon augurio (niente finanza vera, promesso!)",
        "start_quiz": "Inizia il quiz",
        "profile_title": "Step 1 • Conosciamoci",
        "q1": "Che tipo di regalo vorresti fare agli sposi?",
        "q1_opts": ["🌍 Viaggi & Avventure", "🍝 Cibo & Tradizione", "🎬 Divertimento & Relax", "🚀 Futuro & Innovazione"],
        "q2": "Quale valore pensi rappresenti meglio la coppia?",
        "q2_opts": ["💖 Amore romantico", "💪 Energia & sportività", "✨ Magia & fantasia", "📱 Tecnologia & modernità"],
        "q3": "Se dovessi scegliere un settore…",
        "q3_opts": ["🛫 Viaggi & trasporti", "🥂 Food & Beverage", "🎮 Intrattenimento", "⚡ Energia & innovazione"],
        "to_suggestions": "Vai ai suggerimenti",
        "suggestions_title": "Step 2 • Suggerimenti per te",
        "suggestions_sub": "Spunta i simboli che vuoi regalare (puoi anche cercare).",
        "search_placeholder": "Cerca un’azienda (es. Disney, Ferrari)…",
        "to_amounts": "Conferma selezioni",
        "amounts_title": "Step 3 • Importi",
        "amounts_sub": "Assegna un importo a ciascun simbolo scelto. È solo un gioco simbolico 😉",
        "total": "Totale",
        "instructions_safe": "Non stai comprando azioni vere: è solo un gioco simbolico 🎁. Il regalo vero è il bonifico.",
        "generate_code": "Genera codice regalo",
        "your_code": "Il tuo codice da mettere nella causale:",
        "copy_hint": "Copia e incolla questo codice nella causale del bonifico.",
        "stats_title": "Statistiche simpatiche",
        "top_brands": "Brand più scelti",
        "total_symbols": "Totale simboli regalati",
        "reset": "Azzera selezioni",
        "lang_label": "Lingua",
        "step": "Step",
        "back": "Indietro",
        "forward": "Avanti",
    },
    "en": {
        "app_title": "Good Wishes Game • Wedding App",
        "welcome_title": "Welcome! 🎉",
        "welcome_sub": "Turn your gift into symbolic good-luck tokens (no real finance, promise!)",
        "start_quiz": "Start the quiz",
        "profile_title": "Step 1 • Let’s get to know you",
        "q1": "What kind of gift would you like to give?",
        "q1_opts": ["🌍 Travel & Adventure", "🍝 Food & Tradition", "🎬 Fun & Chill", "🚀 Future & Innovation"],
        "q2": "Which value best represents the couple?",
        "q2_opts": ["💖 Romantic love", "💪 Energy & sport", "✨ Magic & wonder", "📱 Tech & modernity"],
        "q3": "If you had to pick a sector…",
        "q3_opts": ["🛫 Travel & Transport", "🥂 Food & Beverage", "🎮 Entertainment", "⚡ Energy & Innovation"],
        "to_suggestions": "See suggestions",
        "suggestions_title": "Step 2 • Suggestions for you",
        "suggestions_sub": "Tick the tokens you want to gift (you can also search).",
        "search_placeholder": "Search a company (e.g., Disney, Ferrari)…",
        "to_amounts": "Confirm selections",
        "amounts_title": "Step 3 • Amounts",
        "amounts_sub": "Set an amount for each chosen token. This is just symbolic 😉",
        "total": "Total",
        "instructions_safe": "You’re NOT buying real stocks: it’s a symbolic game 🎁. The real gift is the bank transfer.",
        "generate_code": "Generate gift code",
        "your_code": "Your code to put in the bank transfer note:",
        "copy_hint": "Copy & paste this code into your bank transfer note.",
        "stats_title": "Fun stats",
        "top_brands": "Most-picked brands",
        "total_symbols": "Total tokens gifted",
        "reset": "Reset selections",
        "lang_label": "Language",
        "step": "Step",
        "back": "Back",
        "forward": "Next",
    },
}


# -------------------------
# Utility / data structures
# -------------------------
EMOJI_MAP = {
    "Tesla": "🚗⚡", "Disney": "✨", "Coca-Cola": "🥤", "Apple": "🍏", "Nike": "👟",
    "Ferrari": "🏎️", "Nestlé": "🍫", "Airbus": "✈️", "Booking Holdings": "🌍",
    "Netflix": "🎬", "Microsoft": "🖥️", "Amazon": "📦", "Alphabet": "🔎",
    "Meta": "💬", "Shell": "🛢️", "TotalEnergies": "⚡", "ASML": "🔬",
    "Siemens": "🛠️", "LVMH": "👜", "Adidas": "👟", "PepsiCo": "🥤", "Starbucks": "☕",
    "McDonald’s": "🍟", "Airbnb": "🏡", "Spotify": "🎵", "Samsung": "📱",
}

# Fallback curated list (brand → (ticker, index_name))
# Used if scraping fails; keep it famous & mixed (US + EU).
FALLBACK_BRANDS = {
    "Apple": ("AAPL", "NASDAQ-100"),
    "Microsoft": ("MSFT", "NASDAQ-100"),
    "Amazon": ("AMZN", "NASDAQ-100"),
    "Alphabet": ("GOOGL", "NASDAQ-100"),
    "Meta": ("META", "NASDAQ-100"),
    "Tesla": ("TSLA", "NASDAQ-100"),
    "Netflix": ("NFLX", "NASDAQ-100"),
    "NVIDIA": ("NVDA", "NASDAQ-100"),
    "Disney": ("DIS", "S&P 500"),
    "Coca-Cola": ("KO", "S&P 500"),
    "Nike": ("NKE", "S&P 500"),
    "McDonald’s": ("MCD", "S&P 500"),
    "PepsiCo": ("PEP", "S&P 500"),
    "Starbucks": ("SBUX", "S&P 500"),
    "Airbnb": ("ABNB", "NASDAQ-100"),
    "Booking Holdings": ("BKNG", "NASDAQ-100"),
    "Ferrari": ("RACE", "EuroStoxx-like"),
    "ASML": ("ASML", "EuroStoxx 50"),
    "Siemens": ("SIEGY", "EuroStoxx 50 (ADR)"),
    "LVMH": ("LVMUY", "EuroStoxx 50 (ADR)"),
    "Nestlé": ("NSRGY", "EuroStoxx 50 (ADR)"),
    "TotalEnergies": ("TTE", "EuroStoxx 50"),
    "Shell": ("SHEL", "EuroStoxx 50"),
    "Adidas": ("ADDYY", "EuroStoxx 50 (ADR)"),
    "Spotify": ("SPOT", "EU-listed to US ADR"),
    "Samsung": ("SSNLF", "KOR Large Cap (OTC)"),
    "Airbus": ("EADSY", "EuroStoxx 50 (ADR)"),
}


@dataclass
class Brand:
    name: str
    ticker: str
    index_name: str


class WeddingApp:
    def __init__(self, data_dir: str = ".", donations_csv: str = "donations.csv"):
        self.data_dir = data_dir
        self.donations_csv = os.path.join(self.data_dir, donations_csv)
        self._universe = None  # pd.DataFrame with columns: name, ticker, index
        self.random = random.Random(2025)

    # -------------------------
    # Data loading
    # -------------------------
    def load_index_sp500(self) -> pd.DataFrame:
        # Wikipedia S&P 500 table
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        try:
            tables = pd.read_html(url)
            df = tables[0][["Security", "Symbol"]].rename(columns={"Security": "name", "Symbol": "ticker"})
            df["index"] = "S&P 500"
            return df
        except Exception:
            return pd.DataFrame()

    def load_index_nasdaq100(self) -> pd.DataFrame:
        # Wikipedia NASDAQ-100 table
        url = "https://en.wikipedia.org/wiki/NASDAQ-100"
        try:
            tables = pd.read_html(url)
            # Find table with Ticker and Company
            cand = None
            for t in tables:
                cols = set([c.lower() for c in t.columns])
                if {"ticker", "company"}.issubset(cols):
                    cand = t
                    break
            if cand is None:
                cand = tables[3]  # heuristic fallback
            df = cand.rename(columns={c: c.lower() for c in cand.columns})
            df = df[["company", "ticker"]].rename(columns={"company": "name"})
            df["index"] = "NASDAQ-100"
            return df
        except Exception:
            return pd.DataFrame()

    def load_index_eurostoxx50(self) -> pd.DataFrame:
        # Wikipedia Euro Stoxx 50
        url = "https://en.wikipedia.org/wiki/EURO_STOXX_50"
        try:
            tables = pd.read_html(url)
            # usually first table has company and ticker columns
            cand = None
            for t in tables:
                lc = [str(c).lower() for c in t.columns]
                if ("company" in lc) and ("ticker" in lc or "ticker symbol" in lc):
                    cand = t
                    break
            if cand is None:
                cand = tables[0]
            df = cand.rename(columns={c: c.lower() for c in cand.columns})
            # normalize column names
            ticker_col = "ticker" if "ticker" in df.columns else ("ticker symbol" if "ticker symbol" in df.columns else df.columns[-1])
            company_col = "company" if "company" in df.columns else df.columns[0]
            df = df[[company_col, ticker_col]].rename(columns={company_col: "name", ticker_col: "ticker"})
            df["index"] = "EuroStoxx 50"
            return df
        except Exception:
            return pd.DataFrame()

    def build_universe(self, famous_only: bool = True) -> pd.DataFrame:
        """Combine indices and deduplicate; if famous_only True keep curated brands set."""
        if self._universe is not None:
            return self._universe

        sp = self.load_index_sp500()
        ndx = self.load_index_nasdaq100()
        esx = self.load_index_eurostoxx50()
        combined = pd.concat([sp, ndx, esx], ignore_index=True).dropna().drop_duplicates(subset=["ticker"])
        if combined.empty:
            # fall back to curated list
            data = [{"name": k, "ticker": v[0], "index": v[1]} for k, v in FALLBACK_BRANDS.items()]
            combined = pd.DataFrame(data)

        if famous_only:
            famous_names = set(FALLBACK_BRANDS.keys())
            uni = combined.copy()
            uni["is_famous"] = uni["name"].apply(lambda n: self.closest_famous(n, famous_names))
            # keep famous ones + exact matches; if none, fallback to top 40 combined
            keep = uni[uni["is_famous"]]
            if keep.empty:
                keep = combined.head(40)
            combined = keep.drop(columns=["is_famous"]).reset_index(drop=True)

        # Attach emojis if available
        combined["emoji"] = combined["name"].map(EMOJI_MAP).fillna("")
        self._universe = combined.sort_values("name").reset_index(drop=True)
        return self._universe

    def closest_famous(self, name: str, famous_names: set) -> bool:
        # simple heuristic: exact or partial containment
        nm = name.lower()
        for f in famous_names:
            if f.lower() in nm or nm in f.lower():
                return True
        return name in famous_names

    # -------------------------
    # Suggestions based on profile answers
    # -------------------------
    def suggestions(self, answers: Dict[str, str], k: int = 10) -> pd.DataFrame:
        uni = self.build_universe(famous_only=True).copy()

        # Scoring by simple keyword/brand affinity rules
        score = []
        for _, row in uni.iterrows():
            s = 0
            n = row["name"].lower()
            # Q1
            q1 = answers.get("q1", "")
            if "viaggi" in q1 or "travel" in q1 or "avventure" in q1 or "adventure" in q1:
                if any(x in n for x in ["booking", "airbus", "ferrari", "tesla", "airbnb"]):
                    s += 3
            if "cibo" in q1 or "food" in q1 or "tradizione" in q1 or "tradition" in q1:
                if any(x in n for x in ["nestlé", "coca", "pepsi", "starbucks", "mcdon"]):
                    s += 3
            if "divert" in q1 or "fun" in q1 or "relax" in q1:
                if any(x in n for x in ["disney", "netflix", "spotify"]):
                    s += 3
            if "futuro" in q1 or "innovation" in q1 or "innovazione" in q1:
                if any(x in n for x in ["tesla", "apple", "microsoft", "amazon", "alphabet", "meta", "nvidia", "asml", "samsung"]):
                    s += 3

            # Q2
            q2 = answers.get("q2", "")
            if "romant" in q2 or "romantic" in q2:
                if "disney" in n or "lvmh" in n:
                    s += 2
            if "energia" in q2 or "energy" in q2 or "sport" in q2:
                if any(x in n for x in ["nike", "adidas", "tesla", "total", "shell"]):
                    s += 2
            if "magia" in q2 or "magic" in q2:
                if "disney" in n:
                    s += 2
            if "tecnologia" in q2 or "tech" in q2 or "modern" in q2:
                if any(x in n for x in ["apple", "microsoft", "amazon", "alphabet", "meta", "nvidia", "asml", "samsung"]):
                    s += 2

            # Q3 sector nudge
            q3 = answers.get("q3", "")
            if "viaggi" in q3 or "travel" in q3 or "trasporti" in q3 or "transport" in q3:
                if any(x in n for x in ["airbus", "booking", "airbnb", "ferrari", "tesla"]):
                    s += 2
            if "food" in q3 or "beverage" in q3 or "cibo" in q3:
                if any(x in n for x in ["starbucks", "nestlé", "coca", "pepsi", "mcdon"]):
                    s += 2
            if "intratten" in q3 or "entertain" in q3:
                if any(x in n for x in ["disney", "netflix", "spotify"]):
                    s += 2
            if "energia" in q3 or "innov" in q3:
                if any(x in n for x in ["tesla", "nvidia", "asml", "apple", "microsoft", "total", "shell", "siemens"]):
                    s += 2

            # Soft popularity bonus for famous names
            if row["name"] in FALLBACK_BRANDS:
                s += 1

            score.append(s)

        uni["score"] = score
        uni = uni.sort_values(["score", "name"], ascending=[False, True])
        # keep top-k; if sparse, pad randomly
        top = uni.head(k)
        if len(top) < k:
            others = uni[~uni.index.isin(top.index)].sample(min(k - len(top), len(uni) - len(top)), random_state=42)
            top = pd.concat([top, others])
        return top.drop(columns=["score"]).reset_index(drop=True)

    # -------------------------
    # Gift code generation
    # -------------------------
    def generate_gift_code(self, selections: List[Tuple[str, float]], lang: str = "it") -> str:
        """selections: list of (name, amount)"""
        total = int(round(sum(a for _, a in selections if a and a > 0)))
        # Build a short hash for uniqueness
        seed = f"{json.dumps(selections, sort_keys=True)}|{int(time.time())}"
        h = hashlib.sha1(seed.encode()).hexdigest()[:6].upper()
        # Compose readable slug with up to 2 brand tokens
        brands = [re.sub(r'[^A-Za-z0-9]+', '', n).upper() for n, a in selections if a and a > 0]
        brands = brands[:2] if brands else ["LOVE"]
        prefix = "REGALO" if lang == "it" else "GIFT"
        code = f"#{prefix}-{total}-{('-').join(brands)}-{h}"
        return code

    # -------------------------
    # Persistence (simple CSV)
    # -------------------------
    def save_donation(self, guest_id: str, lang: str, selections: List[Tuple[str, float]], code: str):
        rows = []
        for name, amount in selections:
            rows.append({
                "timestamp": int(time.time()),
                "guest_id": guest_id,
                "lang": lang,
                "brand": name,
                "amount": float(amount or 0),
                "code": code,
            })
        df = pd.DataFrame(rows)
        if os.path.exists(self.donations_csv):
            old = pd.read_csv(self.donations_csv)
            df = pd.concat([old, df], ignore_index=True)
        df.to_csv(self.donations_csv, index=False)

    def load_stats(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        if not os.path.exists(self.donations_csv):
            return pd.DataFrame(columns=["brand", "amount"]), pd.DataFrame(columns=["code"])
        df = pd.read_csv(self.donations_csv)
        top = df.groupby("brand", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        codes = df[["code"]].drop_duplicates()
        return top, codes



#%%
# # c_wedding_app.py
# import pandas as pd

# WIKI_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

# class WeddingApp:
#     def __init__(self, couple_names: str, iban: str):
#         self.couple_names = couple_names
#         self.iban = iban

#     def load_universe(self) -> pd.DataFrame:
#         """
#         Load the S&P 500 constituents from Wikipedia.
#         Returns DataFrame with: Ticker, Name, Sector
#         """
#         tables = pd.read_html(WIKI_SP500_URL)
#         df = tables[0].copy()
#         df = df.rename(columns={
#             "Symbol": "Ticker",
#             "Security": "Name",
#             "GICS Sector": "Sector"
#         })[["Ticker", "Name", "Sector"]]
#         df = df.drop_duplicates(subset=["Ticker"]).reset_index(drop=True)
#         return df
