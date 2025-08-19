# app.py
import streamlit as st
import pandas as pd
from c_wedding_app import WeddingApp, I18N

# --- Hero image da Google Drive (ID dal tuo link) ---
HERO_URL = "https://drive.google.com/thumbnail?id=10zj4MWKuCwflsTNCa8hXSyEnsPB3_aul&sz=w1200"
# In Drive: Condividi -> Chiunque abbia il link: Visualizzatore

app = WeddingApp()

st.set_page_config(page_title="Wedding App", page_icon="💍", layout="centered")

# --- CSS: selectbox compatta per la lingua ---
st.markdown("""
<style>
div[data-baseweb="select"] { min-width: 70px !important; max-width: 70px !important; }
div[data-testid="stSelectbox"] label { display:none !important; }
</style>
""", unsafe_allow_html=True)

# ---------- Init session_state ----------
if "step" not in st.session_state: st.session_state.step = 0
if "lang" not in st.session_state: st.session_state.lang = "it"
if "selected_tags" not in st.session_state: st.session_state.selected_tags = set()
if "cart" not in st.session_state: st.session_state.cart = []
if "amounts" not in st.session_state: st.session_state.amounts = {}
if "gift_code" not in st.session_state: st.session_state.gift_code = None

def goto(step: int):
    st.session_state.step = step

T = I18N[st.session_state.lang]

# ---------- Header + Language toggle (sempre visibile) ----------
colA, colB = st.columns([4, 1])
with colA:
    st.title(I18N[st.session_state.lang]["app_title"])
with colB:
    lang = st.selectbox(
        "",
        options=[("it","🇮🇹"), ("en","🇬🇧")],
        index=0 if st.session_state.lang=="it" else 1,
        format_func=lambda x: x[1],
        key="lang_select_global",
    )
    if lang[0] != st.session_state.lang:
        st.session_state.lang = lang[0]
T = I18N[st.session_state.lang]
st.divider()

# ---------- Step 0 Welcome ----------
if st.session_state.step == 0:
    st.header(T["welcome_title"])
    st.markdown(
        "👋 Benvenutə nel **Gioco degli Auguri**!\n\n"
        "Trasforma il tuo regalo in un carrello **simbolico** di brand famosi: "
        "nessuna finanza vera, è solo un gioco per rendere il pensiero più divertente 💖\n\n"
        "Scegli i temi che ti ispirano, seleziona qualche azienda che li rappresenta "
        "e alla fine genera un **codice regalo** da usare nella causale del bonifico."
    )
    st.image(HERO_URL, use_column_width=True, caption="Un pizzico di ispirazione ✨")
    st.button(T["start_quiz"], on_click=lambda: goto(1), type="primary")

# ---------- Step 1 • Scegli i temi (curated & friendly) ----------
elif st.session_state.step == 1:
    st.header(T["profile_title"])
    lang = st.session_state.lang

    # Carica catalogo tag e tieni SOLO quelli semplici
    tag_catalog = app.load_tag_catalog()
    curated_keys = [
        "ai",             # 🤖 Tech & AI
        "electric_cars",  # ⚡ E-cars
        "movies",         # 🎬 Movies
        "music",          # 🎵 Music
        "travel",         # ✈️ Travel
        "food_bev",       # 🍔 Food & Drinks
        "sportswear",     # 👟 Sport & fashion
        "pets",           # 🐶 Pets
        "green",          # 🌱 Green / environment
        "luxury",         # 💎 Luxury
    ]
    df_tags = tag_catalog[tag_catalog["tag_key"].isin(curated_keys)].copy()

    st.subheader("🎯 " + T["tags_title"])
    selected = set(st.session_state.selected_tags)

    if df_tags.empty:
        st.info("Nessun tag disponibile. Controlla data/tag_catalog.csv.")
    else:
        cols = st.columns(5)  # griglia 2x5
        for i, (_, row) in enumerate(df_tags.iterrows()):
            label = row["label_en"] if lang == "en" else row["label_it"]
            emoji = row["emoji"] if pd.notna(row["emoji"]) and row["emoji"] != "?" else "✨"
            key = row["tag_key"]
            with cols[i % 5]:
                checked = st.checkbox(f"{emoji} {label}", value=(key in selected), key=f"tagchk_{key}")
                if checked:
                    selected.add(key)
                else:
                    selected.discard(key)

    st.session_state.selected_tags = selected

    # pillole riassuntive
    st.markdown(" ")
    if selected:
        pills = " ".join([f"`{k}`" for k in sorted(selected)])
        st.markdown(("**Selezionati:** " if lang=="it" else "**Selected:** ") + pills)

    st.markdown(" ")
    col1, col2 = st.columns(2)
    with col1:
        st.button(T["back"], on_click=lambda: goto(0))
    with col2:
        st.button(T["to_suggestions"], on_click=lambda: goto(2), type="primary")

# ---------- Step 2 Companies (shopping-style) ----------
elif st.session_state.step == 2:
    st.header(T["suggestions_title"])
    st.caption(T["suggestions_sub"])

    df = app.filter_universe_by_tag_keys(st.session_state.selected_tags).copy()

    # Barra di ricerca
    search = st.text_input(T["search_placeholder"])
    if search:
        df = df[df["Company"].str.contains(search, case=False, na=False)]

    # Cards aziende + bottone "Aggiungi al carrello"
    if df.empty:
        st.info("Nessuna azienda trovata." if st.session_state.lang=="it" else "No companies found.")
    else:
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
    with col1:
        st.button(T["back"], on_click=lambda: goto(1))
    with col2:
        st.button(T["to_amounts"], on_click=lambda: goto(3), type="primary")

# ---------- Step 3 Amounts ----------
elif st.session_state.step == 3:
    st.header(T["amounts_title"])
    st.caption(T["amounts_sub"])

    if not st.session_state.cart:
        st.warning("Nessuna selezione." if st.session_state.lang=="it" else "No picks yet.")
    else:
        for name in st.session_state.cart:
            st.session_state.amounts.setdefault(name, 0.0)
            st.number_input(
                name, min_value=0.0, step=5.0,
                value=float(st.session_state.amounts[name]),
                key=f"amt_{name}"
            )
            st.session_state.amounts[name] = st.session_state[f"amt_{name}"]

        total = sum(st.session_state.amounts.values())
        st.markdown(f"### {T['total']}: € {total:,.2f}")
        st.info(T["instructions_safe"])

        col1, col2 = st.columns(2)
        with col1:
            st.button(T["back"], on_click=lambda: goto(2))
        with col2:
            if st.button(T["generate_code"], type="primary"):
                selections = [(n, st.session_state.amounts[n]) for n in st.session_state.cart if st.session_state.amounts[n] > 0]
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
