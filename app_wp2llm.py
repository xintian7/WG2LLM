import streamlit as st
from pathlib import Path
from button_check_aicase import get_ai_guidance_status, perform_ai_guidance
from functions.env_loader import get_azure_settings
from functions.write2notion import write_to_notion


st.markdown("""
<style>

/* Hide Streamlit footer ("Hosted with Streamlit") */
footer {
    visibility: hidden;
    display: none !important;
}

/* Hide bottom decoration (GitHub avatar / repo badge) */
[data-testid="stDecoration"] {
    display: none;
}
            
</style>
""", unsafe_allow_html=True)

# ---- IPCC STYLE ----
st.markdown("""
<style>
.main-title {
    /* no background to keep default page background */
    color: #00a9cf;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    font-size: 42px;
    font-weight: 700;
    letter-spacing: 1px;
}

div.stButton > button[kind="primary"] {
    background-color: #1f77b4;
    color: #ffffff;
    border: 1px solid #1f77b4;
    min-height: 48px;
    padding: 0.5rem 1.25rem;
    white-space: nowrap;
}

div.stButton > button[kind="primary"]:hover {
    background-color: #166aa3;
    border-color: #166aa3;
}

div.stButton > button[kind="secondary"] {
    background-color: #8f98a3;
    color: #ffffff;
    border: 1px solid #8f98a3;
    min-height: 48px;
    padding: 0.5rem 1.25rem;
    white-space: nowrap;
}

div.stButton > button[kind="secondary"]:hover {
    background-color: #7f8893;
    border-color: #7f8893;
}

</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">WGII AI Assistant</div>', unsafe_allow_html=True)


def _get_client_ip() -> str:
    ctx = getattr(st, "context", None)
    headers = getattr(ctx, "headers", None) if ctx is not None else None
    if not headers:
        return ""

    forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return headers.get("x-real-ip") or headers.get("X-Real-IP") or ""


def render_text_document_page(doc_key: str) -> None:
    """Render a markdown document from assets based on the selected key."""
    docs = {
        "privacy": ("Privacy Policy", "Privacy Policy.txt"),
        "terms": ("Terms of Use", "Terms of Use.txt"),
    }

    doc_meta = docs.get(doc_key)
    if not doc_meta:
        st.error("Requested document was not found.")
        st.markdown("[Back to WGII AI Assistant](?)")
        return

    doc_title, doc_filename = doc_meta
    doc_path = Path(__file__).parent / "assets" / doc_filename

    st.divider()
    st.markdown(f"## {doc_title}")

    if not doc_path.exists():
        st.error(f"Document file not found: assets/{doc_filename}")
        st.markdown("[Back to WGII AI Assistant](?)")
        return

    doc_text = doc_path.read_text(encoding="utf-8").strip()
    if not doc_text:
        st.warning(f"Document is empty: assets/{doc_filename}")
    else:
        st.markdown(doc_text)

    st.markdown("[Back to WGII AI Assistant](?)")


query_params = st.query_params
doc_key = query_params.get("doc")
if doc_key:
    render_text_document_page(str(doc_key))
    st.stop()


def render_ai_use_case_reference() -> None:
    """Display the AI use case reference image from assets."""
    st.divider()
    st.markdown("<h3 style='text-align:center'>AI Use Case Reference</h3>", unsafe_allow_html=True)

    image_path = Path(__file__).parent / "assets" / "AIGuidance.webp"
    if image_path.exists():
        st.image(str(image_path), caption="Figure 1. AI Guidance Use Case Reference from the IPCC WGII Author Handbook.", use_container_width=True)
        st.info(
            "The AI use case reference will be updated soon after the publication of the report for the "
            "[IPCC Workshop on Engaging Diverse Knowledge Systems and IPCC Workshop on Methods of Assessment](https://www.ipcc.ch/event/ipcc-workshop-on-engaging-diverse-knowledge-systems-and-ipcc-workshop-on-methods-of-assessment/)."
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

# Pre-populate Azure settings from .env and refill any missing values on reruns.
env_settings = get_azure_settings()
session_env_keys = [
    ("azure_endpoint", "endpoint"),
    ("azure_api_key", "api_key"),
    ("azure_chat_deployment", "chat_deployment"),
    ("azure_embed_deployment", "embed_deployment"),
    ("azure_api_version", "api_version"),
]

if "_env_settings_loaded" not in st.session_state:
    for session_key, env_key in session_env_keys:
        st.session_state[session_key] = (env_settings.get(env_key) or "").strip()
    st.session_state["_env_settings_loaded"] = True
else:
    for session_key, env_key in session_env_keys:
        if not (st.session_state.get(session_key, "") or "").strip():
            st.session_state[session_key] = (env_settings.get(env_key) or "").strip()

spacer_left, btn_wrap, spacer_right = st.columns([0.3, 6, 0.3])
with btn_wrap:
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Check AI use cases", use_container_width=True, type="primary"):
            st.session_state["active_panel"] = "ai_guidance"
    with col2:
        if st.button("Rephrase sentences", use_container_width=True, type="secondary"):
            st.session_state["active_panel"] = "rephrase"
    with col3:
        if st.button("Check grammar", use_container_width=True, type="secondary"):
            st.session_state["active_panel"] = "grammar"

    row2_col1, row2_col2, row2_col3 = st.columns(3)
    with row2_col1:
        if st.button("View AI use case reference", use_container_width=True, type="primary"):
            st.session_state["active_panel"] = "view_use_cases"
    with row2_col2:
        if st.button("Report a new AI use case", use_container_width=True, type="secondary"):
            st.session_state["active_panel"] = "report_use_case"
    with row2_col3:
        if st.button("Use case scenario analysis", use_container_width=True, type="secondary"):
            st.session_state["active_panel"] = "use_case_scenario_analysis"

    row3_col1, row3_col2, row3_col3 = st.columns(3)

active_panel = st.session_state.get("active_panel")

if active_panel == "ai_guidance":
    st.divider()
    st.markdown("<h3 style='text-align:center'>Check AI use cases based on the AI guidance</h3>", unsafe_allow_html=True)
    ai_guidance_container = st.container()
    with ai_guidance_container:
        kb_status = get_ai_guidance_status()
        if kb_status["ready"]:
            parts = [
                "Knowledge base: ready",
                f"Indexed chunks: {kb_status['chunks']}",
            ]
            if kb_status["last_load_sec"] is not None:
                parts.append(f"Last engine load: {kb_status['last_load_sec']}s")
            if kb_status["cached"]:
                parts.append("Engine cache: warm")
            st.caption(" | ".join(parts))
        else:
            msg = kb_status["message"] or "Knowledge base is not ready yet."
            st.caption(f"Knowledge base: not ready | {msg}")

        user_query = st.text_area(
            "Check whether an AI use case is permitted based on the AI guidance from the WGII AR7 Author Handbook:",
            placeholder="e.g. Can I use AI to help rephrase a sentence in the assessment text?",
            key="ai_guidance_query",
            height=120,
        )
        if st.button("Submit", key="ai_guidance_submit", type="primary"):
            answer_text = perform_ai_guidance(
                query=user_query,
                container=ai_guidance_container,
            )
            if user_query.strip():
                try:
                    write_to_notion(user_query, _get_client_ip(), answer_text)
                except Exception as exc:
                    st.warning(f"Notion logging failed: {exc}")
elif active_panel == "view_use_cases":
    render_ai_use_case_reference()
elif active_panel in ("rephrase", "grammar", "report_use_case", "use_case_scenario_analysis"):
    label_map = {
        "rephrase": "Rephrase sentences",
        "grammar": "Check grammar",
        "report_use_case": "Report a new AI use case",
        "use_case_scenario_analysis": "Use case scenario analysis",
    }
    label = label_map.get(active_panel, "This feature")
    st.divider()
    st.info(f"**{label}** is still being developed and will be available soon.")

with st.sidebar:
    st.header("About")
    st.markdown(
        "<span style='color: #00a9cf; font-weight: bold;'>WGII AI Assistant</span> (ver 0.1) "
        "is a web app developed by the IPCC [WGII](https://www.ipcc.ch/working-group/wg2/) TSU to help IPCC authors use AI-enhanced functionalities. "
        "Please contact tsu@ipccwg2.org if you have any questions or suggestions.",
        unsafe_allow_html=True,
    )

    st.markdown("### Disclaimer")
    st.markdown("Please carefully review the [Terms of Use](?doc=terms) and [Privacy Policy](?doc=privacy) before using this app. By using the app, you agree to the terms outlined in these documents.")
    st.markdown("### User Guide")
    st.markdown("Please carefully read the [User Guide](https://xintian.notion.site/TSU-AI-Assistant-User-Guide-35134913e84c80a28fa4d0e377d1aaac?source=copy_link).")
    # st.markdown(
    #     "[Privacy Policy](?doc=privacy)  \n[Terms of Use](?doc=terms)"
    # )
    # st.markdown(
    #     "The information provided by "
    #     "<span style='color: #00a9cf; font-weight: bold;'>Climate Knowledge Finder</span> "
    #     "is sourced from [OpenAlex](https://openalex.org). "
    #     "While we strive to ensure accuracy, we cannot guarantee the completeness or reliability of the data. "
    #     "Users are encouraged to verify the information independently before making decisions based on it.",
    #     unsafe_allow_html=True,
    # )
    

    # with st.expander("Azure OpenAI Settings", expanded=False):
    #     st.text_input("Endpoint", placeholder="https://<resource>.openai.azure.com/",
    #                   label_visibility="visible", key="azure_endpoint")
    #     st.text_input("API Key", placeholder="Azure OpenAI API key",
    #                   type="password", key="azure_api_key")
    #     st.text_input("Chat deployment", placeholder="e.g. gpt-4o",
    #                   key="azure_chat_deployment")
    #     st.text_input("Embedding deployment", placeholder="e.g. text-embedding-3-small",
    #                   key="azure_embed_deployment")
    #     st.text_input("API version", value="2024-12-01-preview",
    #                   key="azure_api_version")

    st.markdown("### To-do")
    st.checkbox("Add use case scenario analysis.", value=False, key="todo_use_case_scenario_analysis")

