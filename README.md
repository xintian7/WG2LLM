# WG2LLM
placeholder; handbook + editorial 

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
