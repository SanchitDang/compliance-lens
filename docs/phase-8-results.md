# Phase 8 final verification

Status: in progress; local checks passed, GitHub CI pending publication.

Verification date: October 11, 2026 in Toronto (October 12 UTC). This phase adds CI, a concise README/diagram, canonical Mac Azure and Windows Ollama server instructions, and the [resume evidence report](resume-gap-report.md). No resume was edited.

## Clean setup and checks

An isolated temporary checkout contained only registered source files and a copy of .env.example, with no private .env, downloaded corpus, caches, state or generated Lambda image. A fresh Python 3.12.15 environment installed the locked dependencies. config-check, Ruff lint/format and all pre-commit hooks passed. A separate temporary pgvector/pgvector:pg16 Docker container used the example's dummy database settings and a generated loopback port. All 182 tests, including 13 PostgreSQL integration cases, passed. Providers were mocked in tests; no hosted inference occurred in this clean check. Both spike and platform Terraform configurations passed init -backend=false -lockfile=readonly and validate using the committed AWS 6.68.0/archive 2.8.1 locks. The temporary checkout, virtual environment and database were removed.

The existing Mac workspace independently passed all 182 tests, Ruff, Compose configuration and Terragrunt HCL formatting. Both dev/prod-style Terragrunt validations passed and repeat plans returned no changes (exit 0). The first GitHub Linux Python jobs passed all checks. Terraform init downloaded the pinned provider, but read-only validate rejected the unpacked Linux package because only Mac unpacked hashes were present in the committed locks. Signed darwin_arm64/linux_amd64 hashes are being added without changing versions; a corrected complete run is pending. Linux results do not establish Windows compatibility. The full ARM64 image build, Floci provisioning, workflow/API requests and automatic alarms remain the real checks recorded in [Phase 6](phase-6-results.md) and [Phase 7](phase-7-results.md); this documentation phase does not repeat destructive setup or alarm probes. Monitoring inspect worked for both environments, with all deployed alarms OK; its recent window was empty, so that observation is not another transition test.

## Corpus, safety and inference usage

Ingestion run 8482ca4e40ba4af8ae91f3b8f940d6d6 reused all 530 chunks across ten documents. The stored identity was Azure text-embedding-3-small, dimension 1536; there were zero new embedding requests/tokens. The existing HNSW index was preserved. Query guard run 66c24eb7d0ed4436bd7b5082358587fa refused a known injection with zero chat or embedding requests. These are local reuse/guard checks, not new embedding inference.

Local safety run 33b7e32dd4f44ee4901099316c5bab70 repeated the fixture counts: query redaction removed 17/21 expected values, injection patterns caught 11/14 attacks, one of nine benign controls was flagged and one was altered by redaction. Backend was local Presidio 2.2.364, spaCy 3.8.16/en_core_web_sm 3.8.0 plus versioned patterns; no LLM produced these numbers and no synthetic PII went to Azure. Misses and false positives remain [documented](phase-3-results.md).

Baseline evaluation run a49842c85e0e44a7af8b44b292612bfa completed 34 questions against the same 530-chunk corpus with top-k 6 and similarity gate 0.30. Answer/judge backend was Azure AI Foundry, reported model gpt-5.4-mini-2026-03-17, API 2024-12-01-preview, 2048 output-token cap. Embedding identity was Azure text-embedding-3-small, 1536 dimensions. Exact gold retrieval was 28/30, judge answer acceptance 23/30, citation support 90/96 emitted claim/source pairs, unsupported refusals 4/4, with zero failed questions/missing judgments. These match the historical Phase 4 baseline; [metric definitions and three-variant comparison](../eval/results/phase-4.md) remain the owner of the original results. This is mostly cached replay, not an independent or held-out evaluation.

| Role/backend | New requests | New input tokens | New output tokens | Cache hits |
| --- | ---: | ---: | ---: | ---: |
| Azure text-embedding-3-small query vectors | 0 | 0 | 0 | 34 |
| Azure gpt-5.4-mini-2026-03-17 answers | 1 | 1161 | 108 | 32 |
| Azure gpt-5.4-mini-2026-03-17 judgments | 0 | 0 | 0 | 29 |

One weak-evidence query skips chat, and refused supported output skips judging, so cache-hit denominators differ. The uncached answer was withheld by output PII checks and not stored, as required by the cache policy. Reported usage is complete for this phase. Cached answer tokens (41394 input/3206 output) and cached judge tokens (32012 input/1219 output) belong to original requests and are not new charges. No new embeddings or judge calls were needed. Exact monetary charges depend on Azure deployment pricing; no dollar estimate is asserted. Per-run journals remain ignored under data/runs.

## CI and reproduction

The workflow runs on dev/main pushes and PRs into main, with read-only contents permission, full action commit pins and bounded timeouts. It uses uv 0.12.24, locked Python dependencies, an isolated database and Terraform 1.16.4. Database bootstrap settings are read from .env.example instead of duplicated credentials. It needs no Azure or AWS secrets and makes no provider inference, Terraform apply or Floci deployment calls. Public dependency/provider/container downloads still need network access.

Canonical commands, including build/apply and Windows listener/firewall instructions, live in [design principles](design-principles.md). Final local reproduction:

```bash
uv sync --locked --group dev
uv run compliancelens config-check
uv run pytest --db-integration
uv run pre-commit run --all-files
terraform fmt -check -recursive infra
terragrunt hcl fmt --check --working-dir infra
RETRIEVAL_TOP_K=6 uv run compliancelens eval --variant baseline
```

Existing configured local PostgreSQL is needed for --db-integration. A fresh corpus/cache requires ingestion and paid Azure evaluation. Do not refresh caches just to repeat scores. An example-only config-check is not authentication proof. Windows/Ollama setup follows [official Ollama configuration](https://docs.ollama.com/faq) and [Microsoft firewall documentation](https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallrule), but no Windows machine or live Ollama provider was available to test it. The Python adapters are transport-mocked only; GPU fit is not measured. Bedrock is mock-tested only, all AWS execution is on Floci, and no real AWS deployment or production readiness is claimed.

Deviations: CI uses independent pgvector for deterministic SQL tests; full Floci runtime verification remains local rather than being silently claimed as CI coverage. The first CI failure exposed missing Linux unpacked provider hashes and prompted a signed cross-platform lock update, with versions unchanged. Phase 8 repeats only the baseline to limit Azure spend; the measured wider/focused comparison remains the unchanged Phase 4 artifact. Windows verification remains an explicit gap, not a success claim.
