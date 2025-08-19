# app.py
import streamlit as st
import pandas as pd
from c_wedding_app import WeddingApp, I18N
import streamlit.components.v1 as components

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
if "selected_tags" not in st.session_state:
    st.session_state.selected_tags = set()

T = I18N[st.session_state.lang]

# ---------- Header + Language toggle ----------
colA, colB = st.columns([4,1])
with colA:
    st.title(T["app_title"])
with colB:
    current = st.session_state.lang
    if current == "it":
        flag = "🇮🇹"
    else:
        flag = "🇬🇧"

    html = f"""
    <style>
    .lang-dropdown {{
        position: relative;
        display: inline-block;
    }}
    .lang-button {{
        background: white;
        border: 1px solid #ccc;
        padding: 2px 6px;
        border-radius: 6px;
        font-size: 20px;
        cursor: pointer;
    }}
    .lang-options {{
        display: none;
        position: absolute;
        background: white;
        border: 1px solid #ccc;
        border-radius: 6px;
        margin-top: 2px;
        z-index: 9999;
    }}
    .lang-options div {{
        padding: 4px 8px;
        cursor: pointer;
    }}
    .lang-options div:hover {{
        background: #eee;
    }}
    .lang-dropdown:hover .lang-options {{
        display: block;
    }}
    </style>

    <div class="lang-dropdown">
        <div class="lang-button">{flag} ▼</div>
        <div class="lang-options">
            <div onclick="window.parent.postMessage({{'lang':'it'}}, '*')">🇮🇹 Italiano</div>
            <div onclick="window.parent.postMessage({{'lang':'en'}}, '*')">🇬🇧 English</div>
        </div>
    </div>
    """
    st.components.v1.html(html, height=50)

# piccolo hack per ricevere i messaggi
lang_choice = st.session_state.lang
if "_lang_msg" in st.session_state:
    lang_choice = st.session_state._lang_msg
if lang_choice != st.session_state.lang:
    st.session_state.lang = lang_choice
    T = I18N[st.session_state.lang]



def goto(step): st.session_state.step = step

# ---------- Smart Tag Selector ----------
def tag_selector(tag_catalog: pd.DataFrame, lang="it"):
    st.subheader("🎯 " + T["tags_title"])
    selected_tags = st.session_state.get("selected_tags", set())

    groups = tag_catalog["group_key"].unique()
    for group in groups:
        with st.expander(f"📂 {group.capitalize()}"):
            subset = tag_catalog[tag_catalog["group_key"] == group]
            cols = st.columns(3)  # griglia 3 colonne
            for i, row in subset.iterrows():
                label = row["label_en"] if lang == "en" else row["label_it"]
                emoji = row["emoji"] if pd.notna(row["emoji"]) and row["emoji"] != "?" else "✨"
                tag_key = row["tag_key"]

                if tag_key in selected_tags:
                    style = "background-color:#cce5ff;border-radius:10px;padding:8px;border:2px solid #004085;"
                else:
                    style = "background-color:white;border-radius:10px;padding:8px;border:1px solid #ccc;"

                with cols[i % 3]:
                    if st.button(f"{emoji} {label}", key=f"tag_{tag_key}"):
                        if tag_key in selected_tags:
                            selected_tags.remove(tag_key)
                        else:
                            selected_tags.add(tag_key)

    # salva stato
    st.session_state["selected_tags"] = selected_tags

    # mostriamo pillole dei selezionati
    if selected_tags:
        st.markdown("### ✅ Selezionati:")
        st.markdown(" ".join([f"`{t}`" for t in selected_tags]))


# ---------- Step 0 Welcome ----------
if st.session_state.step == 0:
    st.header(T["welcome_title"])
    st.write(T["welcome_sub"])
    st.button(T["start_quiz"], on_click=lambda: goto(1), type="primary")

# ---------- Step 1 Tags ----------
elif st.session_state.step == 1:
    st.header(T["profile_title"])

    # --- Mini quiz (opzionale, puoi toglierlo se vuoi)
    st.subheader("✨ Mini quiz per scoprire i tuoi temi")

    q1 = st.radio(
        "Se fosse un viaggio di nozze sarebbe…",
        ["🌴 Relax", "🚀 Avventura", "🎭 Cultura"],
        key="quiz1"
    )
    q2 = st.radio(
        "Il regalo perfetto ha a che fare con…",
        ["🤖 Tecnologia", "🍷 Cibo & bevande", "💎 Lusso"],
        key="quiz2"
    )

    st.markdown("---")

    # --- Bubbles selezionabili
    st.subheader("🎈 Scegli le tue bolle preferite")

    bubbles = [
        ("ai", "🤖", "AI / Tech"),
        ("chips", "💻", "Chips"),
        ("cloud", "☁️", "Cloud"),
        ("ecars", "⚡", "E-Cars"),
        ("movies", "🎬", "Movies"),
        ("music", "🎵", "Music"),
        ("luxury", "💎", "Luxury"),
        ("sport", "🏀", "Sport"),
        ("travel", "✈️", "Travel"),
        ("food", "🍔", "Food & Bev"),
        ("pets", "🐶", "Pets"),
        ("green", "🌱", "Green"),
    ]

    if "selected_tags" not in st.session_state:
        st.session_state.selected_tags = set()

    cols = st.columns(6)
    for i, (key, emoji, label) in enumerate(bubbles):
        with cols[i % 6]:
            selected = key in st.session_state.selected_tags
            style = f"""
                background-color: {'#ffcccc' if selected else 'white'};
                border: 2px solid {'#ff6666' if selected else '#ccc'};
                border-radius: 50%;
                padding: 25px;
                text-align: center;
                cursor: pointer;
                font-size: 14px;
                margin: 5px;
            """
            if st.button(f"{emoji} {label}", key=f"bubble_{key}"):
                if selected:
                    st.session_state.selected_tags.remove(key)
                else:
                    st.session_state.selected_tags.add(key)
            st.markdown(
                f"<div style='{style}'>{emoji}<br>{label}</div>",
                unsafe_allow_html=True
            )

    # --- Pulsante avanti
    st.markdown(" ")
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
