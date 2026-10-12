# Resume evidence and wording

This compares the three original requested bullets against the completed portfolio project. It does not edit a resume. All AWS-shaped execution happened on **Floci**, with real Docker-backed PostgreSQL/Lambda execution locally. **Real LLM inference ran on Azure AI Foundry. Bedrock is mock-tested only.** Ollama chat and embeddings are transport-mocked, with a documented Windows server setup that has not been live-tested.

## 1. RAG with cited regulatory sources

Original: “A RAG assistant over OSFI, FINTRAC and PIPEDA documents with source citations, built with Python, LangChain and a vector database.”

Supported. Python and LangChain connect retrieval and generation; pgvector on Floci RDS stores ten official public documents in 530 chunks. Azure text-embedding-3-small produced the 1536-dimension vectors. Azure AI Foundry chat, reported model gpt-5.4-mini-2026-03-17, produced real cited answers through the CLI and both local APIs. Citations use stored source metadata rather than generated URLs. See [ingestion](phase-1-results.md), [RAG](phase-2-results.md) and [API evidence](phase-6-results.md).

Suggested wording: “Built a Python/LangChain RAG assistant over public OSFI, FINTRAC and PIPEDA guidance, using pgvector and Azure AI Foundry to return source-cited answers.”

Do not claim every answer is correct or always cite a source: legitimate refusals have no citations, and semantic citation quality is measured rather than guaranteed.

## 2. Serverless services and Bedrock

Original: “A serverless ingestion and query pipeline using S3, Step Functions, Lambda, API Gateway and an LLM (Bedrock), provisioned with Terraform and Terragrunt.”

Partially supported. All named AWS service interfaces and the Terraform/Terragrunt provisioning work on Floci. Both local dev/prod-style stacks execute real image-based Lambda handlers, representative public ingestion and query HTTP requests. They are AWS serverless service patterns running on a local emulator, not a deployed AWS production system. The Bedrock Converse and Titan embedding adapters have boto3 mock contract tests; no real Bedrock inference ran. Floci's canned Bedrock responses are not usable inference evidence. See [infrastructure](phase-5-results.md), [application](phase-6-results.md) and [monitoring](phase-7-results.md).

Suggested wording: “Provisioned and verified an AWS serverless ingestion/query pattern on Floci using S3, Step Functions, Lambda and API Gateway, with Terraform/Terragrunt and live Azure AI Foundry inference; implemented mock-tested Bedrock adapters.”

To close the Bedrock gap, first explicitly change the no-real-AWS constraint and approve account, region, model access and a bounded usage budget. A future real Converse/embedding smoke test would establish provider connectivity, not production deployment or benchmark quality. No such call is part of this project run. No dollar estimate is claimed without current regional/model pricing.

## 3. Safety, evaluation and monitoring

Original: “PII redaction, prompt injection guardrails, and an evaluation set that tracks answer accuracy and citation quality, with CloudWatch monitoring.”

Supported with qualifications. Local Presidio/spaCy and conservative patterns redact before Azure calls; input/context/output checks add defenses. The synthetic local assessment removed 17/21 expected PII values and detected 11/14 attacks, with missed cases and false positives. These are fixture counts from local en_core_web_sm 3.8.0 and rules, not LLM inference or general security rates. See [safety evidence](phase-3-results.md).

The 34-question development benchmark uses 30 supported questions and four expected refusals. Azure AI Foundry model gpt-5.4-mini-2026-03-17 both generates and judges; Azure text-embedding-3-small retrieves from the same 530-chunk corpus. Measured Phase 4 run 4d154436ccef4f2fa5e2b03ffc44ef87 improved judge answer acceptance from baseline 23/30 to focused-context 27/30. Focused-context citation support was 91/94 emitted claim/source pairs. These are development-set rubric scores, not independently verified legal accuracy. Defaults remain baseline pending held-out validation. See [full metric definitions and usage](../eval/results/phase-4.md).

CloudWatch logs, metric filters, statistics and single-metric alarms were verified on Floci. Real parse failures drove deployed error alarms through failure/recovery; isolated synthetic samples tested all stage error/latency configurations. Real latency breaches, notifications and real AWS CloudWatch were not tested. Retained-chunk count replaces the initially planned retrieval-score metric; similarity remains in query journals. See [Phase 7 evidence](phase-7-results.md).

Suggested wording: “Added PII redaction and prompt injection checks, a 34-question Azure-judged development evaluation for answer/citation quality, and Floci CloudWatch logs, metrics and tested error-alarm recovery.”

Remaining work: broaden Canadian PII and adversarial fixtures; add human/expert review and a held-out benchmark; live-test Windows Ollama and GPU memory use; verify latency under load and notification delivery; explicitly authorize any real AWS deployment before claiming cloud production behavior.

## Claims to avoid

- Real Bedrock inference, real AWS deployment or production readiness.
- Free Azure inference, fully offline operation before downloads, or verified Windows/GPU performance.
- Complete PII removal, injection-proof behavior or guaranteed regulatory correctness.
- An independent “90% accuracy” headline without development-set, judge, denominator and backend context.
- Treating cached responses, mocked adapters, synthetic vectors or synthetic alarm samples as fresh provider inference.
