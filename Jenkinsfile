// Pipeline da plataforma (Shared Library "platform", repo devops-platform/jenkins-lib).
// PRs e branches: validação, CI (docker build --target test, com terraform fmt/validate),
// pip-audit e Trivy.
// main: build e smoke test da imagem da Lambda, release (semantic-release), rebuild do
// portfolio e rebuild semanal. Sem deploy: a infra vai para a AWS pelo Terraform, à mão.
@Library('platform') _

appPipeline(
    name: 'serverless-chatbot-aws',
    deployBranch: 'main',
    deploy: false,
    // Sem lockfile: o pip-audit resolve as faixas do requirements da Lambda.
    pipAuditFile: 'infra/lambdas/orchestrator/requirements.txt',
    notify: [[repo: 'ntsation/portfolio', event: 'rebuild']],
)
