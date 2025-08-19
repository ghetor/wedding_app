# app.py
import streamlit as st
import pandas as pd
from c_wedding_app import WeddingApp, I18N
import streamlit.components.v1 as components

def animated_tag_selector(tag_catalog, lang="it"):
    tags = []
    for _, row in tag_catalog.iterrows():
        label = row["label_en"] if lang == "en" else row["label_it"]
        emoji = row["emoji"] if row["emoji"] not in [None, "?", "nan"] else "✨"
        tags.append({"key": row["tag_key"], "label": f"{emoji} {label}"})

    html = """
    <style>
    .bubble {
      position: absolute;
      border-radius: 50%;
      padding: 15px 25px;
      background: #f0f8ff;
      border: 2px solid #0077b6;
      cursor: pointer;
      user-select: none;
      animation: float 10s infinite ease-in-out;
    }
    @keyframes float {
      0%   { transform: translateY(0px); }
      50%  { transform: translateY(-30px); }
      100% { transform: translateY(0px); }
    }
    .bubble.selected {
      background: #90e0ef;
      border-color: #03045e;
      font-weight: bold;
    }
    </style>
    <div id="bubble-container" style="position:relative; height:500px;">
    """
    import random
    for t in tags:
        x = random.randint(0, 80)
        y = random.randint(0, 80)
        html += f'<div class="bubble" style="left:{x}%;top:{y}%;" onclick="toggleBubble(this, \'{t["key"]}\')">{t["label"]}</div>'
    html += """
    </div>
    <script>
    const selected = new Set();
    function toggleBubble(el, key) {
      if (selected.has(key)) {
        selected.delete(key);
        el.classList.remove("selected");
      } else {
        selected.add(key);
        el.classList.add("selected");
      }
      const q = new URLSearchParams(window.location.search);
      q.set("selected_tags", Array.from(selected).join(","));
      window.history.replaceState(null, "", "?" + q.toString());
    }
    </script>
    """
    components.html(html, height=600)
#%%
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
    tag_catalog = app.load_tag_catalog()
    animated_tag_selector(tag_catalog, lang=st.session_state.lang)

    # Leggiamo le scelte dai query params
    qparams = st.experimental_get_query_params()
    selected = set()
    if "selected_tags" in qparams:
        selected = set(qparams["selected_tags"][0].split(","))
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
