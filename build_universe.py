# clean_universe.py

import pandas as pd

# === 1. Lettura file originale ===
df = pd.read_csv(r"C:\Users\Gaetano\Desktop\Projects\wedding_app\data\bloomberg_universe.csv")

# La prima riga è spazzatura ("None (2456 securities)") -> la elimino
df = df.drop(0).reset_index(drop=True)

# === 2. Pulizia campi ===
# Estraggo ticker pulito (prendo solo la prima parte prima dello spazio)
df["Ticker"] = df["Ticker"].str.split().str[0]

# Market Cap numerico
df["Market Cap"] = (
    df["Market Cap"]
    .str.replace(",", "", regex=False)
    .astype(float)
)

# Normalizzo i nomi delle colonne che useremo
df.rename(
    columns={
        "Name": "Company",
        "Cntry Terrtry Of Dom": "Country",
        "GICS Sector": "GICS_Sector",
        "BICS L1 Sect Nm": "BICS_L1",
        "BICS L2 IG Nm": "BICS_L2",
        "BICS L3 Ind Nm": "BICS_L3",
    },
    inplace=True,
)

# === 3. Dizionario mapping BICS -> Friendly Tags ===
sector_mapping = {
    "Consumer Discretionary": {
        "en": ["consumer", "retail", "autos"],
        "it": ["consumi", "retail", "auto"]
    },
    "Consumer Staples": {
        "en": ["food", "beverages", "household"],
        "it": ["alimentari", "bevande", "casa"]
    },
    "Energy": {
        "en": ["oil", "gas", "energy"],
        "it": ["petrolio", "gas", "energia"]
    },
    "Financials": {
        "en": ["banks", "insurance", "finance"],
        "it": ["banche", "assicurazioni", "finanza"]
    },
    "Health Care": {
        "en": ["healthcare", "biotech", "pharma"],
        "it": ["sanità", "biotech", "farmaceutica"]
    },
    "Industrials": {
        "en": ["industrials", "manufacturing", "transport"],
        "it": ["industria", "manifattura", "trasporti"]
    },
    "Information Technology": {
        "en": ["technology", "software", "hardware"],
        "it": ["tecnologia", "software", "hardware"]
    },
    "Materials": {
        "en": ["materials", "chemicals", "metals"],
        "it": ["materiali", "chimica", "metalli"]
    },
    "Communication Services": {
        "en": ["media", "telecom", "internet"],
        "it": ["media", "telecomunicazioni", "internet"]
    },
    "Utilities": {
        "en": ["utilities", "electricity", "water"],
        "it": ["utilities", "elettricità", "acqua"]
    },
    "Real Estate": {
        "en": ["real estate", "property"],
        "it": ["immobiliare", "proprietà"]
    },
}

def map_tags_en(sector):
    return ";".join(sector_mapping.get(sector, {"en": ["other"]})["en"])

def map_tags_it(sector):
    return ";".join(sector_mapping.get(sector, {"it": ["altro"]})["it"])

df["tags_en"] = df["BICS_L1"].apply(map_tags_en)
df["tags_it"] = df["BICS_L1"].apply(map_tags_it)

# === 4. Selezione colonne finali ===
universe = df[[
    "Ticker", "Company", "Country", "BICS_L1", "BICS_L2", "BICS_L3", "tags_en", "tags_it"
]]

# === 5. Salvataggio ===
universe.to_csv(r"C:\Users\Gaetano\Desktop\Projects\wedding_app\data/universe.csv", index=False)

print(f"✅ Universe salvato in data/universe.csv con {len(universe)} aziende")
print("Shape finale:", universe.shape)
print("Settori unici:", universe["BICS_L1"].unique())
