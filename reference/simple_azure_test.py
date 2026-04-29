from openai import AzureOpenAI
import os
import sys
from pathlib import Path

import dotenv

try:
    from env_loader import get_azure_settings
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from env_loader import get_azure_settings

dotenv.load_dotenv()

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
    "Response rules:\n"
    "- For (1): answer normally in plain prose grounded in guidance text. Do NOT use the template.\n"
    "- For (2): use the exact template provided.\n"
    "- For (3): respond exactly with: This question is not related to the AI guidance.\n"
    "Always use only the provided guidance text. Do not rely on outside knowledge."
)


def answer_with_guidance(md_filename: str, question: str) -> str:
    """Return a policy answer based on the provided guidance markdown and question.

    Parameters
    ----------
    md_filename : str
        File name or relative path to the guidance markdown file.
    question : str
        User question about whether a case is permitted.

    Returns
    -------
    str
        Model response text.
    """
    api_key = os.getenv("AZURE_API_KEY", "").strip()
    if not api_key:
        raise ValueError("AZURE_API_KEY is missing. Please set it in .env.")

    guidance_path = Path(md_filename)
    if not guidance_path.is_absolute():
        local_path = Path(__file__).parent / guidance_path
        parent_path = Path(__file__).parent.parent / guidance_path
        guidance_path = local_path if local_path.exists() else parent_path

    if not guidance_path.exists():
        raise FileNotFoundError(f"Guidance file is missing: {guidance_path}")

    guidance_text = guidance_path.read_text(encoding="utf-8").strip()
    if not guidance_text:
        raise ValueError(f"Guidance file is empty: {guidance_path}")

    settings = get_azure_settings()
    endpoint = settings.get("endpoint", "").strip()
    api_version = settings.get("api_version", "").strip() or "2024-12-01-preview"
    model = (
        settings.get("model_name", "").strip()
        or settings.get("chat_deployment", "").strip()
        or "gpt-4.1-mini"
    )

    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT is missing. Please set it in .env.")

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=api_key,
    )

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
                    f"Question:\n{question}"
                ),
            },
        ],
        max_completion_tokens=256,
        temperature=0.0,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        model=model,
    )

    return (response.choices[0].message.content or "").strip()


def main(test_question: str) -> int:
    """Run a minimal Azure OpenAI guidance QA smoke test."""
    try:
        answer = answer_with_guidance(
            md_filename="AIGuidance_20260428.md",
            question=test_question,
        )
        print(answer)
        return 0
    except Exception as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    # Switch this value or add more local tests while developing.
    test_question = "Can I use openai to draft the IPCC reports?"
    # test_question = "What are the 10 UN AI principles?"
    # test_question = "What is the capital of France?"
    sys.exit(main(test_question))