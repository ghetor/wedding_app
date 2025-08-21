# c_wedding_app.py
from __future__ import annotations

import os
import re
import time
import json
import csv
import random
import hashlib
from typing import List, Dict, Tuple, Optional, Set

import pandas as pd

# -------------------------
# Minimal i18n dictionary
# -------------------------
I18N = {
    "it": {
        "app_title": "L'investitore intelligente!",
        "welcome_title": "Benvenuti! 🎉👋",
        "welcome_text": """
Set di argenteria? 🍴  Grandi elettrodomestici? 🧺  Valigie di ogni dimensione? 🧳

E se il tuo regalo crescesse nel tempo invece di rimanere chiuso in un armadio per gran parte dell'anno?!

La nostra idea è far si che tu possa trasformare il tuo regalo in un carrello **simbolico** di società famose su cui investire!  
.. in questo modo non solo rimarrà un regalo indimenticabile per gli sposi, ma li farà pensare a te ogni volta che guarderanno i loro investimenti!

<div style='text-align: center; font-weight: bold; font-size: 1.2rem; margin: 1em 0;'>🚫 Nessun rischio di sbagliare! 🚫</div>

<div style='
    font-family: "Georgia", serif;
    font-size: 1.1rem;
    font-style: italic;
    color: #c2185b;
    margin: 1em 0;
'>
    L'acquisto vero e proprio lo faranno gli sposi: questo è solo un gioco per rendere il pensiero più divertente 💖
</div>

### Come funziona
1) Seleziona i temi che ti ispirano (es. *Cura degli animali*, *Viaggi*, *Intelligenza Artificiale*…)  
2) Aggiungi al carrello le aziende che vuoi regalare agli sposi  
3) Dividi l'importo del tuo regalo fra le aziende che hai scelto  
4) Genera il **Codice del Regalo** e inseriscilo nella causale del bonifico  

**Ricorda**: il codice è l'unico modo che abbiamo per decodificare il tuo regalo!
""",
        "start_quiz": "Inizia",
 
    },
    "en": {
        "app_title": "The intelligent investor!",
        "welcome_title": "Welcome! 🎉👋",
        "welcome_text": """
Silverware set? 🍴  Large appliances? 🧺  Luggage of all sizes? 🧳

What if your gift could grow over time instead of staying locked in a closet for most of the year?!

Our idea is to let you transform your gift into a **symbolic** basket of famous companies to invest in!  
.. this way it won’t just be an unforgettable gift for the couple, but it will remind them of you every time they look at their investments!

<div style='text-align: center; font-weight: bold; font-size: 1.2rem; margin: 1em 0;'>🚫 No risk of getting it wrong! 🚫</div>

<div style='
    font-family: "Georgia", serif;
    font-size: 1.1rem;
    font-style: italic;
    color: #c2185b;
    margin: 1em 0;
'>
    The couple will make the real purchase: this is just a game to make your thought more fun 💖
</div>

### How it works
1) Pick the themes that inspire you (e.g. *Pets*, *Travel*, *Artificial Intelligence*…)  
2) Add the companies you want to gift the couple  
3) Split your gift amount among the chosen companies  
4) Generate the **Gift Code** and put it in the bank transfer note  

**Remember**: the code is the only way for us to decode your gift!
""",
        "start_quiz": "Start",
    },
}


# -------------------------
# Classe core
# -------------------------


class WeddingApp:
    def __init__(self, data_dir: str = ".", donations_csv: str = "donations.csv",
                 universe_csv: str = "data/universe.csv", tag_catalog_csv: str = "data/tag_catalog.csv"):
        self.data_dir = data_dir
        self.donations_csv = os.path.join(self.data_dir, donations_csv)
        self.universe_csv = os.path.join(self.data_dir, universe_csv)
        self.tag_catalog_csv = os.path.join(self.data_dir, tag_catalog_csv)
        self._universe: Optional[pd.DataFrame] = None
        self._tags: Optional[pd.DataFrame] = None
        self.random = random.Random(2025)

    # ---------- Loaders ----------
    def load_universe(self) -> pd.DataFrame:
        if self._universe is None:
            if not os.path.exists(self.universe_csv):
                raise FileNotFoundError(
                    f"Universe not found: {self.universe_csv}")
            df = pd.read_csv(self.universe_csv)
            for col in ["tags_keys", "tags_it", "tags_en"]:
                if col not in df.columns:
                    df[col] = ""
            self._universe = df
        return self._universe

    def load_tag_catalog(self) -> pd.DataFrame:
        if self._tags is not None:
            return self._tags
        if not os.path.exists(self.tag_catalog_csv):
            return pd.DataFrame(columns=["group_key", "tag_key", "label_it", "label_en", "emoji"])
        df = pd.read_csv(self.tag_catalog_csv)
        self._tags = df
        return df

    def refresh_from_disk(self) -> None:
        self._universe = None
        self._tags = None

    # ---------- Filtering ----------
    def filter_universe_by_tag_keys(self, selected: Set[str]) -> pd.DataFrame:
        uni = self.load_universe().copy()
        if not selected:
            return uni

        def any_match(keys_str: str) -> bool:
            keys = [k.strip()
                    for k in (keys_str or "").split(";") if k.strip()]
            return any(k in selected for k in keys)
        mask = uni["tags_keys"].apply(any_match)
        return uni[mask].reset_index(drop=True)

    # ---------- Display helpers ----------
    def display_tags(self, row: pd.Series, lang: str = "it") -> str:
        col = "tags_en" if lang == "en" else "tags_it"
        s = str(row.get(col, "") or "").replace(";", ", ")
        return s

    # ---------- Gift code ----------
    def generate_gift_code(self, selections: List[Tuple[str, float]], lang: str = "it") -> str:
        total_val = sum(float(a) for _, a in selections if a and float(a) > 0)
        total = int(round(total_val)) if total_val > 0 else 0
        seed = f"{json.dumps(selections, sort_keys=True)}|{int(time.time())}"
        h = hashlib.sha1(seed.encode()).hexdigest()[:6].upper()
        brands = [re.sub(r'[^A-Za-z0-9]+', '', (n or "")).upper()
                  for n, a in selections if a and float(a) > 0]
        brands = [b for b in brands if b] or ["LOVE"]
        brands = brands[:2]
        prefix = "REGALO" if lang == "it" else "GIFT"
        return f"#{prefix}-{total}-{'-'.join(brands)}-{h}"

    # ---------- Persistence ----------
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
            os.makedirs(os.path.dirname(self.donations_csv)
                        or ".", exist_ok=True)
            self._append_rows_csv(rows, self.donations_csv)
        except Exception:
            pass

    def _append_rows_csv(self, rows: List[dict], csv_path: str) -> None:
        file_exists = os.path.exists(csv_path)
        fieldnames = ["timestamp", "guest_id",
                      "lang", "brand", "amount", "code"]
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for r in rows:
                writer.writerow(r)

    # ---------- Stats ----------
    def load_stats(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        try:
            if not os.path.exists(self.donations_csv):
                return pd.DataFrame(columns=["brand", "amount"]), pd.DataFrame(columns=["code"])
            df = pd.read_csv(self.donations_csv)
            if df.empty:
                return pd.DataFrame(columns=["brand", "amount"]), pd.DataFrame(columns=["code"])
            top = df.groupby("brand", as_index=False)[
                "amount"].sum().sort_values("amount", ascending=False)
            codes = df[["code"]].drop_duplicates()
            return top, codes
        except Exception:
            return pd.DataFrame(columns=["brand", "amount"]), pd.DataFrame(columns=["code"])
