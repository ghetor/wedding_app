# c_wedding_app.py
from __future__ import annotations

import os
import re
import time
import json
import csv
import random
import hashlib
from typing import List, Dict, Tuple, Optional

import pandas as pd

# yfinance è opzionale: non la usiamo nella UI attuale, ma rimane compatibile
try:
    import yfinance as yf  # noqa: F401
except Exception:
    yf = None  # opzionale

# requests è opzionale: se manca, useremo direttamente pandas.read_html(url)
try:
    import requests
except Exception:
    requests = None

# file lock opzionale: se disponibile, riduce i rischi in scrittura concorrente
try:
    from filelock import FileLock
except Exception:
    FileLock = None


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
# Emojis e fallback brand
# -------------------------
EMOJI_MAP = {
    "Tesla": "🚗⚡", "Disney": "✨", "Coca-Cola": "🥤", "Apple": "🍏", "Nike": "👟",
    "Ferrari": "🏎️", "Nestlé": "🍫", "Airbus": "✈️", "Booking Holdings": "🌍",
    "Netflix": "🎬", "Microsoft": "🖥️", "Amazon": "📦", "Alphabet": "🔎",
    "Meta": "💬", "Shell": "🛢️", "TotalEnergies": "⚡", "ASML": "🔬",
    "Siemens": "🛠️", "LVMH": "👜", "Adidas": "👟", "PepsiCo": "🥤", "Starbucks": "☕",
    "McDonald’s": "🍟", "Airbnb": "🏡", "Spotify": "🎵", "Samsung": "📱",
    "NVIDIA": "🧠",
}

# Fallback curato (brand → (ticker, index_name))
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
    "Spotify": ("SPOT", "EU→US ADR"),
    "Samsung": ("SSNLF", "KOR Large Cap (OTC)"),
    "Airbus": ("EADSY", "EuroStoxx 50 (ADR)"),
}


class WeddingApp:
    """
    Core logic: sorgenti dati, suggerimenti, generazione codice, salvataggio e statistiche.
    """

    def __init__(self, data_dir: str = ".", donations_csv: str = "donations.csv"):
        self.data_dir = data_dir
        self.donations_csv = os.path.join(self.data_dir, donations_csv)
        self._universe: Optional[pd.DataFrame] = None  # cache
        self.random = random.Random(2025)

    # -------------------------
    # Helpers rete/file
    # -------------------------
    def _fetch_html(self, url: str, timeout: int = 8) -> Optional[str]:
        """
        Tenta di scaricare HTML con requests (se presente) altrimenti None.
        Usiamo poi pandas.read_html sul testo scaricato per maggiore controllo del timeout.
        """
        try:
            if requests is None:
                return None
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and resp.text:
                return resp.text
        except Exception:
            return None
        return None

    # -------------------------
    # Data loading (3 indici)
    # -------------------------
    def load_index_sp500(self) -> pd.DataFrame:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        try:
            html = self._fetch_html(url)
            if html:
                tables = pd.read_html(html)
            else:
                tables = pd.read_html(url)  # fallback diretto
            df = tables[0][["Security", "Symbol"]].rename(columns={"Security": "name", "Symbol": "ticker"})
            df["index"] = "S&P 500"
            return df
        except Exception:
            return pd.DataFrame()

    def load_index_nasdaq100(self) -> pd.DataFrame:
        url = "https://en.wikipedia.org/wiki/NASDAQ-100"
        try:
            html = self._fetch_html(url)
            tables = pd.read_html(html) if html else pd.read_html(url)
            # Cerca tabella con Company / Ticker
            cand = None
            for t in tables:
                cols = {str(c).strip().lower() for c in t.columns}
                if {"ticker", "company"} <= cols:
                    cand = t
                    break
            if cand is None:
                cand = tables[0]
            df = cand.rename(columns={c: str(c).strip().lower() for c in cand.columns})
            df = df[["company", "ticker"]].rename(columns={"company": "name"})
            df["index"] = "NASDAQ-100"
            return df
        except Exception:
            return pd.DataFrame()

    def load_index_eurostoxx50(self) -> pd.DataFrame:
        url = "https://en.wikipedia.org/wiki/EURO_STOXX_50"
        try:
            html = self._fetch_html(url)
            tables = pd.read_html(html) if html else pd.read_html(url)
            cand = None
            for t in tables:
                lc = [str(c).strip().lower() for c in t.columns]
                if ("company" in lc) and ("ticker" in lc or "ticker symbol" in lc):
                    cand = t
                    break
            if cand is None:
                cand = tables[0]
            df = cand.rename(columns={c: str(c).strip().lower() for c in cand.columns})
            ticker_col = "ticker" if "ticker" in df.columns else ("ticker symbol" if "ticker symbol" in df.columns else df.columns[-1])
            company_col = "company" if "company" in df.columns else df.columns[0]
            df = df[[company_col, ticker_col]].rename(columns={company_col: "name", ticker_col: "ticker"})
            df["index"] = "EuroStoxx 50"
            return df
        except Exception:
            return pd.DataFrame()

    # -------------------------
    # Universo brand combinato
    # -------------------------
    def build_universe(self, famous_only: bool = True) -> pd.DataFrame:
        """
        Combina S&P 500, NASDAQ-100, EuroStoxx50 e fa fallback sui brand famosi.
        Aggiunge emoji se disponibili. Cache in self._universe.
        """
        if self._universe is not None:
            return self._universe

        sp = self.load_index_sp500()
        ndx = self.load_index_nasdaq100()
        esx = self.load_index_eurostoxx50()

        combined = pd.concat([sp, ndx, esx], ignore_index=True).dropna()
        if not combined.empty:
            combined = combined.drop_duplicates(subset=["ticker"])
        else:
            # Fallback curato: sempre non vuoto
            data = [{"name": k, "ticker": v[0], "index": v[1]} for k, v in FALLBACK_BRANDS.items()]
            combined = pd.DataFrame(data)

        if famous_only:
            famous_names = set(FALLBACK_BRANDS.keys())
            uni = combined.copy()
            uni["is_famous"] = uni["name"].apply(lambda n: self._is_famous(n, famous_names))
            keep = uni[uni["is_famous"]]
            if keep.empty:
                keep = combined.head(min(40, len(combined)))
            combined = keep.drop(columns=["is_famous"]).reset_index(drop=True)

        combined["emoji"] = combined["name"].map(EMOJI_MAP).fillna("")
        self._universe = combined.sort_values("name").reset_index(drop=True)
        return self._universe

    def _is_famous(self, name: str, famous_names: set) -> bool:
        nm = name.lower()
        for f in famous_names:
            if f.lower() in nm or nm in f.lower():
                return True
        return name in famous_names

    # -------------------------
    # Suggerimenti basati sul quiz
    # -------------------------
    def suggestions(self, answers: Dict[str, str], k: int = 10) -> pd.DataFrame:
        uni = self.build_universe(famous_only=True).copy()
        if uni.empty:
            return pd.DataFrame(columns=["name", "ticker", "index", "emoji"])

        score_list = []
        q1 = (answers.get("q1") or "").lower()
        q2 = (answers.get("q2") or "").lower()
        q3 = (answers.get("q3") or "").lower()

        for _, row in uni.iterrows():
            s = 0
            n = str(row["name"]).lower()

            # Q1: tipo regalo
            if any(w in q1 for w in ["viaggi", "avventure", "travel", "adventure"]):
                if any(x in n for x in ["booking", "airbus", "ferrari", "tesla", "airbnb"]):
                    s += 3
            if any(w in q1 for w in ["cibo", "tradizion", "food"]):
                if any(x in n for x in ["nestlé", "nestle", "coca", "pepsi", "starbucks", "mcdon"]):
                    s += 3
            if any(w in q1 for w in ["divert", "relax", "fun", "chill"]):
                if any(x in n for x in ["disney", "netflix", "spotify"]):
                    s += 3
            if any(w in q1 for w in ["futuro", "innov", "future", "innovation"]):
                if any(x in n for x in ["tesla", "apple", "microsoft", "amazon", "alphabet", "meta", "nvidia", "asml", "samsung"]):
                    s += 3

            # Q2: valore
            if "romant" in q2 or "romantic" in q2:
                if "disney" in n or "lvmh" in n:
                    s += 2
            if any(w in q2 for w in ["energia", "energy", "sport"]):
                if any(x in n for x in ["nike", "adidas", "tesla", "total", "shell"]):
                    s += 2
            if "magia" in q2 or "magic" in q2:
                if "disney" in n:
                    s += 2
            if any(w in q2 for w in ["tecno", "tech", "modern"]):
                if any(x in n for x in ["apple", "microsoft", "amazon", "alphabet", "meta", "nvidia", "asml", "samsung"]):
                    s += 2

            # Q3: settore
            if any(w in q3 for w in ["viaggi", "travel", "trasport", "transport"]):
                if any(x in n for x in ["airbus", "booking", "airbnb", "ferrari", "tesla"]):
                    s += 2
            if any(w in q3 for w in ["food", "beverage", "cibo"]):
                if any(x in n for x in ["starbucks", "nestlé", "nestle", "coca", "pepsi", "mcdon"]):
                    s += 2
            if any(w in q3 for w in ["intratten", "entertain"]):
                if any(x in n for x in ["disney", "netflix", "spotify"]):
                    s += 2
            if any(w in q3 for w in ["energia", "innov"]):
                if any(x in n for x in ["tesla", "nvidia", "asml", "apple", "microsoft", "total", "shell", "siemens"]):
                    s += 2

            # Bonus popolarità
            if row["name"] in FALLBACK_BRANDS:
                s += 1

            score_list.append(s)

        uni["score"] = score_list
        uni = uni.sort_values(["score", "name"], ascending=[False, True])
        top = uni.head(k).drop(columns=["score"])
        if len(top) < k:
            others = uni[~uni.index.isin(top.index)].sample(min(k - len(top), max(len(uni) - len(top), 0)), random_state=42)
            top = pd.concat([top, others.drop(columns=["score"])]) if not others.empty else top
        return top.reset_index(drop=True)

    # -------------------------
    # Generazione codice regalo
    # -------------------------
    def generate_gift_code(self, selections: List[Tuple[str, float]], lang: str = "it") -> str:
        """
        selections: lista di (brand_name, amount). Somma gli importi > 0.
        Crea un codice leggibile + hash breve per unicità.
        """
        total_val = sum(float(a) for _, a in selections if a and float(a) > 0)
        total = int(round(total_val)) if total_val > 0 else 0

        # Hash breve per unicità (dipende da scelte + timestamp)
        seed = f"{json.dumps(selections, sort_keys=True)}|{int(time.time())}"
        h = hashlib.sha1(seed.encode()).hexdigest()[:6].upper()

        # Slug brand (max 2)
        brands = [re.sub(r'[^A-Za-z0-9]+', '', (n or "")).upper() for n, a in selections if a and float(a) > 0]
        brands = [b for b in brands if b] or ["LOVE"]
        brands = brands[:2]
        prefix = "REGALO" if lang == "it" else "GIFT"

        code = f"#{prefix}-{total}-{'-'.join(brands)}-{h}"
        return code

    # -------------------------
    # Salvataggio donazioni
    # -------------------------
    def save_donation(self, guest_id: str, lang: str, selections: List[Tuple[str, float]], code: str) -> None:
        """
        Scrive su CSV in append. Usa file lock se disponibile.
        In caso di errore, non solleva eccezioni (best-effort).
        """
        try:
            rows = []
            ts = int(time.time())
            for name, amount in selections:
                try:
                    amt = float(amount or 0)
                except Exception:
                    amt = 0.0
                rows.append({
                    "timestamp": ts,
                    "guest_id": guest_id,
                    "lang": lang,
                    "brand": name,
                    "amount": amt,
                    "code": code,
                })

            if not rows:
                return

            # Assicura esistenza dir
            os.makedirs(os.path.dirname(self.donations_csv) or ".", exist_ok=True)

            lock_path = self.donations_csv + ".lock"
            if FileLock is not None:
                with FileLock(lock_path, timeout=4):
                    self._append_rows_csv(rows, self.donations_csv)
            else:
                # Fallback senza lock
                self._append_rows_csv(rows, self.donations_csv)
        except Exception:
            # Non blocchiamo l'app
            pass

    def _append_rows_csv(self, rows: List[dict], csv_path: str) -> None:
        file_exists = os.path.exists(csv_path)
        fieldnames = ["timestamp", "guest_id", "lang", "brand", "amount", "code"]
        # Apri in append + crea header se nuovo
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for r in rows:
                writer.writerow(r)

    # -------------------------
    # Statistiche
    # -------------------------
    def load_stats(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Ritorna:
          - top: DataFrame con colonne [brand, amount] ordinate desc
          - codes: DataFrame con colonna [code] unici
        """
        try:
            if not os.path.exists(self.donations_csv):
                return pd.DataFrame(columns=["brand", "amount"]), pd.DataFrame(columns=["code"])
            df = pd.read_csv(self.donations_csv)
            if df.empty:
                return pd.DataFrame(columns=["brand", "amount"]), pd.DataFrame(columns=["code"])
            # Aggrega
            top = df.groupby("brand", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
            codes = df[["code"]].drop_duplicates()
            return top, codes
        except Exception:
            return pd.DataFrame(columns=["brand", "amount"]), pd.DataFrame(columns=["code"])
