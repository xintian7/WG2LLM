from openai import AzureOpenAI
import os
import sys

import dotenv

dotenv.load_dotenv()

endpoint = "https://azureopenaitsu.openai.azure.com/"
model_name = "gpt-4.1-mini"
deployment = "gpt-4.1-mini"


def main() -> int:
    """Run a minimal Azure OpenAI chat completion smoke test."""
    api_key = os.getenv("AZURE_API_KEY", "").strip()
    if not api_key:
        print("AZURE_API_KEY is missing. Please set it in .env.")
        return 1

    client = AzureOpenAI(
        api_version="2024-12-01-preview",
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
        model=deployment,
    )

    print(response.choices[0].message.content)
    return 0


if __name__ == "__main__":
    sys.exit(main())