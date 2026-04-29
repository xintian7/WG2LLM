# Guidance

This document introduces **WGII AI Assistant (version 0.1)** which is designed to support IPCC AR7 authors using the AI-enhanced functionalities.

## 1) What this app does

The WGII AI Assistant helps users:

- check whether a proposed AI use case is aligned with WGII AI guidance,
- view a reference figure for AI use cases,
- access Terms of Use and Privacy Policy,
- receive structured feedback for AI-use permission checks.

The app does not replace author judgment, chapter leadership decisions, or IPCC governance procedures.

## 2) Quick start

### Prerequisites

- web browser,
- internet access,
- valid Azure OpenAI settings configured by the TSU or deployment environment.

### Web app

Use the deployed WGII AI Assistant URL provided by WGII TSU.

## 3) Core controls

### Check AI use cases

- Enter a question such as: "Can I use AI to rephrase assessment text?"
- Click **Submit** to receive a guidance-based answer.
- Output is grounded in the guidance content bundled with the app.

![alt text](image.png)

### View AI use case reference

- Opens the AI use case reference figure.
- You can view and download the image.
- You can also expand the figure to a full size by clicking the button on the top left. 
![alt text](image-1.png)

### Other buttons

- **Rephrase sentences**: under development.
- **Check grammar**: under development.
- **Report a new AI use case**: under development.
- **Use case scenario analysis**: under development.

## 4) How responses are framed

For permission-check style prompts, the app returns:

1. Permission category.
2. Why (brief reason from guidance).
3. What to pay attention to (conditions, cautions, and limits).

If a question is outside the guidance scope, the app indicates that directly.

## 5) Recommended workflow

1. Draft your AI-use question in practical terms (task, context, expected output).
2. Run **Check AI use cases**.
3. Review the permission category and cautions.
4. If needed, refine your question and re-run.
5. Align your final action with WGII procedures and leadership direction.

## 6) Troubleshooting

- **No response from model**: verify endpoint, API key, deployment, and API version.
- **Unexpected answer quality**: ask a more specific question and include intended use context.

## 7) Notes

- This assistant is a support tool, not a policy authority.
- Guidance and app behavior may be updated over time.
- The tool is based on Azure OpenAI studio. 
- For questions or suggestions, contact WGII TSU.