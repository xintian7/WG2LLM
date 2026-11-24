import streamlit as st

from functions.handbook import load_handbook_section


def render_ai_use_case_reference() -> None:
    st.divider()
    try:
        reference_html = load_handbook_section("11.6")
    except (OSError, UnicodeError, ValueError) as exc:
        st.error(f"Could not load the AI use case reference: {exc}")
        return

    st.markdown(reference_html, unsafe_allow_html=True)
