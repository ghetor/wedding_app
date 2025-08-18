# -*- coding: utf-8 -*-
"""
Created on Mon Aug 18 18:37:44 2025

@author: Gaetano
"""

# pages/1_Hall_of_Fame.py
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# --- robust import for local modules (so it works on Streamlit Cloud too) ---
ROOT = Path(__file__).resolve().parents[1]  # repo root (folder sopra /pages)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from c_wedding_app import WeddingApp, I18N
except Exception as e:
    st.set_page_config(page_title="Hall of Fame • Wedding App", page_icon="🏆", layout="centered")
    st.error(f"Impossibile importare c_wedding_app.py: {e}")
    st.stop()

st.set_page_config(page_title="Hall of Fame • Wedding App", page_icon="🏆", layout="centered")

# Lingua condivisa con l'app principale
if "lang" not in st.session_state:
    st.session_state.lang = "it"
T = I18N[st.session_state.lang]

# Header + cambio lingua
col1, col2 = st.columns([3,2])
with col1:
    st.title("🏆 Hall of Fame")
with col2:
    st.selectbox(
        T["lang_label"],
        options=[("it", "🇮🇹 Italiano"), ("en", "🇬🇧 English")],
        index=0 if st.session_state.lang == "it" else 1,
        format_func=lambda x: x[1],
        key="lang_select_hof",
    )
    if st.session_state.lang_select_hof[0] != st.session_state.lang:
        st.session_state.lang = st.session_state.lang_select_hof[0]
        T = I18N[st.session_state.lang]

st.caption(
    "Classifica simpatica dei simboli regalati (solo gioco, nessuna finanza vera!)."
    if st.session_state.lang == "it"
    else "A friendly leaderboard of gifted tokens (just a game, no real finance!)."
)

app = WeddingApp()
top, codes = app.load_stats()

if top.empty:
    st.info(
        "Ancora nessun simbolo regalato… Sarai il primo? ✨"
        if st.session_state.lang == "it"
        else "No tokens yet… Be the first! ✨"
    )
else:
    total_amount = float(top["amount"].sum())
    formatted_amount = f"€ {total_amount:,.2f}"
    if st.session_state.lang == "it":
        formatted_amount = formatted_amount.replace(",", "X").replace(".", ",").replace("X", ".")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Brand unici" if st.session_state.lang == "it" else "Unique brands", f"{top['brand'].nunique()}")
    with c2:
        st.metric("Totale simbolico" if st.session_state.lang == "it" else "Symbolic total", formatted_amount)
    with c3:
        st.metric("Codici generati" if st.session_state.lang == "it" else "Gift codes", f"{len(codes)}")

    st.subheader("Top 10")
    chart_df = top.head(10).set_index("brand")["amount"]
    st.bar_chart(chart_df)

    label_brand = "Brand"
    label_amount = "€"
    table = top.rename(columns={"brand": label_brand, "amount": label_amount})
    st.dataframe(table, use_container_width=True, hide_index=True)

st.page_link("app.py", label="⬅️ Torna all’app" if st.session_state.lang == "it" else "⬅️ Back to app")
st.caption("© 2025 • Symbolic gifts only 💖")
