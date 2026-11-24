import streamlit as st

from functions.handbook import load_handbook_section


def render_ai_principles() -> None:
    st.divider()
    try:
        principles_html = load_handbook_section("11.5")
    except (OSError, UnicodeError, ValueError) as exc:
        st.error(f"Could not load WGII's AI principles: {exc}")
        return

    st.markdown(principles_html, unsafe_allow_html=True)
