# Content filtering

The current Practice build does not call an AI model. It uses fixed templates and
deterministic facts.

Before Foundry is connected:

1. select the model in `config/models.json`;
2. keep platform content filters on;
3. bound input, output, tool calls, and retrieval; and
4. treat document text and tool results as untrusted data.

No exception is active.

