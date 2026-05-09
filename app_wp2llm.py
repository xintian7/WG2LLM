import streamlit as st
from pathlib import Path
from functions.feedback_form import FeedbackConfig, render_feedback_form
from functions.main_buttons import render_main_buttons
from functions.panel_ai_guidance import render_ai_guidance_panel
from functions.panel_grammar import render_grammar_panel
from functions.panel_reference import render_ai_use_case_reference
from functions.panel_rephrase import render_rephrase_panel


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
:root {
    --btn-blue: #1f77b4;
    --btn-blue-hover: #166aa3;
    --btn-gray: #8f98a3;
    --btn-gray-hover: #7f8893;
}

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
    background-color: var(--btn-blue);
    color: #ffffff;
    border: 1px solid var(--btn-blue);
    min-height: 40px;
    padding: 0.4rem 1rem;
    font-size: 0.95rem;
    white-space: nowrap;
}

div.stButton > button[kind="primary"]:hover {
    background-color: var(--btn-blue-hover);
    border-color: var(--btn-blue-hover);
}

div.stButton > button[kind="secondary"] {
    background-color: var(--btn-blue);
    color: #ffffff;
    border: 1px solid var(--btn-blue);
    min-height: 40px;
    padding: 0.4rem 1rem;
    font-size: 0.95rem;
    white-space: nowrap;
}

div.stButton > button[kind="secondary"]:hover {
    background-color: var(--btn-blue-hover);
    border-color: var(--btn-blue-hover);
}

div[data-testid="stFormSubmitButton"] button,
div.stDownloadButton > button {
    background-color: var(--btn-blue);
    color: #ffffff;
    border: 1px solid var(--btn-blue);
    min-height: 40px;
    padding: 0.4rem 1rem;
    font-size: 0.95rem;
}

.st-key-main_btn_ai_guidance button,
.st-key-main_btn_rephrase button,
.st-key-main_btn_grammar button,
.st-key-main_btn_reference button,
.st-key-main_btn_report button,
.st-key-main_btn_analysis button {
    min-height: 48px;
    padding: 0.5rem 1.25rem;
    font-size: 1rem;
}

.st-key-main_btn_analysis button {
    background-color: var(--btn-gray) !important;
    border: 1px solid var(--btn-gray) !important;
    color: #ffffff !important;
}

.st-key-main_btn_analysis button:hover {
    background-color: var(--btn-gray-hover) !important;
    border-color: var(--btn-gray-hover) !important;
}

div[data-testid="stTextArea"] textarea {
    font-family: "Source Sans Pro", sans-serif;
    font-size: 1rem;
    line-height: 1.6;
}

</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">WGII AI Assistant &#129302;</div>', unsafe_allow_html=True)


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


def render_feedback_page() -> None:
    st.divider()
    render_feedback_form(FeedbackConfig(form_key="feedback_form_page"))
    st.markdown("[Back to WGII AI Assistant](?)")


query_params = st.query_params
doc_key = query_params.get("doc")
if doc_key:
    render_text_document_page(str(doc_key))
    st.stop()

page_key = query_params.get("page")
if page_key == "feedback":
    render_feedback_page()
    st.stop()


active_panel = render_main_buttons()

if active_panel == "ai_guidance":
    render_ai_guidance_panel(_get_client_ip)
elif active_panel == "view_use_cases":
    render_ai_use_case_reference()
elif active_panel == "report_use_case":
    render_feedback_form(
        FeedbackConfig(
            app_name="TSU_LLM_ReportNewUseCase",
            form_key="report_use_case_form",
            title="Report a new AI use case",
            show_divider=True,
            center_title=True,
            intro_text=(
                "Please share new AI use cases that you think should be included in the AI guidance use case reference. "
                "Our WGII TSU will discuss and review all cases carefully and get "
                "back to you if you indicate that we can contact you."
            ),
            required_prompt_label="New AI use case *",
            submit_button_type="primary",
        )
    )
elif active_panel == "rephrase":
    render_rephrase_panel(_get_client_ip)
elif active_panel == "grammar":
    render_grammar_panel(_get_client_ip)
elif active_panel in ("use_case_scenario_analysis",):
    label_map = {
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
    st.markdown("### Give feedback")
    st.markdown("Please share your questions or suggestions using the [feedback form](?page=feedback). For other general questions, please contact tsu@ipccwg2.org.")
    st.markdown("### Other WGII TSU Apps")
    st.markdown("- [WGII Literature App](https://wg2literature.streamlit.app/)")
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
    st.checkbox("Add use case scenario analysis. （v0.2）", value=False, key="todo_use_case_scenario_analysis")
    st.checkbox("Add feature report new AI cases. （v0.2）", value=False, key="todo_report_new_ai_cases")
    st.checkbox("Add feature check grammar. （v0.3）", value=False, key="todo_check_grammar")
    st.checkbox("Add feature rephrase sentences. （v0.4）", value=False, key="todo_rephrase_sentences")
    st.checkbox("General maintenance. （v0.5）", value=False, key="todo_maintenance")
    st.checkbox("Add more models from Azure OpenAI, Mistral, Claude, etc. （v0.6）", value=False, key="todo_more_models")
    st.checkbox("Content comparison between AR7 and AR6. （v0.7）", value=False, key="todo_content_comparison")

