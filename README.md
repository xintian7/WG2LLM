# WG2LLM
placeholder; handbook + editorial 

## WGII's AI principles and AI use case reference

The **WGII's AI principles** and **AI use case reference** panels render sections
11.5 and 11.6 directly from `userhandbook/sections-11-5-11-6.html`. **Check AI
use cases** also uses these sections as its guidance and sends them to the
configured Azure OpenAI service with each question. Edit that file to update the
content; it must be present wherever the app is deployed. The two panel buttons
are marked with a **NEW** badge.

## Rephrase sentences and check grammar

Both model selectors default to `gpt-6.1-sol` and exclude GPT-4.1
models (including `gpt-4.1-mini`). Other configured models remain available,
and the AI guidance model is unchanged. This deployment uses
`https://azureopenaitsu.openai.azure.com/` with API version `2024-12-01-preview`
and the existing `AZURE_API_KEY` (or `AZURE_OPENAI_KEY`) environment variable.
The key must have access to that Azure resource. Credentials are not stored in
source code.

## Model labels

The model selectors in Check AI use cases, Rephrase sentences, and Check grammar
append `(with Data and Information Protection under GDPR and ISO27001)` to each
displayed model name. This is display-only wording; deployment names sent to
Azure and recorded in logs are unchanged.

Run the panel regression tests with:

```sh
python -m unittest discover -s tests -p 'test_panel_*.py'
```
