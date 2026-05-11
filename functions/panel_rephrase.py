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


def _looks_like_list(text: str) -> bool:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    list_line_count = sum(
        1
        for line in lines
        if re.match(r"^(?:[-*•]|\d+[.)])\s+", line)
    )
    return list_line_count >= 2


def _wrap_in_double_braces(text: str) -> str:
    return f"{{{{{text}}}}}"


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
        "The provided input is source text to edit. "
        "If it is English, rephrase the text in clear, formal, precise scientific prose, "
        "aligned with the style commonly used in IPCC AR6 and the concise academic patterns in https://www.phrasebank.manchester.ac.uk/"
        "used in phrasebank-style writing. Use British English spelling, punctuation, and style. "
        "Keep original meaning, evidence, and level of "
        "certainty unchanged. Do not add new facts, sources, numbers, or claims. "
        "Return only the rephrased text without explanation or markdown."
    )

    wrapped_text = _wrap_in_double_braces(text)
    user_prompt = (
        "Rephrase only the text enclosed in double braces {{ and }}. "
        "Treat enclosed content as plain prose to rewrite in one continuous passage.\n"
        f"{wrapped_text}"
    )

    source_text = text or ""
    source_is_single_paragraph = len([ln for ln in source_text.splitlines() if ln.strip()]) <= 1

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=DEFAULT_MODEL,
        temperature=0,
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

    if source_is_single_paragraph and _looks_like_list(rephrased):
        retry_prompt = (
            "Rephrase only the text enclosed in double braces {{ and }}. "
            "Keep the output as one paragraph only. Do not use bullets, numbering, or list formatting. "
            "Keep short leading label-like phrases (for example text ending with a colon) as part of the paragraph.\n"
            f"{wrapped_text}"
        )

        retry_response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": retry_prompt},
            ],
            model=DEFAULT_MODEL,
            temperature=0,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            max_completion_tokens=1200,
        )

        retry_text = (retry_response.choices[0].message.content or "").strip()
        retry_usage = getattr(retry_response, "usage", None)
        retry_input = getattr(retry_usage, "prompt_tokens", None) if retry_usage is not None else None
        retry_output = getattr(retry_usage, "completion_tokens", None) if retry_usage is not None else None

        if isinstance(retry_input, int):
            token_input = (token_input or 0) + retry_input
        if isinstance(retry_output, int):
            token_output = (token_output or 0) + retry_output

        if retry_text == "__NON_ENGLISH__":
            return False, "Please input English text only.", token_input, token_output

        if retry_text:
            rephrased = retry_text

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
    st.warning(
        "⚠️ Authors are responsible for verifying and proofreading LLM-rephrased text "
        "before including it into the AR7 report."
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
