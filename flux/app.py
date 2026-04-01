import json
import os
import base64
from dotenv import load_dotenv
import streamlit as st

# Load environment variables explicitly from flux/.env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from agent.graph import flux_graph
from agent.state import FluxState

# ── Suggestion Chips ───────────────────────────────────────────────────────────
SUGGESTION_CHIPS = [
    {"icon": "🌙", "label": "Late-night study calm",       "prompt": "Something calm and ambient for a late-night study session — music, podcasts and films"},
    {"icon": "🚗", "label": "Weekend road trip",            "prompt": "Upbeat tracks, shows and podcasts perfect for a long weekend road trip"},
    {"icon": "🎭", "label": "Dark psychological thriller",  "prompt": "Gripping dark psychological thriller movies, true-crime podcasts and related news"},
    {"icon": "☔", "label": "Rainy Sunday jazz",             "prompt": "Jazz music, slow documentaries and art films for a cozy rainy Sunday"},
    {"icon": "💪", "label": "High-energy workout",          "prompt": "High-BPM music, hype videos and motivational podcasts to fuel my workout"},
    {"icon": "🎨", "label": "Creative & indie vibes",       "prompt": "Lo-fi music, indie films and art documentaries for a solo creative evening"},
    {"icon": "🌅", "label": "Morning focus & news",         "prompt": "Mellow focus music, top morning news and uplifting podcasts to start the day right"},
    {"icon": "🕺", "label": "Party night in",               "prompt": "Party-ready music, trending videos and fun shows for a social night in"},
]

DOMAIN_COLORS = {
    "videos":   "#D95534",
    "music":    "#FF0000",  # YouTube Red
    "movies":   "#4A8B63",
    "podcasts": "#4570DA",
    "news":     "#4285F4",
}

st.set_page_config(
    page_title="FLUX",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,600;1,600&display=swap');

/* ── Reset & Base ── */
* { font-family: 'Inter', system-ui, -apple-system, sans-serif; box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: #F9F9F8 !important;
    color: #1A1A19 !important;
}

[data-testid="stAppViewContainer"] { padding: 0 !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── Header ── */
.flux-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 48px;
    border-bottom: 1.5px solid #E5E3E0;
    position: sticky;
    top: 0;
    background: rgba(249, 249, 248, 0.92);
    backdrop-filter: blur(8px);
    z-index: 100;
}

.flux-logo {
    font-size: 26px;
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-weight: 600;
    letter-spacing: -0.5px;
    color: #1A1A19;
}

.flux-logo span { color: #DA6A45; margin-right: 10px; font-style: normal; }

.flux-tagline {
    font-size: 15px;
    font-family: 'Inter', sans-serif;
    color: #6B6B66;
    font-weight: 400;
}

/* ── Chat Messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 10px 0 !important;
}

[data-testid="stChatMessageContent"] {
    background: #FFFFFF !important;
    border: 1px solid #E5E3E0 !important;
    border-radius: 14px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    padding: 18px 22px !important;
    color: #1A1A19 !important;
    font-size: 16px !important;
    line-height: 1.7 !important;
}

/* ── Synthesis Card ── */
.synthesis-card {
    background: #FFFFFF;
    border: 1px solid #E5E3E0;
    border-left: 4px solid #DA6A45;
    border-radius: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    padding: 20px 24px;
    margin: 16px 0;
    font-size: 16px;
    line-height: 1.8;
    color: #1A1A19;
}

.synthesis-label {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #DA6A45;
    margin-bottom: 8px;
}

/* ── Domain Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    background: transparent !important;
    border-bottom: 1px solid #E5E3E0 !important;
    gap: 0 !important; padding: 0 !important;
}
[data-testid="stTabs"] [role="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    border-radius: 0 !important;
    color: #8C8C87 !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    padding: 14px 20px !important;
    margin: 0 !important;
    transition: all 0.15s ease !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #1A1A19 !important;
    border-bottom: 3px solid #DA6A45 !important;
}
[data-testid="stTabs"] [role="tab"]:hover { color: #1A1A19 !important; }

/* ── Recommendation Cards ── */
.rec-card {
    background: #FFFFFF;
    border: 1px solid #E5E3E0;
    border-radius: 14px;
    padding: 16px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.01);
    transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
    cursor: pointer;
    height: 100%;
}
.rec-card:hover {
    border-color: #CECCC7;
    transform: translateY(-3px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.06);
}
.rec-card img {
    width: 100%; border-radius: 8px; margin-bottom: 12px;
    object-fit: cover; aspect-ratio: 16/9; background: #F0EEEB;
}
.rec-card-title {
    font-size: 15px; font-weight: 600;
    color: #1A1A19; line-height: 1.4; margin-bottom: 4px;
    display: -webkit-box; -webkit-line-clamp: 2;
    -webkit-box-orient: vertical; overflow: hidden;
}
.rec-card-meta { font-size: 13px; color: #6B6B66; font-weight: 400; }
.rec-card-link {
    display: inline-block; margin-top: 10px;
    font-size: 13px; font-weight: 600;
    color: #DA6A45; text-decoration: none;
}
.domain-dot {
    display: inline-block; width: 7px; height: 7px;
    border-radius: 50%; margin-right: 6px; vertical-align: middle;
}

/* ── Score Badge ── */
.score-badge {
    display: inline-block;
    background: #F0EEEB;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
    color: #6B6B66;
    padding: 2px 8px;
    margin-left: 6px;
    vertical-align: middle;
}

/* ── Follow-up Chip ── */
.followup-label {
    font-size: 12px; font-weight: 600;
    letter-spacing: 0.8px; text-transform: uppercase;
    color: #B0B0A8; margin: 20px 0 8px 0;
}
.followup-chip .stButton > button {
    background: #FFFAF8 !important;
    border: 1.5px solid #DA6A45 !important;
    border-radius: 999px !important;
    color: #DA6A45 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 10px 20px !important;
    cursor: pointer !important;
    transition: background 0.15s ease, box-shadow 0.15s ease !important;
    white-space: normal !important;
    text-align: left !important;
}
.followup-chip .stButton > button:hover {
    background: #DA6A45 !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 12px rgba(218,106,69,0.2) !important;
}

/* ── Input Bar ── */
[data-testid="stChatInput"] {
    background: #FFFFFF !important;
    border: 1px solid #E5E3E0 !important;
    border-radius: 16px !important;
    color: #1A1A19 !important;
    font-size: 16px !important;
    padding: 16px 22px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03) !important;
}
[data-testid="stChatInput"]:focus {
    border-color: #CECCC7 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
}
[data-testid="stChatInput"]::placeholder { color: #B0B0A8 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #D1CFCA; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #B0AFA9; }

/* ── Suggestion Chips ── */
.chip-section-label {
    text-align: center;
    font-size: 11px; font-weight: 600;
    letter-spacing: 1.2px; text-transform: uppercase;
    color: #B0B0A8; margin: 14px 0 6px 0;
}
.chip-grid .stButton > button {
    background: #FFFFFF !important;
    border: 1.5px solid #E5E3E0 !important;
    border-radius: 999px !important;
    color: #1A1A19 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 14px !important;
    cursor: pointer !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.12s ease !important;
    white-space: nowrap !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    line-height: 1.3 !important;
    width: 100% !important;
}
.chip-grid .stButton > button:hover {
    border-color: #DA6A45 !important;
    color: #DA6A45 !important;
    box-shadow: 0 3px 10px rgba(218,106,69,0.10) !important;
    transform: translateY(-1px) !important;
    background: #FFFAF8 !important;
}

/* ── Main padding — tighter for no-scroll ── */
.main .block-container {
    padding: 16px 32px 8px 32px !important;
    max-width: 1200px !important;
}
</style>

<!-- FLUX Header -->
<div class="flux-header">
    <div class="flux-logo"><span>⚡</span>FLUX</div>
    <div class="flux-tagline">Your taste, everywhere.</div>
</div>
""", unsafe_allow_html=True)


def initialize_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "prefill" not in st.session_state:
        st.session_state.prefill = None


def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


def render_card(title, meta, link, image_url=None, domain_color="#8C8C87"):
    img_html = (
        f'<img src="{image_url}" loading="lazy" />'
        if image_url
        else '<div style="width:100%;aspect-ratio:16/9;background:#F0EEEB;border-radius:8px;margin-bottom:12px;"></div>'
    )
    safe_title = title[:80] + "…" if len(title) > 80 else title
    return f"""
    <div class="rec-card">
        {img_html}
        <div class="rec-card-title">{safe_title}</div>
        <div class="rec-card-meta">
            <span class="domain-dot" style="background:{domain_color}"></span>
            {meta}
        </div>
        <a class="rec-card-link" href="{link}" target="_blank">Open →</a>
    </div>
    """


def score_label(score):
    """Convert a 0-10 score to an emoji + number badge."""
    try:
        s = int(score)
    except Exception:
        return ""
    if s >= 8:
        star = "🔥"
    elif s >= 5:
        star = "✨"
    else:
        star = "·"
    return f" ({star} {s}/10)"


def render_domain_tab(items, domain_color):
    if not items:
        st.markdown('<p style="color:#8C8C87;padding:20px 0;">No results found for this domain.</p>',
                    unsafe_allow_html=True)
        return
    cols = st.columns(3)
    for idx, item in enumerate(items[:6]):
        with cols[idx % 3]:
            st.markdown(render_card(
                item.get("title", ""),
                item.get("meta", item.get("source", "")),
                item.get("url", "#"),
                image_url=item.get("image_url"),
                domain_color=domain_color
            ), unsafe_allow_html=True)


def main():
    initialize_session()

    if not st.session_state.messages:
        # ── Landing: fits in one viewport, no scroll ───────────────────────
        banner_path = os.path.join(os.path.dirname(__file__), "banner.png")
        banner_b64 = get_image_base64(banner_path)
        img_src = (
            f"data:image/png;base64,{banner_b64}"
            if banner_b64
            else "https://images.unsplash.com/photo-1628155930542-3c7a64e2c833?q=80&w=2000&auto=format&fit=crop"
        )

        st.markdown(f"""
        <div style="text-align:center; padding: 4px 0 0 0;">
            <div style="width:100%;border-radius:10px;overflow:hidden;margin-bottom:10px;">
                <img src="{img_src}" alt="Flux Banner"
                     style="width:100%;height:120px;object-fit:cover;border-radius:10px;display:block;" />
            </div>
            <h1 style="font-family:'Playfair Display',serif;font-size:46px;font-weight:600;
                       font-style:italic;color:#1A1A19;margin:0 0 4px 0;line-height:1.15;">
                What do you want to experience?
            </h1>
            <p style="font-size:17px;color:#6B6B66;font-weight:400;margin:0;">
                Music, podcasts, movies, and more. Describe your mood.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Suggestion chips — 2 rows × 4 ─────────────────────────────────
        st.markdown('<div class="chip-section-label">✦ Try asking FLUX</div>', unsafe_allow_html=True)
        st.markdown('<div class="chip-grid">', unsafe_allow_html=True)
        row1 = st.columns(4)
        row2 = st.columns(4)
        for col, chip in zip(row1 + row2, SUGGESTION_CHIPS):
            with col:
                if st.button(f"{chip['icon']}  {chip['label']}", key=f"chip_{chip['label']}"):
                    st.session_state.prefill = chip["prompt"]
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Chat history ───────────────────────────────────────────────────────
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)

    # ── Input (typed or chip prefill) ─────────────────────────────────────
    user_input = st.chat_input("What are you in the mood for?")
    if st.session_state.prefill:
        user_input = st.session_state.prefill
        st.session_state.prefill = None

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.spinner("⚡ FLUX is thinking across all domains…"):
            try:
                initial_state: FluxState = {
                    "messages": [],
                    "user_input": user_input,
                    "conversation_memory": st.session_state.conversation_history[-12:],
                    "preferences": {},
                    "domain_results": {},
                    "domain_scores": {},
                    "follow_up_question": "",
                    "cross_domain_insight": "",
                    "final_output": ""
                }

                result = flux_graph.invoke(initial_state)
                final_output = json.loads(result.get("final_output", "{}"))
                insight = final_output.get("insight", result.get("cross_domain_insight", ""))
                results = final_output.get("results", {})
                domain_scores = final_output.get("domain_scores", {})
                follow_up = final_output.get("follow_up_question", "")

                # Update rolling conversation memory
                st.session_state.conversation_history.append({"role": "user", "content": user_input})
                st.session_state.conversation_history.append({"role": "assistant", "content": insight})

                # ── Assistant synthesis card ───────────────────────────────
                assistant_html = f"""
<div class="synthesis-card">
    <div class="synthesis-label">✦ Synthesis Insight</div>
    {insight}
</div>
"""
                st.session_state.messages.append({"role": "assistant", "content": assistant_html})

                with st.chat_message("assistant"):
                    st.markdown(assistant_html, unsafe_allow_html=True)

                    # ── Domain tabs with relevance scores ─────────────────
                    def tab_label(emoji, name, key):
                        s = domain_scores.get(key, "")
                        badge = score_label(s) if s else ""
                        return f"{emoji} {name}{badge}"

                    tab1, tab2, tab3, tab4, tab5 = st.tabs([
                        tab_label("🎬", "Videos",   "videos"),
                        tab_label("🎵", "Music",    "music"),
                        tab_label("🎥", "Movies",   "movies"),
                        tab_label("🎙", "Podcasts", "podcasts"),
                        tab_label("📰", "News",     "news"),
                    ])

                    with tab1: render_domain_tab(results.get("videos", []),   DOMAIN_COLORS["videos"])
                    with tab2: render_domain_tab(results.get("music", []),    DOMAIN_COLORS["music"])
                    with tab3: render_domain_tab(results.get("movies", []),   DOMAIN_COLORS["movies"])
                    with tab4: render_domain_tab(results.get("podcasts", []), DOMAIN_COLORS["podcasts"])
                    with tab5: render_domain_tab(results.get("news", []),     DOMAIN_COLORS["news"])

                    # ── Follow-up question chip ────────────────────────────
                    if follow_up:
                        st.markdown('<div class="followup-label">🔁 Refine your taste</div>',
                                    unsafe_allow_html=True)
                        st.markdown('<div class="followup-chip">', unsafe_allow_html=True)
                        if st.button(f"💬  {follow_up}", key=f"followup_{len(st.session_state.messages)}"):
                            st.session_state.prefill = follow_up
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                error_msg = f"❌ Something went wrong: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                with st.chat_message("assistant"):
                    st.error(error_msg)

    # ── Footer ────────────────────────────────────────────────────────────
    st.divider()
    st.markdown(
        "<div style='font-size:14px;font-weight:500;color:#1A1A19;'>"
        "<strong>FLUX</strong> — Made with ❤️ by Ramesh Choudhary</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
