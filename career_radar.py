import streamlit as st
import time
import random

def show_career_radar(colors):
    """
    Interactive Career Radar Animation
    Plays once per session
    """

    if st.session_state.get("animation_played", False):
        return

    PRIMARY = colors["primary"]
    BG = colors["background"]
    ACCENT1 = colors["accent1"]
    ACCENT2 = colors["accent2"]
    ACCENT3 = colors["accent3"]
    TEXT = colors["text"]

    careers = [
        "Engineer", "Doctor", "Designer", "Entrepreneur",
        "Scientist", "Lawyer", "Psychologist", "Architect",
        "Data Analyst", "Researcher", "Journalist"
    ]

    # CSS for radar effect
    st.markdown(
        f"""
        <style>
        .radar-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 55vh;
            background: radial-gradient(circle at center,
                        {ACCENT1}22,
                        {BG} 70%);
            border-radius: 20px;
            margin-bottom: 30px;
        }}

        .radar-circle {{
            width: 320px;
            height: 320px;
            border-radius: 50%;
            border: 3px dashed {PRIMARY};
            display: flex;
            justify-content: center;
            align-items: center;
            animation: pulse 2s infinite;
        }}

        .radar-text {{
            font-size: 2rem;
            font-weight: 700;
            color: {ACCENT2};
            transition: all 0.4s ease;
        }}

        @keyframes pulse {{
            0% {{ transform: scale(1); opacity: 0.9; }}
            50% {{ transform: scale(1.04); opacity: 1; }}
            100% {{ transform: scale(1); opacity: 0.9; }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    container = st.empty()

    # Rotation animation
    for _ in range(9):
        word = random.choice(careers)
        container.markdown(
            f"""
            <div class="radar-container">
                <div class="radar-circle">
                    <div class="radar-text">{word}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        time.sleep(0.8)

    # Final freeze message
    container.markdown(
        f"""
        <div class="radar-container">
            <div class="radar-circle">
                <div class="radar-text" style="color:{ACCENT3};">
                    Let AI find <i>your</i> path
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    time.sleep(1.2)
    st.session_state.animation_played = True
