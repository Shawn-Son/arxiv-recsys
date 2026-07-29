# Contributing

## Workflow

1. Create a focused branch from `main`.
2. Keep commits small and describe the intent with Conventional Commits.
3. Add tests for behavior changes.
4. Run `npm run check`.
5. Open a pull request using the repository template.

## Engineering standards

- Do not publish an evaluation metric without its dataset manifest, baseline,
  configuration, and raw result artifact.
- Keep ingestion idempotent and restartable.
- Make ranking features inspectable and record their version.
- Treat upstream text and metadata as untrusted input.
- Include rollback instructions for schema, model, and infrastructure changes.
