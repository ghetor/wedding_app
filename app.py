# app.py
import streamlit as st
import pandas as pd
from c_wedding_app import WeddingApp, I18N

app = WeddingApp()

st.set_page_config(page_title="Wedding App", page_icon="💍", layout="centered")

# ---------- Init session_state ----------
if "step" not in st.session_state: st.session_state.step = 0
if "lang" not in st.session_state: st.session_state.lang = "it"
if "selected_tags" not in st.session_state: st.session_state.selected_tags = set()
if "cart" not in st.session_state: st.session_state.cart = []
if "amounts" not in st.session_state: st.session_state.amounts = {}
if "gift_code" not in st.session_state: st.session_state.gift_code = None

def goto(step): st.session_state.step = step
T = I18N[st.session_state.lang]

# ---------- Header + Language toggle ----------
colA, colB = st.columns([4,1])
with colA:
    st.title(T["app_title"])
with colB:
    lang = st.selectbox(
        "", 
        options=[("it","🇮🇹 Italiano"), ("en","🇬🇧 English")],
        index=0 if st.session_state.lang=="it" else 1,
        format_func=lambda x: x[1],
        key="lang_select_global"
    )
    if lang[0] != st.session_state.lang:
        st.session_state.lang = lang[0]
        T = I18N[st.session_state.lang]
st.divider()

# ---------- Step 0 Welcome ----------
if st.session_state.step == 0:
    st.header(T["welcome_title"])
    st.markdown("""
    👋 Benvenuto nel **Gioco degli Auguri**!  
    Trasforma il tuo regalo in un simbolico carrello di azioni, settori e brand famosi.  
    È un modo divertente per fare un regalo con significato, senza comprare azioni vere.  

    ✨ Scegli i tuoi temi preferiti, componi il carrello e genera un codice speciale da usare nella causale del bonifico!
    """)
    st.button(T["start_quiz"], on_click=lambda: goto(1), type="primary")

# ---------- Step 1 Tags ----------
elif st.session_state.step == 1:
    st.header(T["profile_title"])
    tag_catalog = app.load_tag_catalog()
    lang = st.session_state.lang

    st.subheader("🎯 " + T["tags_title"])
    selected_tags = st.session_state.selected_tags

    cols = st.columns(4)
    for i, (_, row) in enumerate(tag_catalog.iterrows()):
        label = row["label_en"] if lang=="en" else row["label_it"]
        emoji = row["emoji"] if pd.notna(row["emoji"]) and row["emoji"]!="?" else "✨"
        tag_key = row["tag_key"]
        selected = tag_key in selected_tags
        style = "background-color:#ffdddd;" if selected else "background-color:#f5f5f5;"
        if cols[i % 4].button(f"{emoji} {label}", key=f"tag_{tag_key}"):
            if selected: selected_tags.remove(tag_key)
            else: selected_tags.add(tag_key)

    st.session_state.selected_tags = selected_tags
    st.button(T["to_suggestions"], on_click=lambda: goto(2), type="primary")

# ---------- Step 2 Companies ----------
elif st.session_state.step == 2:
    st.header(T["suggestions_title"])
    st.caption(T["suggestions_sub"])
    df = app.filter_universe_by_tag_keys(st.session_state.selected_tags)

    # Search bar
    search = st.text_input(T["search_placeholder"])
    if search:
        df = df[df["Company"].str.contains(search, case=False, na=False)]

    # Company cards
    for _, row in df.iterrows():
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(f"**{row['Company']}** ({row['Ticker']})")
            st.caption(app.display_tags(row, st.session_state.lang))
        with col2:
            if st.button("🛒 Aggiungi", key=f"add_{row['Ticker']}"):
                if row["Company"] not in st.session_state.cart:
                    st.session_state.cart.append(row["Company"])

    st.markdown("### 🛍️ Carrello attuale")
    if st.session_state.cart:
        st.write(", ".join(st.session_state.cart))
    else:
        st.info("Carrello vuoto.")

    col1, col2 = st.columns(2)
    with col1: st.button(T["back"], on_click=lambda: goto(1))
    with col2: st.button(T["to_amounts"], on_click=lambda: goto(3), type="primary")

# ---------- Step 3 Amounts ----------
elif st.session_state.step == 3:
    st.header(T["amounts_title"])
    st.caption(T["amounts_sub"])
    if not st.session_state.cart:
        st.warning("Nessuna selezione." if st.session_state.lang=="it" else "No picks yet.")
    else:
        for name in st.session_state.cart:
            st.session_state.amounts.setdefault(name, 0.0)
            st.number_input(name, min_value=0.0, step=5.0,
                            value=float(st.session_state.amounts[name]),
                            key=f"amt_{name}")
            st.session_state.amounts[name] = st.session_state[f"amt_{name}"]

        total = sum(st.session_state.amounts.values())
        st.markdown(f"### {T['total']}: € {total:,.2f}")
        st.info(T["instructions_safe"])
        col1, col2 = st.columns(2)
        with col1: st.button(T["back"], on_click=lambda: goto(2))
        with col2:
            if st.button(T["generate_code"], type="primary"):
                selections = [(n, st.session_state.amounts[n]) for n in st.session_state.cart if st.session_state.amounts[n]>0]
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
