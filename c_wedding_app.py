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
# Emoji di default (usate se non già nel CSV)
# -------------------------
EMOJI_MAP = {
    "Tesla": "🚗⚡", "Disney": "✨", "Coca-Cola": "🥤", "Apple": "🍏", "Nike": "👟",
    "Ferrari": "🏎️", "Nestlé": "🍫", "Airbus": "✈️", "Booking Holdings": "🌍",
    "Netflix": "🎬", "Microsoft": "🖥️", "Amazon": "📦", "Alphabet": "🔎",
    "Meta": "💬", "Shell": "🛢️", "TotalEnergies": "⚡", "ASML": "🔬",
    "Siemens": "🛠️", "LVMH": "👜", "Adidas": "👟", "PepsiCo": "🥤", "Starbucks": "☕",
    "McDonald’s": "🍟", "Airbnb": "🏡", "Spotify": "🎵", "Samsung": "📱", "NVIDIA": "🧠",
}

# Fallback (se il CSV non esiste proprio)
FALLBACK_BRANDS = {
    "Apple": ("AAPL", "USA", "Information Technology", "Consumer Electronics"),
    "Microsoft": ("MSFT", "USA", "Information Technology", "Software"),
    "Amazon": ("AMZN", "USA", "Consumer Discretionary", "E-commerce & Cloud"),
    "Alphabet": ("GOOGL", "USA", "Communication Services", "Search & Ads"),
    "Meta": ("META", "USA", "Communication Services", "Social Media"),
    "Tesla": ("TSLA", "USA", "Consumer Discretionary", "Automobiles (EVs)"),
    "NVIDIA": ("NVDA", "USA", "Information Technology", "Semiconductors"),
    "Netflix": ("NFLX", "USA", "Communication Services", "Streaming"),
    "Disney": ("DIS", "USA", "Communication Services", "Entertainment"),
    "Coca-Cola": ("KO", "USA", "Consumer Staples", "Beverages"),
    "PepsiCo": ("PEP", "USA", "Consumer Staples", "Beverages & Snacks"),
    "Nike": ("NKE", "USA", "Consumer Discretionary", "Apparel & Footwear"),
    "McDonald’s": ("MCD", "USA", "Consumer Discretionary", "Fast Food"),
    "Starbucks": ("SBUX", "USA", "Consumer Discretionary", "Coffeehouses"),
    "Airbnb": ("ABNB", "USA", "Consumer Discretionary", "Lodging / OTA"),
    "Booking Holdings": ("BKNG", "USA", "Consumer Discretionary", "Online Travel Agency"),
    "ASML": ("ASML", "Netherlands", "Information Technology", "Semiconductor Equipment"),
    "Siemens": ("SIEGY", "Germany", "Industrials", "Conglomerate / Automation"),
    "LVMH": ("LVMUY", "France", "Consumer Discretionary", "Luxury Goods"),
    "Nestlé": ("NSRGY", "Switzerland", "Consumer Staples", "Packaged Foods & Beverages"),
    "TotalEnergies": ("TTE", "France", "Energy", "Integrated Oil & Gas"),
    "Shell": ("SHEL", "UK", "Energy", "Integrated Oil & Gas"),
    "Adidas": ("ADDYY", "Germany", "Consumer Discretionary", "Apparel & Footwear"),
    "Spotify": ("SPOT", "Sweden", "Communication Services", "Music Streaming"),
    "Ferrari": ("RACE", "Italy", "Consumer Discretionary", "Automobiles (Luxury)"),
    "Airbus": ("EADSY", "Netherlands", "Industrials", "Aerospace & Defense"),
    "Samsung": ("SSNLF", "South Korea", "Information Technology", "Consumer Electronics"),
}

class WeddingApp:
    """
    Core logic: legge un CSV statico con le aziende.
    Default path: data/universe.csv (puoi sostituirlo nel costruttore).
    Nessuno scraping → avvii rapidissimi.
    """

    def __init__(self, data_dir: str = ".", donations_csv: str = "donations.csv", universe_csv: str = "data/universe.csv"):
        self.data_dir = data_dir
        self.donations_csv = os.path.join(self.data_dir, donations_csv)
        self.universe_csv = os.path.join(self.data_dir, universe_csv) if not os.path.isabs(universe_csv) else universe_csv
        self._universe: Optional[pd.DataFrame] = None
        self.random = random.Random(2025)

    # -------------------------
    # Caricamento universo (CSV statico)
    # -------------------------
    def load_universe_csv(self) -> pd.DataFrame:
        """
        Legge il CSV statico (richieste colonne minime: name, ticker).
        Colonne opzionali usate se presenti: index, country, sector, subsector, emoji.
        """
        try:
            if os.path.exists(self.universe_csv):
                df = pd.read_csv(self.universe_csv)
                # Normalizza colonne minime
                cols = {c.lower(): c for c in df.columns}
                # Ensure required
                if "name" not in [c.lower() for c in df.columns] or "ticker" not in [c.lower() for c in df.columns]:
                    return pd.DataFrame()
                # Rename robusto
                rename_map = {}
                for std in ["name", "ticker", "index", "country", "sector", "subsector", "emoji"]:
                    if std not in df.columns and std in cols:
                        rename_map[cols[std]] = std
                # But if case-insensitive match exists, fix it
                for c in list(df.columns):
                    lc = c.lower()
                    if lc in ["name","ticker","index","country","sector","subsector","emoji"] and c != lc:
                        rename_map[c] = lc
                if rename_map:
                    df = df.rename(columns=rename_map)
                # Fill optional
                for opt in ["index","country","sector","subsector","emoji"]:
                    if opt not in df.columns:
                        df[opt] = ""
                # Map emoji fallback se vuoto
                df["emoji"] = df.apply(lambda r: (r["emoji"] if isinstance(r["emoji"], str) and r["emoji"] else EMOJI_MAP.get(str(r["name"]), "")), axis=1)
                # Ordina e de-dup
                df = df.dropna(subset=["name","ticker"]).drop_duplicates(subset=["ticker"]).sort_values("name").reset_index(drop=True)
                return df[["name","ticker","index","country","sector","subsector","emoji"]]
        except Exception:
            pass
        return pd.DataFrame()

    def build_universe(self, famous_only: bool = True) -> pd.DataFrame:
        """
        Usa il CSV se presente, altrimenti fallback curato.
        famous_only è ignorato (il CSV è già curato).
        """
        if self._universe is not None:
            return self._universe

        df = self.load_universe_csv()
        if df.empty:
            # Fallback minimo
            data = []
            for name, (ticker, country, sector, subsector) in FALLBACK_BRANDS.items():
                data.append({
                    "name": name,
                    "ticker": ticker,
                    "index": "Curated",
                    "country": country,
                    "sector": sector,
                    "subsector": subsector,
                    "emoji": EMOJI_MAP.get(name, ""),
                })
            df = pd.DataFrame(data)

        self._universe = df
        return self._universe

    def refresh_universe_from_disk(self) -> None:
        """Ricarica il CSV (utile se lo aggiorni senza riavviare l'app)."""
        self._universe = None
        _ = self.build_universe()

    # -------------------------
    # Suggerimenti (usa settore/subsettore + parole chiave)
    # -------------------------
    def suggestions(self, answers: Dict[str, str], k: int = 10) -> pd.DataFrame:
        uni = self.build_universe().copy()
        if uni.empty:
            return pd.DataFrame(columns=["name","ticker","index","emoji"])

        q1 = (answers.get("q1") or "").lower()
        q2 = (answers.get("q2") or "").lower()
        q3 = (answers.get("q3") or "").lower()

        def sector_match(row) -> int:
            s = 0
            name = str(row["name"]).lower()
            sector = str(row.get("sector","")).lower()
            sub = str(row.get("subsector","")).lower()

            # Mappature leggere dal quiz
            # Q1: tipo regalo
            if any(w in q1 for w in ["viaggi", "adventure", "travel", "avventure"]):
                if any(x in sub for x in ["lodging", "travel", "aerospace"]) or any(x in name for x in ["booking", "airbnb", "airbus", "ferrari", "tesla"]):
                    s += 3
            if any(w in q1 for w in ["cibo", "food", "tradizion"]):
                if "staple" in sector or any(x in sub for x in ["beverage", "coffee", "food"]) or any(x in name for x in ["nestlé","nestle","coca","pepsi","starbucks","mcdon"]):
                    s += 3
            if any(w in q1 for w in ["divert", "relax", "fun", "chill"]):
                if any(x in sub for x in ["streaming","entertainment","music"]) or any(x in name for x in ["disney","netflix","spotify"]):
                    s += 3
            if any(w in q1 for w in ["futuro","future","innov"]):
                if "information technology" in sector or any(x in name for x in ["tesla","nvidia","asml","apple","microsoft","samsung","alphabet","meta","amazon"]):
                    s += 3

            # Q2: valori
            if "romant" in q2 or "romantic" in q2:
                if "disney" in name or "lvmh" in name:
                    s += 2
            if any(w in q2 for w in ["energia","energy","sport"]):
                if any(x in name for x in ["nike","adidas","tesla","total","shell"]):
                    s += 2
            if "magia" in q2 or "magic" in q2:
                if "disney" in name:
                    s += 2
            if any(w in q2 for w in ["tecno","tech","modern"]):
                if "information technology" in sector or any(x in name for x in ["apple","microsoft","amazon","alphabet","meta","nvidia","asml","samsung"]):
                    s += 2

            # Q3: settore
            if any(w in q3 for w in ["viaggi","travel","trasport","transport"]):
                if any(x in name for x in ["airbus","booking","airbnb","ferrari","tesla"]) or any(x in sub for x in ["aerospace","lodging","automobile"]):
                    s += 2
            if any(w in q3 for w in ["food","beverage","cibo"]):
                if "staple" in sector or any(x in sub for x in ["beverage","coffee","food"]):
                    s += 2
            if any(w in q3 for w in ["intratten","entertain"]):
                if any(x in sub for x in ["streaming","entertainment","music"]):
                    s += 2
            if any(w in q3 for w in ["energia","innov"]):
                if "energy" in sector or "information technology" in sector:
                    s += 2

            # Bonus popolarità: emoji presente = brand noto
            if str(row.get("emoji","")).strip():
                s += 1
            return s

        uni["score"] = uni.apply(sector_match, axis=1)
        uni = uni.sort_values(["score", "name"], ascending=[False, True])
        top = uni.head(k).drop(columns=["score"])
        if len(top) < k:
            others = uni[~uni.index.isin(top.index)].sample(min(k - len(top), max(len(uni) - len(top), 0)), random_state=42)
            if not others.empty:
                top = pd.concat([top, others.drop(columns=["score"])])
        return top.reset_index(drop=True)[["name","ticker","index","emoji"]]

    # -------------------------
    # Generazione codice regalo
    # -------------------------
    def generate_gift_code(self, selections: List[Tuple[str, float]], lang: str = "it") -> str:
        total_val = sum(float(a) for _, a in selections if a and float(a) > 0)
        total = int(round(total_val)) if total_val > 0 else 0
        seed = f"{json.dumps(selections, sort_keys=True)}|{int(time.time())}"
        h = hashlib.sha1(seed.encode()).hexdigest()[:6].upper()
        brands = [re.sub(r'[^A-Za-z0-9]+', '', (n or "")).upper() for n, a in selections if a and float(a) > 0]
        brands = [b for b in brands if b] or ["LOVE"]
        brands = brands[:2]
        prefix = "REGALO" if lang == "it" else "GIFT"
        return f"#{prefix}-{total}-{'-'.join(brands)}-{h}"

    # -------------------------
    # Salvataggio donazioni (CSV append + best-effort)
    # -------------------------
    def save_donation(self, guest_id: str, lang: str, selections: List[Tuple[str, float]], code: str) -> None:
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
            os.makedirs(os.path.dirname(self.donations_csv) or ".", exist_ok=True)
            self._append_rows_csv(rows, self.donations_csv)
        except Exception:
            pass

    def _append_rows_csv(self, rows: List[dict], csv_path: str) -> None:
        file_exists = os.path.exists(csv_path)
        fieldnames = ["timestamp", "guest_id", "lang", "brand", "amount", "code"]
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
        try:
            if not os.path.exists(self.donations_csv):
                return pd.DataFrame(columns=["brand", "amount"]), pd.DataFrame(columns=["code"])
            df = pd.read_csv(self.donations_csv)
            if df.empty:
                return pd.DataFrame(columns=["brand", "amount"]), pd.DataFrame(columns=["code"])
            top = df.groupby("brand", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
            codes = df[["code"]].drop_duplicates()
            return top, codes
        except Exception:
            return pd.DataFrame(columns=["brand", "amount"]), pd.DataFrame(columns=["code"])
