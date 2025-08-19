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

# helper per navigazione step
def goto(step: int):
    st.session_state.step = step

T = I18N[st.session_state.lang]

# ---------- Header + Language toggle ----------
colA, colB = st.columns([4,1])
with colA:
    st.title(T["app_title"])
with colB:
    # piccolo menu compatto con HTML
    current = st.session_state.lang
    flag = "🇮🇹" if current == "it" else "🇬🇧"

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
        min-width: 45px;
        text-align:center;
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
    st.components.v1.html(html, height=60)

# intercetta il messaggio e aggiorna la lingua
lang_choice = st.session_state.lang
msg = st.experimental_get_query_params().get("lang", [None])[0]
if msg in ["it", "en"] and msg != st.session_state.lang:
    st.session_state.lang = msg
    T = I18N[msg]


# ---------- Step 0 Welcome ----------
if st.session_state.step == 0:
    st.header(T["welcome_title"])
    st.write(T["welcome_sub"])
    st.button(T["start_quiz"], on_click=lambda: goto(1), type="primary")

# ---------- Step 1 Tags ----------
elif st.session_state.step == 1:
    st.header(T["profile_title"])
    st.subheader("🎈 " + ("Scegli le tue bolle preferite" if st.session_state.lang=="it" else "Pick your favorite bubbles"))

    TAGS = [
        ("ai", "🤖", "AI / Tech"),
        ("chips", "💾", "Chips"),
        ("cloud", "☁️", "Cloud"),
        ("ecars", "⚡🚗", "E-Cars"),
        ("movies", "🎬", "Movies"),
        ("music", "🎵", "Music"),
        ("luxury", "💎", "Luxury"),
        ("sport", "🏀", "Sport"),
        ("travel", "✈️", "Travel"),
        ("food", "🍔", "Food & Bev"),
        ("pets", "🐶", "Pets"),
        ("green", "🌱", "Green"),
    ]

    # inizializza se non c'è
    if "selected_tags" not in st.session_state:
        st.session_state.selected_tags = set()

    html = "<div style='display:flex;flex-wrap:wrap;gap:15px;'>"
    for key, emoji, label in TAGS:
        active = key in st.session_state.selected_tags
        bg = "#ffcccc" if active else "white"
        border = "3px solid #ff4b4b" if active else "2px solid #ccc"
        html += f"""
        <div onclick="var p=document.querySelector('input#{key}');
                      p.checked=!p.checked; p.dispatchEvent(new Event('change'));"
             style="cursor:pointer;width:90px;height:90px;border-radius:50%;
                    display:flex;align-items:center;justify-content:center;
                    flex-direction:column;background:{bg};border:{border};
                    font-size:13px;">
            <div style="font-size:22px;">{emoji}</div>
            <div>{label}</div>
        </div>
        <input type="checkbox" id="{key}" style="display:none" {'checked' if active else ''}>
        """
    html += "</div>"

    selected = st.html(html)  # se usi st.markdown(unsafe_allow_html=True) meglio ancora

    # aggiorna lo stato
    for key, _, _ in TAGS:
        val = st.session_state.get(key, False)
        if val:
            st.session_state.selected_tags.add(key)
        else:
            st.session_state.selected_tags.discard(key)

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
