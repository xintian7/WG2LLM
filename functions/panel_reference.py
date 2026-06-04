from pathlib import Path

import streamlit as st


@st.dialog("AI Use Case Reference (Full Screen)", width="large")
def _show_reference_figure_fullscreen(image_path: Path) -> None:
    st.image(
        str(image_path),
        caption="Figure 1. AI Guidance Use Case Reference from the IPCC WGII Author Handbook.",
        use_container_width=True,
    )


def render_ai_use_case_reference() -> None:
    st.divider()
    st.markdown("<h3 style='text-align:center'>AI Use Case Reference</h3>", unsafe_allow_html=True)

    image_path = Path(__file__).resolve().parent.parent / "assets" / "AIGuidance.webp"
    principles_path = Path(__file__).resolve().parent.parent / "AI Principles.txt"
    if image_path.exists():
        st.image(
            str(image_path),
            caption="Figure 1. AI Guidance Use Case Reference from the IPCC WGII Author Handbook.",
            use_container_width=True,
        )
        st.info(
            "The AI use case reference will be updated soon after the publication of the report for the "
            "[IPCC Workshop on Engaging Diverse Knowledge Systems and IPCC Workshop on Methods of Assessment]"
            "(https://www.ipcc.ch/event/ipcc-workshop-on-engaging-diverse-knowledge-systems-and-ipcc-workshop-on-methods-of-assessment/)."
        )
        with image_path.open("rb") as img_file:
            image_bytes = img_file.read()
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            st.download_button(
                "Download figure",
                data=image_bytes,
                file_name="AIGuidance.webp",
                mime="image/webp",
                use_container_width=True,
            )
        with action_col2:
            if st.button("Expand to full screen", use_container_width=True):
                _show_reference_figure_fullscreen(image_path)

        st.divider()
        st.markdown("<h3 style='text-align:center'>AI principles</h3>", unsafe_allow_html=True)
        if principles_path.exists():
            principles_text = principles_path.read_text(encoding="utf-8").strip()
            if principles_text:
                st.markdown(principles_text)
            else:
                st.info("AI principles text is currently empty.")
        else:
            st.warning("AI principles file not found: AI Principles.txt")
    else:
        st.warning("Reference image not found: assets/AIGuidance.webp")
