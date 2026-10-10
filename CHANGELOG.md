# CHANGELOG

<!-- version list -->

## v1.0.4 (2026-10-10)

### Bug Fixes

- **docker**: Patch base image CVEs and drop aws-lambda-rie
  ([#44](https://github.com/thentsation/serverless-chatbot-aws/pull/44),
  [`1f6c78f`](https://github.com/thentsation/serverless-chatbot-aws/commit/1f6c78fd8cb9c1f1e00b37f20d68852ca2d97f7f))

- **docker**: Upgrade OS packages from latest AL2023 release
  ([#44](https://github.com/thentsation/serverless-chatbot-aws/pull/44),
  [`1f6c78f`](https://github.com/thentsation/serverless-chatbot-aws/commit/1f6c78fd8cb9c1f1e00b37f20d68852ca2d97f7f))

### Chores

- **ci**: Bump hashicorp/setup-terraform from 3 to 4
  ([`f661f4f`](https://github.com/thentsation/serverless-chatbot-aws/commit/f661f4fb2cabbc62dcab61ab272e1bae938cdca7))

- **deps**: Bump dotenv from 16.6.1 to 18.0.3 in /scripts
  ([`4b99d5f`](https://github.com/thentsation/serverless-chatbot-aws/commit/4b99d5fb91e3713b23ae0dc103c9f444bd67a302))

- **deps**: Ignore node-fetch 3 in dependabot
  ([`81e15a4`](https://github.com/thentsation/serverless-chatbot-aws/commit/81e15a493d87c86fde5336cc3a521dc9de5ab00a))

- **deps**: Update boto3 requirement in /infra/lambdas/orchestrator
  ([#42](https://github.com/thentsation/serverless-chatbot-aws/pull/42),
  [`2cf13eb`](https://github.com/thentsation/serverless-chatbot-aws/commit/2cf13eb94742be8f8e6aa462cba427a443b95aa0))

- **deps**: Update boto3 requirement in /infra/lambdas/orchestrator
  ([#29](https://github.com/thentsation/serverless-chatbot-aws/pull/29),
  [`1c578f9`](https://github.com/thentsation/serverless-chatbot-aws/commit/1c578f91067f8dda1560d4894b3d733a05dac953))

- **deps**: Update botocore requirement in /infra/lambdas/orchestrator
  ([#28](https://github.com/thentsation/serverless-chatbot-aws/pull/28),
  [`60aa9de`](https://github.com/thentsation/serverless-chatbot-aws/commit/60aa9def095d32ca86dc0591786f1bfe271a36b2))

- **deps**: Update dependency mypy to v2.4.0
  ([#37](https://github.com/thentsation/serverless-chatbot-aws/pull/37),
  [`1ebaa30`](https://github.com/thentsation/serverless-chatbot-aws/commit/1ebaa301e23b47d6451eaf202e74e19c1ff7a301))

- **deps**: Update dependency ruff to v0.16.10
  ([#36](https://github.com/thentsation/serverless-chatbot-aws/pull/36),
  [`90d9712`](https://github.com/thentsation/serverless-chatbot-aws/commit/90d971238bb86b24c5a51e06258e555e030ab43f))

- **deps**: Update terraform aws to v6.67.0
  ([#38](https://github.com/thentsation/serverless-chatbot-aws/pull/38),
  [`33b4d2f`](https://github.com/thentsation/serverless-chatbot-aws/commit/33b4d2fd6ae073b85487d9cf615d4f472836a3f9))

### Continuous Integration

- Pipeline da Shared Library da plataforma e Renovate
  ([#35](https://github.com/thentsation/serverless-chatbot-aws/pull/35),
  [`6a229de`](https://github.com/thentsation/serverless-chatbot-aws/commit/6a229dee2d45c14d0d5417527e83f3a00e66ca57))


## v1.0.3 (2026-09-28)

### Bug Fixes

- Use RELEASE_PAT so dependabot auto-merge can write to PRs
  ([`fc8f723`](https://github.com/thentsation/serverless-chatbot-aws/commit/fc8f723421e2405d575f8309e9252e20b4b45701))


## v1.0.2 (2026-09-26)

### Bug Fixes

- Broaden Trivy's pip/_vendor skip-dirs glob
  ([`57e22fc`](https://github.com/thentsation/serverless-chatbot-aws/commit/57e22fc6cf621d6b6269ad8d52731eeb5b59407a))


## v1.0.1 (2026-09-26)

### Bug Fixes

- Invalid workflow triggers and tfsec hard-failing on pre-existing findings
  ([`4392986`](https://github.com/thentsation/serverless-chatbot-aws/commit/43929864605e8e4fe4337c0518011c7b4599e5dd))

### Chores

- **deps**: Bump lambda/python in /infra/lambdas/orchestrator
  ([#27](https://github.com/thentsation/serverless-chatbot-aws/pull/27),
  [`115ce74`](https://github.com/thentsation/serverless-chatbot-aws/commit/115ce7473b3bb5662ea5f64b7dbe2cd116e1ec3b))
