import json
import re
from typing import Callable

import streamlit as st
import streamlit.components.v1 as components
from openai import AzureOpenAI

from functions.env_loader import get_azure_settings
from functions.func_OpenAI_query import DEFAULT_MODEL
from functions.write2notion import write_to_notion


def _count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text or ""))


def _rephrase_with_ai(text: str) -> tuple[bool, str, int | None, int | None]:
    settings = get_azure_settings()
    client = AzureOpenAI(
        api_version=settings.get("api_version") or "2024-12-01-preview",
        azure_endpoint=settings.get("endpoint") or "",
        api_key=settings.get("api_key") or "",
    )

    system_prompt = (
        "You are an expert academic rephrasing assistant for IPCC-style writing. "
        "If the user input is not English, respond exactly with: __NON_ENGLISH__. "
        "If it is English, rephrase the text in clear, formal, precise scientific prose, "
        "aligned with the style commonly used in IPCC AR6 and the concise academic patterns "
        "used in phrasebank-style writing. Keep original meaning, evidence, and level of "
        "certainty unchanged. Do not add new facts, sources, numbers, or claims. "
        "Return only the rephrased text without explanation or markdown."
    )

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text.strip()},
        ],
        model=DEFAULT_MODEL,
        temperature=0.0,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        max_completion_tokens=1200,
    )

    rephrased = (response.choices[0].message.content or "").strip()
    usage = getattr(response, "usage", None)
    token_input = getattr(usage, "prompt_tokens", None) if usage is not None else None
    token_output = getattr(usage, "completion_tokens", None) if usage is not None else None
    if not isinstance(token_input, int):
        token_input = None
    if not isinstance(token_output, int):
        token_output = None

    if rephrased == "__NON_ENGLISH__":
        return False, "Please input English text only.", token_input, token_output

    return True, rephrased, token_input, token_output


def render_rephrase_panel(get_client_ip: Callable[[], str]) -> None:
    st.divider()
    st.markdown("<h3 style='text-align:center'>Rephrase sentences</h3>", unsafe_allow_html=True)
    st.markdown(
        "Input English text (up to 300 words). The app will suggest a rephrased version "
        "in a formal style documented in the [academic phrasebank](https://www.phrasebank.manchester.ac.uk/) "
        "published by the University of Manchester."
    )

    if "rephrase_output_text_editable" not in st.session_state:
        st.session_state["rephrase_output_text_editable"] = st.session_state.get("rephrase_output_text", "")

    rephrase_input_text = st.text_area(
        "Input text (English only, max 300 words)",
        key="rephrase_input_text",
        value="",
        height=260,
    )
    rephrase_word_count = _count_words(rephrase_input_text)
    st.caption(f"Word count: {rephrase_word_count} / 300")
    share_rephrase_with_tsu = st.checkbox(
        "Share my prompts and results with TSU for App improvement (optional)",
        key="rephrase_share_prompt",
        value=True,
    )

    if st.button("Rephrase text", key="rephrase_submit", type="primary"):
        if not rephrase_input_text.strip():
            st.error("Please enter text to rephrase.")
        elif rephrase_word_count > 300:
            st.error("Input is too long. Please limit to 300 words.")
        else:
            with st.spinner("Rephrasing text..."):
                try:
                    ok, rephrased_or_msg, token_input, token_output = _rephrase_with_ai(rephrase_input_text)
                except Exception as exc:
                    st.error(f"Rephrasing failed: {exc}")
                    ok = False
                    rephrased_or_msg = ""
                    token_input = None
                    token_output = None

            if ok:
                st.session_state["rephrase_output_text"] = rephrased_or_msg
                st.session_state["rephrase_output_text_editable"] = rephrased_or_msg
                if rephrase_input_text.strip():
                    try:
                        question_to_log = rephrase_input_text if share_rephrase_with_tsu else ""
                        answer_to_log = rephrased_or_msg if share_rephrase_with_tsu else ""
                        write_to_notion(
                            question_to_log,
                            get_client_ip(),
                            answer_to_log,
                            app_name="TSU_LLM_rephrase",
                            token_input=token_input,
                            token_output=token_output,
                        )
                    except Exception as exc:
                        st.warning(f"Notion logging failed: {exc}")
            else:
                st.error(rephrased_or_msg)

    st.text_area(
        "Rephrased text",
        key="rephrase_output_text_editable",
        height=260,
    )
    rephrase_copy_payload = json.dumps(st.session_state.get("rephrase_output_text_editable", ""))
    components.html(
        f"""
        <button id=\"copy-rephrase-text-btn\" style=\"
            background:#1f77b4;
            color:#fff;
            border:1px solid #1f77b4;
            border-radius:6px;
            padding:6px 10px;
            font-size:13px;
            cursor:pointer;
        \">Copy text</button>
        <script>
          const btn = document.getElementById('copy-rephrase-text-btn');
          btn.addEventListener('click', async () => {{
            try {{
              await navigator.clipboard.writeText({rephrase_copy_payload});
              btn.innerText = 'Copied';
              setTimeout(() => btn.innerText = 'Copy text', 1200);
            }} catch (e) {{
              btn.innerText = 'Copy failed';
              setTimeout(() => btn.innerText = 'Copy text', 1200);
            }}
          }});
        </script>
        """,
        height=42,
    )
