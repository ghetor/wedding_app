# app.py
import streamlit as st
import pandas as pd
from c_wedding_app import WeddingApp, I18N

app = WeddingApp()

st.set_page_config(page_title="Wedding App", page_icon="💍", layout="centered")

if "step" not in st.session_state:
    st.session_state.step = 0
if "lang" not in st.session_state:
    st.session_state.lang = "it"
if "picked" not in st.session_state:
    st.session_state.picked = []
if "amounts" not in st.session_state:
    st.session_state.amounts = {}
if "gift_code" not in st.session_state:
    st.session_state.gift_code = None

T = I18N[st.session_state.lang]

# ---------- Header + Language toggle ----------
colA, colB = st.columns([4,1])
with colA:
    st.title(T["app_title"])
with colB:
    lang = st.selectbox(
        "", 
        options=[("it","🇮🇹"), ("en","🇬🇧")],
        index=0 if st.session_state.lang=="it" else 1,
        format_func=lambda x: x[1],
        key="lang_select",
    )
    if lang[0] != st.session_state.lang:
        st.session_state.lang = lang[0]
        T = I18N[st.session_state.lang]
st.divider()

def goto(step): st.session_state.step = step

# ---------- Step 0 Welcome ----------
if st.session_state.step == 0:
    st.header(T["welcome_title"])
    st.write(T["welcome_sub"])
    st.button(T["start_quiz"], on_click=lambda: goto(1), type="primary")

# ---------- Step 1 Tags ----------
elif st.session_state.step == 1:
    st.header(T["profile_title"])
    tag_catalog = app.load_tag_catalog()
    lang = st.session_state.lang
    grouped = {}
    for _, row in tag_catalog.iterrows():
        g = row["group_key"]
        grouped.setdefault(g, []).append(row)
    selected = set()
    for g, rows in grouped.items():
        with st.expander(g):
            for r in rows:
                label = f"{r['emoji']} {r['label_it'] if lang=='it' else r['label_en']}"
                if st.checkbox(label, key=f"tag_{r['tag_key']}"):
                    selected.add(r["tag_key"])
    st.session_state.selected_tags = selected
    st.button(T["to_suggestions"], on_click=lambda: goto(2), type="primary")

# ---------- Step 2 Companies ----------
elif st.session_state.step == 2:
    st.header(T["suggestions_title"])
    st.caption(T["suggestions_sub"])
    df = app.filter_universe_by_tag_keys(st.session_state.get("selected_tags", set()))
    if df.empty:
        st.warning("Nessuna azienda trovata." if st.session_state.lang=="it" else "No companies found.")
    else:
        search = st.text_input(T["search_placeholder"])
        if search:
            df = df[df["Company"].str.contains(search, case=False, na=False)]
        picks = []
        for _, row in df.iterrows():
            label = f"{row['Company']} ({row['Ticker']}) • {app.display_tags(row, st.session_state.lang)}"
            if st.checkbox(label, key=f"pick_{row['Ticker']}"):
                picks.append(row["Company"])
        st.session_state.picked = picks
    col1, col2 = st.columns(2)
    with col1:
        st.button(T["back"], on_click=lambda: goto(1))
    with col2:
        st.button(T["to_amounts"], on_click=lambda: goto(3), type="primary")

# ---------- Step 3 Amounts ----------
elif st.session_state.step == 3:
    st.header(T["amounts_title"])
    st.caption(T["amounts_sub"])
    if not st.session_state.picked:
        st.warning("Nessuna selezione." if st.session_state.lang=="it" else "No picks yet.")
    else:
        for name in st.session_state.picked:
            st.session_state.amounts.setdefault(name, 0.0)
            st.number_input(name, min_value=0.0, step=5.0,
                            value=float(st.session_state.amounts[name]),
                            key=f"amt_{name}")
            st.session_state.amounts[name] = st.session_state[f"amt_{name}"]
        total = sum(st.session_state.amounts.values())
        st.markdown(f"### {T['total']}: € {total:,.2f}")
        st.info(T["instructions_safe"])
        col1, col2 = st.columns(2)
        with col1:
            st.button(T["back"], on_click=lambda: goto(2))
        with col2:
            if st.button(T["generate_code"], type="primary"):
                selections = [(n, st.session_state.amounts[n]) for n in st.session_state.picked if st.session_state.amounts[n]>0]
                code = app.generate_gift_code(selections, st.session_state.lang)
                st.session_state.gift_code = code
                guest_id = str(hash(str(selections)))[:10]
                app.save_donation(guest_id, st.session_state.lang, selections, code)
                goto(4)

# ---------- Step 4 Gift code + Stats ----------
elif st.session_state.step == 4:
    st.header(T["your_code"])
    st.code(st.session_state.gift_code or "")
    st.caption(T["copy_hint"])
    st.divider()
    st.subheader(T["stats_title"])
    top, codes = app.load_stats()
    if not top.empty:
        st.bar_chart(top.set_index("brand"))
    st.button(T["reset"], on_click=lambda: st.session_state.clear())
