# Content filtering

The live Foundry deployment uses the platform
`Microsoft.DefaultV2` content-filter policy. The model name and version remain
in `config/models.json`, not in public UI copy.

Practice mode does not call a model. It returns a fixed briefing shape from
safe test records.

The app also:

1. accepts saved scenarios instead of arbitrary prompts;
2. bounds input, output, request rate, and result size;
3. allows only approved citations in the review request; and
4. treats document text and tool results as untrusted input.

Content filtering is one control, not proof that every unsafe response will be
blocked. A staff member still verifies the briefing.

