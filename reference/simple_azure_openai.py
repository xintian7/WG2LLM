from openai import AzureOpenAI
import sys
from pathlib import Path

try:
    from functions.env_loader import get_azure_settings
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from functions.env_loader import get_azure_settings


def main() -> int:
    """Run a minimal Azure OpenAI chat completion smoke test."""
    settings = get_azure_settings()
    api_key = settings.get("api_key", "").strip()
    endpoint = settings.get("endpoint", "").strip()
    api_version = settings.get("api_version", "").strip()
    model = (
        settings.get("model_name", "").strip()
        or settings.get("chat_deployment", "").strip()
    )
    missing = [
        name
        for name, value in (
            ("AZURE_API_KEY", api_key),
            ("AZURE_OPENAI_ENDPOINT", endpoint),
            ("AZURE_API_VERSION", api_version),
            ("AZURE_OPENAI_MODEL_NAME", model),
        )
        if not value
    ]
    if missing:
        print("Missing Azure configuration in .env: " + ", ".join(missing))
        return 1

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=api_key,
    )

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "What is the capital of France?",
            }
        ],
        max_completion_tokens=256,
        temperature=0.0,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        model=model,
    )

    print(response.choices[0].message.content)
    return 0


if __name__ == "__main__":
    sys.exit(main())