# app.py
import streamlit as st
import pandas as pd
from c_wedding_app import WeddingApp, I18N
from uuid import uuid4

# ...st.set_page_config...

if "selected_tags" not in st.session_state:
    st.session_state.selected_tags = set()
if "tag_catalog" not in st.session_state:
    st.session_state.tag_catalog = None

app = WeddingApp()
if st.session_state.tag_catalog is None:
    st.session_state.tag_catalog = app.load_tag_catalog()


st.set_page_config(page_title="Wedding App", page_icon="💍", layout="centered", initial_sidebar_state="collapsed")

# -------------------------
# Init
# -------------------------
if "lang" not in st.session_state:
    st.session_state.lang = "it"
if "step" not in st.session_state:
    st.session_state.step = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "suggested" not in st.session_state:
    st.session_state.suggested = pd.DataFrame()
if "picked" not in st.session_state:
    st.session_state.picked = []
if "amounts" not in st.session_state:
    st.session_state.amounts = {}
if "gift_code" not in st.session_state:
    st.session_state.gift_code = ""

app = WeddingApp()
T = I18N[st.session_state.lang]

# -------------------------
# Header + Language toggle
# -------------------------
colA, colB = st.columns([6,1])
with colA:
    st.title(T["app_title"])
with colB:
    lang_choice = st.radio(
        "",
        options=["it","en"],
        index=0 if st.session_state.lang=="it" else 1,
        format_func=lambda x: "🇮🇹" if x=="it" else "🇬🇧",
        horizontal=True,
        label_visibility="collapsed"
    )
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        T = I18N[st.session_state.lang]

st.divider()

# -------------------------
# Step navigation helpers
# -------------------------
def goto(step:int):
    st.session_state.step = step

def reset_all():
    for k in ["answers","suggested","picked","amounts","gift_code"]:
        st.session_state[k] = {} if k=="answers" else (pd.DataFrame() if k=="suggested" else ([] if k in ["picked"] else ({} if k=="amounts" else "")))
    st.session_state.step = 0

# -------------------------
# Step 0 – Welcome
# -------------------------
if st.session_state.step == 0:
    st.subheader(T["welcome_title"])
    st.write(T["welcome_sub"])
    st.info(T["instructions_safe"])
    st.button(T["start_quiz"], type="primary", on_click=lambda: goto(1))

# -------------------------
# Step 1 – Selezione temi (tag)
# -------------------------
if st.session_state.step == 1:
    st.header(I18N[st.session_state.lang]["profile_title"])
    st.caption(I18N[st.session_state.lang]["tags_title"])

    tags = st.session_state.tag_catalog
    if tags is None or tags.empty:
        st.error("Manca data/tag_catalog.csv")
    else:
        # Render per gruppi
        selected = set(st.session_state.selected_tags)
        lang = st.session_state.lang
        for grp, dfgrp in tags.groupby("group_key"):
            label_group = grp.capitalize()
            with st.expander(f"{label_group}"):
                for _, r in dfgrp.iterrows():
                    label = (r["label_it"] if lang=="it" else r["label_en"])
                    emoji = str(r.get("emoji","") or "")
                    key = r["tag_key"]
                    ck = st.checkbox(f"{emoji} {label}".strip(), value=(key in selected), key=f"tag_{key}")
                    if ck:
                        selected.add(key)
                    else:
                        selected.discard(key)
        st.session_state.selected_tags = selected
        st.button(I18N[st.session_state.lang]["to_suggestions"], type="primary", on_click=lambda: goto(2))


# -------------------------
# Step 2 – Aziende filtrate per tag
# -------------------------
if st.session_state.step == 2:
    st.header(I18N[st.session_state.lang]["suggestions_title"])
    st.caption(I18N[st.session_state.lang]["suggestions_sub"])

    df_all = app.filter_universe_by_tag_keys(st.session_state.selected_tags)

    q = st.text_input(I18N[st.session_state.lang]["search_placeholder"])
    df = df_all
    if q:
        mask = df["name"].str.contains(q, case=False, na=False)
        df = df[mask]

    picked = set(st.session_state.picked)
    for _, row in df.iterrows():
        tags_str = app.display_tags(row, lang=st.session_state.lang)
        label = f"{row['name']} {row.get('emoji','')} ({row['ticker']}) — {tags_str}"
        ck = st.checkbox(label, value=(row['name'] in picked), key=f"pick_{row['ticker']}")
        if ck:
            picked.add(row['name'])
        else:
            picked.discard(row['name'])
    st.session_state.picked = sorted(list(picked))

    cols = st.columns(2)
    with cols[0]:
        st.button(I18N[st.session_state.lang]["back"], on_click=lambda: goto(1))
    with cols[1]:
        st.button(I18N[st.session_state.lang]["to_amounts"], type="primary", on_click=lambda: goto(3), disabled=len(st.session_state.picked)==0)


# -------------------------
# Step 3 – Amounts & Total
# -------------------------
if st.session_state.step == 3:
    st.header(T["amounts_title"])
    st.caption(T["amounts_sub"])
    if not st.session_state.picked:
        st.warning("Nessuna selezione. Torna indietro per scegliere." if st.session_state.lang=="it"
                   else "No picks yet. Go back to choose.")
    else:
        # Init default amounts if missing
        for name in st.session_state.picked:
            st.session_state.amounts.setdefault(name, 0.0)

        for name in st.session_state.picked:
            col1, col2 = st.columns([2,1])
            with col1:
                emoji = app.build_universe().set_index("name").get("emoji", {}).get(name, "")
                st.write(f"**{name}** {emoji}")
            with col2:
                amt = st.number_input("€", min_value=0.0, step=5.0, value=float(st.session_state.amounts.get(name, 0.0)), key=f"amt_{name}")
                st.session_state.amounts[name] = amt

        total = sum(st.session_state.amounts.values())
        st.markdown(
            f"### {T['total']}: **€ {total:,.2f}**".replace(",", "X").replace(".", ",").replace("X", ".")
            if st.session_state.lang=="it"
            else f"### {T['total']}: **€ {total:,.2f}**"
        )
        st.info(T["instructions_safe"])

        colA, colB, colC = st.columns([1,1,1])
        with colA:
            st.button(T["back"], on_click=lambda: goto(2))
        with colB:
            if st.button(T["generate_code"], type="primary"):
                # Build selections list
                selections = [(name, st.session_state.amounts[name]) for name in st.session_state.picked if st.session_state.amounts[name] > 0]
                code = app.generate_gift_code(selections, lang=st.session_state.lang)
                st.session_state.gift_code = code

                # Persist a simple record (anonymous guest_id by session)
                guest_id = st.session_state.get("_guest_id")
                if not guest_id:
                    guest_id = uuid4().hex[:10]   # <-- fix: non usiamo hash(dict)
                    st.session_state["_guest_id"] = guest_id

                app.save_donation(guest_id, st.session_state.lang, selections, code)
                goto(4)
        with colC:
            st.button(T["reset"], on_click=reset_all)

# -------------------------
# Step 4 – Gift Code + Stats
# -------------------------
if st.session_state.step == 4:
    st.success(T["your_code"])
    st.code(st.session_state.gift_code or "—", language=None)
    st.caption(T["copy_hint"])

    st.divider()
    st.subheader(T["stats_title"])
    top, _codes = app.load_stats()

    c1, c2 = st.columns(2)
    with c1:
        st.metric(T["total_symbols"], f"{len(top)}")
    with c2:
        total_amount = float(top["amount"].sum()) if not top.empty else 0.0
        label_total = T["total"] if st.session_state.lang=="en" else "Somma importi (simbolici)"
        st.metric(label_total, f"€ {total_amount:,.2f}")

    if not top.empty:
        top_display = top.rename(columns={"brand": T["top_brands"], "amount": "€"})
        st.dataframe(top_display, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.button(T["back"], on_click=lambda: goto(3))
    with col2:
        st.button("🏁", help="Fine")

# Footer reassurance
st.write("")
st.caption("© 2025 • No real investing here — only symbolic good wishes 💖")


 #%%

# # app.py
# import streamlit as st
# import pandas as pd
# from c_wedding_app import WeddingApp

# # ---- basic config ----
# st.set_page_config(page_title="Wedding Stock Gift (MVP)", page_icon="💍", layout="wide")

# COUPLE_NAMES = "Your Names Here"
# IBAN = "YOUR-IBAN-HERE"
# app = WeddingApp(COUPLE_NAMES, IBAN)

# # ---- sidebar navigation ----
# st.sidebar.title("Navigation")
# page = st.sidebar.radio("Go to", ["Welcome", "Select Stocks (MVP)"])

# st.sidebar.markdown("---")
# st.sidebar.markdown(f"**Couple:** {COUPLE_NAMES}")
# st.sidebar.markdown(f"**IBAN:** `{IBAN}`")

# # ---- pages ----
# if page == "Welcome":
#     st.title("💍 Wedding Stock Gift App (MVP)")
#     st.write("""
# **This is a fun way to make the money gifts a bit less boring, we want to ask you few questions and let you select the companies that you like!**
# You will then receive a code to include in the bank transfer so that we'll know what's your investment choice!
# **No worries, you won't have to make the transaction, but if you like you'll receive an order confirmation dropping your email!**
#     """)
#     st.info("This minimal version loads the S&P 500 list from Wikipedia and lets you filter by sector. Prices/charts come next.")

# else:  # Select Stocks (MVP)
#     st.header("📈 Select Stocks (MVP)")
#     with st.spinner("Loading S&P 500 list from Wikipedia…"):
#         df = app.load_universe()

#     # Sector filter + search
#     sectors = sorted(df["Sector"].unique().tolist())
#     chosen = st.multiselect("Filter by sector", sectors, default=sectors)
#     q = st.text_input("Search by ticker or company")
#     if chosen:
#         df = df[df["Sector"].isin(chosen)]
#     if q:
#         ql = q.lower()
#         df = df[df["Ticker"].str.lower().str.contains(ql) | df["Name"].str.lower().str.contains(ql)]

#     st.dataframe(df.reset_index(drop=True), use_container_width=True)
#     st.caption("MVP: just a sector/search browser. We’ll add prices, share selection, and codes next.")



