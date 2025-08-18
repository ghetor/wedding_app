# -*- coding: utf-8 -*-
"""
Created on Thu Aug 14 08:33:36 2025

@author: Gaetano
"""

import streamlit as st
from c_wedding_app import WeddingApp
import pandas as pd
import matplotlib.pyplot as plt

app = WeddingApp()

st.set_page_config(page_title="Wedding Portfolio App", layout="wide")

# Sidebar navigation
step = st.sidebar.radio("Step", ["Welcome", "Quiz", "Select Stocks", "Summary"])

if step == "Welcome":
    st.title("Welcome to Our Wedding Portfolio Game!")
    st.write("""
    This is a fun way to make the money gifts a bit less boring.
    We'll ask you a few questions and let you select the companies that you like!
    You will then receive a code to include in the bank transfer so that we'll know
    what's your investment choice! No worries, you won't have to make the transaction,
    but if you like you'll receive an order confirmation dropping your email!
    """)

elif step == "Quiz":
    st.header("Quick Quiz to Guide Your Choices")
    ans1 = st.selectbox("Pick your vibe:", ["tech", "green", "classic"])
    ans2 = st.selectbox("Pick a style:", ["tech", "green", "classic"])
    answers = [ans1, ans2]
    sectors = app.sectors_from_quiz(answers)
    st.success(f"Suggested sectors for you: {', '.join(sectors)}")

elif step == "Select Stocks":
    st.header("Select Stocks to Gift")
    df = app.load_sp500()
    tickers = df['Ticker'].tolist()
    prices = app.get_last_prices(tickers)

    sector_filter = st.multiselect("Filter sectors", df['Sector'].unique())
    if sector_filter:
        df = df[df['Sector'].isin(sector_filter)]

    selected = []
    for idx, row in df.iterrows():
        with st.expander(f"{row['Name']} ({row['Ticker']}) - Sector: {row['Sector']}"):
            st.write(f"Current price: ${prices.get(row['Ticker'], 'N/A'):.2f}")
            history = app.get_history(row['Ticker'])
            st.line_chart(history)
            shares = st.number_input("How many shares to gift?", min_value=0, value=0, step=1, key=row['Ticker'])
            if shares > 0:
                selected.append((row['Ticker'], shares))

    st.session_state['selections'] = selected
    total = sum(prices[t]*s for t,s in selected if t in prices)
    st.write(f"Estimated total value: ${total:.2f}")

elif step == "Summary":
    st.header("Summary & Transfer Code")
    selections = st.session_state.get('selections', [])
    if not selections:
        st.warning("No stocks selected yet.")
    else:
        code = app.encode_transfer_code(selections)
        st.write(f"Your transfer code: **{code}**")
        st.write(f"Total value: ${sum([app.get_last_prices([t])[t]*s for t,s in selections]):.2f}")
        iban = "DE89 3704 0044 0532 0130 00"
        st.write(f"IBAN: {iban}")

        df_summary = pd.DataFrame(selections, columns=["Ticker", "Shares"])
        csv = df_summary.to_csv(index=False).encode()
        st.download_button("Download CSV receipt", csv, "gift_summary.csv", "text/csv")

        email = st.text_input("Optional: enter your email to receive confirmation")
        if email:
            st.success(f"Thanks! We'll send a confirmation to {email}")
