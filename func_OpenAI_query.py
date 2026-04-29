"""Reusable Azure OpenAI query utility for AI guidance checks.

Import `query_openai_with_guidance` from this module and call it from UI or
other scripts.
"""

from pathlib import Path
import sys
import base64
import hashlib

from openai import AzureOpenAI
from cryptography.fernet import Fernet, InvalidToken

from env_loader import get_azure_settings

ANSWER_TEMPLATE = (
    "Use this exact output template:\n"
    "1) Permission category: <Permitted | Conditionally permitted | Not permitted | Unclear from guidance>\n"
    "2) Why: <Short reason grounded in the guidance text>\n"
    "3) What to pay attention to: <List specific cautions, conditions, or limits explicitly mentioned in guidance; if none are mentioned, say 'Not explicitly mentioned in the guidance.'>"
)

QUESTION_ROUTING_RULES = (
    "Classify the user question into one of three categories:\n"
    "(1) General AI questions that are covered by the guidance text's AI introduction/explanatory sections.\n"
    "(2) Permission-check questions asking whether a use/case/action is permitted.\n"
    "(3) Questions unrelated to the guidance text.\n"
    "Routing clarification: If the question is about using AI in IPCC-related work (for example brainstorming, ideation, outlining, editing, visualization support, drafting support, or analysis support), treat it as guidance-related and do NOT classify it as unrelated.\n"
    "When in doubt between (1) and (2) for an IPCC AI-use scenario, choose (2).\n"
    "Response rules:\n"
    "- For (1): answer the question directly in plain prose based on guidance. Do NOT use the numbered template.\n"
    "- For (2): use the exact numbered template provided.\n"
    "- For (3): respond exactly with: This question is not related to the AI guidance.\n"
    "Always use only the provided guidance text. Do not rely on outside knowledge."
)

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_API_VERSION = "2024-12-01-preview"
DEFAULT_GUIDANCE_FILE = "AIGuidance_20260428.md.enc"
DEFAULT_ENDPOINT = "https://azureopenaitsu.openai.azure.com/"


def _resolve_guidance_path(md_filename: str) -> Path:
    """Resolve the guidance file path from absolute or project-relative input."""
    guidance_path = Path(md_filename)
    if guidance_path.is_absolute():
        return guidance_path

    local_path = Path(__file__).parent / guidance_path
    if local_path.exists():
        return local_path

    parent_path = Path(__file__).parent.parent / guidance_path
    return parent_path


def _dedupe_non_empty(values: list[str]) -> list[str]:
    """Return non-empty unique values while preserving order."""
    output: list[str] = []
    for value in values:
        cleaned = (value or "").strip()
        if cleaned and cleaned not in output:
            output.append(cleaned)
    return output


def _derive_fernet_key(passphrase: str) -> bytes:
    """Derive a Fernet key from a passphrase using SHA-256 + urlsafe base64."""
    return base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode("utf-8")).digest())


def _load_guidance_text(guidance_path: Path) -> str:
    """Load guidance text from plaintext markdown or Fernet-encrypted token file."""
    if guidance_path.suffix == ".enc":
        settings = get_azure_settings()
        passphrase = (settings.get("fernet_key") or "").strip()
        if not passphrase:
            raise ValueError("FERNET_KEY is missing. Please set it in .env.")

        token = guidance_path.read_bytes().strip()
        if not token:
            raise ValueError(f"Guidance file is empty: {guidance_path}")

        try:
            fernet = Fernet(_derive_fernet_key(passphrase))
            return fernet.decrypt(token).decode("utf-8").strip()
        except InvalidToken as exc:
            raise ValueError("Unable to decrypt guidance file. Check FERNET_KEY in .env.") from exc

    return guidance_path.read_text(encoding="utf-8").strip()


def _normalize_answer_output(answer_text: str) -> str:
    """Enforce output style for the three routing categories.

    - Category (3): exact fixed sentence
    - Category (1): plain prose (no numbered template)
    - Category (2): keep template as generated
    """
    text = (answer_text or "").strip()
    lowered = text.lower()

    if "not related to the ai guidance" in lowered:
        return "This question is not related to the AI guidance."

    if "1) permission category:" in lowered and "general ai" in lowered:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        why = ""
        attention = ""
        for line in lines:
            l = line.lower()
            if l.startswith("2) why:"):
                why = line.split(":", 1)[1].strip() if ":" in line else ""
            elif l.startswith("3) what to pay attention to:"):
                attention = line.split(":", 1)[1].strip() if ":" in line else ""

        merged = " ".join(part for part in [why, attention] if part).strip()
        return merged or text

    return text


def query_openai_with_guidance(
    question: str,
    md_filename: str = DEFAULT_GUIDANCE_FILE,
    endpoint: str = "",
    api_key: str = "",
    api_version: str = "",
    model: str = "",
) -> str:
    """Query Azure OpenAI using guidance markdown as context.

    Parameters
    ----------
    question : str
        User question to evaluate against the guidance.
    md_filename : str, optional
        Guidance markdown file name or path.
    endpoint : str, optional
        Azure OpenAI endpoint override.
    api_key : str, optional
        Azure OpenAI API key override.
    api_version : str, optional
        API version override.
    model : str, optional
        Model override (deployment/model name).

    Returns
    -------
    str
        Assistant answer text.
    """
    if not (question or "").strip():
        raise ValueError("Question is empty.")

    guidance_path = _resolve_guidance_path(md_filename)
    if not guidance_path.exists():
        raise FileNotFoundError(f"Guidance file is missing: {guidance_path}")

    guidance_text = _load_guidance_text(guidance_path)
    if not guidance_text:
        raise ValueError(f"Guidance file is empty: {guidance_path}")

    settings = get_azure_settings()
    api_key_candidates = _dedupe_non_empty(
        [
            api_key,
            settings.get("api_key", ""),
        ]
    )
    endpoint_candidates = _dedupe_non_empty(
        [
            endpoint,
            settings.get("endpoint", ""),
            DEFAULT_ENDPOINT,
            DEFAULT_ENDPOINT.rstrip("/"),
        ]
    )
    api_version_candidates = _dedupe_non_empty(
        [
            api_version,
            settings.get("api_version", ""),
            DEFAULT_API_VERSION,
        ]
    )
    # Restrict to known-good model path only.
    model_candidates = _dedupe_non_empty(
        [
            DEFAULT_MODEL,
            settings.get("model_name", ""),
        ]
    )

    if not api_key_candidates:
        raise ValueError("AZURE_API_KEY is missing. Please set it in .env.")
    if not endpoint_candidates:
        raise ValueError("AZURE_OPENAI_ENDPOINT is missing. Please set it in .env.")

    errors: list[str] = []
    for use_key in api_key_candidates:
        for use_endpoint in endpoint_candidates:
            for use_version in api_version_candidates:
                try:
                    client = AzureOpenAI(
                        api_version=use_version,
                        azure_endpoint=use_endpoint,
                        api_key=use_key,
                    )
                    for use_model in model_candidates:
                        try:
                            response = client.chat.completions.create(
                                messages=[
                                    {
                                        "role": "system",
                                        "content": (
                                            "You are an IPCC WGII AI guidance assistant. "
                                            "Use only the provided guidance text as your knowledge base. "
                                            f"{QUESTION_ROUTING_RULES}\n\n"
                                            f"{ANSWER_TEMPLATE}"
                                        ),
                                    },
                                    {
                                        "role": "user",
                                        "content": (
                                            f"Guidance text:\n{guidance_text}\n\n"
                                            f"Question:\n{question.strip()}"
                                        ),
                                    },
                                ],
                                max_completion_tokens=256,
                                temperature=0.0,
                                top_p=1.0,
                                frequency_penalty=0.0,
                                presence_penalty=0.0,
                                model=use_model,
                            )
                            answer_text = (response.choices[0].message.content or "").strip()
                            return _normalize_answer_output(answer_text)
                        except Exception as model_exc:
                            errors.append(
                                f"endpoint={use_endpoint}, api_version={use_version}, model={use_model}: {model_exc}"
                            )
                except Exception as client_exc:
                    errors.append(
                        f"endpoint={use_endpoint}, api_version={use_version}, client_init: {client_exc}"
                    )

    raise RuntimeError(
        "Unable to reach Azure OpenAI with current settings. Tried fallback combinations in func_OpenAI_query. "
        f"Last error: {errors[-1] if errors else 'Unknown error'}"
    )


def answer_with_guidance(md_filename: str, question: str) -> str:
    """Backward-compatible wrapper for older imports."""
    return query_openai_with_guidance(question=question, md_filename=md_filename)


def main(test_question: str) -> str:
    """Return answer text for a question using default guidance/settings."""
    return query_openai_with_guidance(
        question=test_question,
        md_filename=DEFAULT_GUIDANCE_FILE,
    )


def _cli_main(test_question: str) -> str:
    """Return answer text for a quick CLI-style query."""
    return main(test_question)


if __name__ == "__main__":
    test_question = "Can I use openai to draft the IPCC reports?"
    if len(sys.argv) > 1:
        test_question = " ".join(sys.argv[1:]).strip() or test_question
    try:
        print(_cli_main(test_question))
        sys.exit(0)
    except Exception as exc:
        print(str(exc))
        sys.exit(1)