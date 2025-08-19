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
        "app_title": "Gioco degli Auguri",
        "welcome_title": "Benvenuto! 🎉",
        "welcome_sub": "Trasforma il tuo regalo in simboli di buon augurio e fa si che cresca col tempo!\nNiente investimenti reali, promesso!",
        "start_quiz": "Inizia",
        "profile_title": "Step 1 • Scegli i temi",
        "to_suggestions": "Vedi aziende suggerite",
        "suggestions_title": "Step 2 • Seleziona le aziende",
        "suggestions_sub": "Spunta i simboli che vuoi regalare (puoi anche cercare).",
        "search_placeholder": "Cerca un’azienda (es. Disney, Ferrari)…",
        "to_amounts": "Conferma selezioni",
        "amounts_title": "Step 3 • \"Investi\" il tuo regalo",
        "amounts_sub": "Assegna un importo a ciascun simbolo scelto 😉",
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
        "tags_title": "Scegli i temi (puoi aprire i gruppi e selezionare più tag)",
    },
    "en": {
        "app_title": "Good Wishes Game",
        "welcome_title": "Welcome! 🎉",
        "welcome_sub": "Turn your gift into symbolic good-luck tokens (no real finance, promise!)",
        "start_quiz": "Start",
        "profile_title": "Step 1 • Pick your themes",
        "to_suggestions": "See suggested companies",
        "suggestions_title": "Step 2 • Pick companies",
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
        "tags_title": "Pick the themes you like (open groups and select multiple tags)",
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
