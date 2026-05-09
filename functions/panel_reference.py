from pathlib import Path

import streamlit as st


def render_ai_use_case_reference() -> None:
    st.divider()
    st.markdown("<h3 style='text-align:center'>AI Use Case Reference</h3>", unsafe_allow_html=True)

    image_path = Path(__file__).resolve().parent.parent / "assets" / "AIGuidance.webp"
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
        st.download_button(
            "Download figure",
            data=image_bytes,
            file_name="AIGuidance.webp",
            mime="image/webp",
            use_container_width=False,
        )
    else:
        st.warning("Reference image not found: assets/AIGuidance.webp")
