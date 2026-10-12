# Phase 7 monitoring evidence

Completed October 11, 2026 in Toronto. Monitoring ran on Floci 2.2.0; two supported query checks used real Azure AI Foundry inference. No real AWS deployment, real Bedrock, or live Ollama inference occurred.

## Implemented monitoring

All four Lambda handlers emit one closed-schema JSON invocation event, including early ingestion failures and query validation. Events contain generated IDs, trusted enum dimensions/status/backend labels, safe reason codes, and numeric counters. Questions, excerpts, answers, citations, arbitrary report fields, and exception text are excluded before serialization. This logging boundary protects free-text fields independently of PII detector recall; provider redaction retains the known Phase 3 limitations.

CloudWatch log metric filters convert events into Requests, LatencyMs, RetrievedChunks, Refusals, GuardrailBlocks, Errors, and RejectedRequests. There are seven filters per stage, 28 per environment. Zero-valued counters are explicit; no metric-filter default values or extra dimension cardinality are introduced. Dimensions are Environment and Stage. Metrics describe Lambda invocations; CLI calls and API Gateway rejections that never invoke a function are outside coverage.

Each environment has eight single-metric alarms: Errors Sum > 0 and LatencyMs Average > 30000 for every stage, using 60-second periods, one evaluation period, and missing data notBreaching. Actions are disabled; no notifications or metric-math expressions are configured. Both environments now have 69 managed resources and repeat plans show no changes. The thresholds are demonstration defaults rather than a measured service objective.

The original direct PutMetricData approach logged an invocation but failed publication with namespace-conditioned IAM. The [Floci 2.2.0 condition resolver](https://github.com/floci-io/floci/blob/2.2.0/src/main/java/io/github/hectorvent/floci/core/common/IamConditionContextResolver.java) does not resolve cloudwatch:namespace. The final implementation uses log metric filters, retains existing log-group-scoped function permissions, and removes the attempted metric policies. Functions receive no wildcard metric grant and make no direct metric SDK calls. Telemetry/serialization/stdout failures preserve handler results and exceptions; a fixed delivery-failure event is emitted when stdout is available.

## Live application evidence

Final dev journal: data/runs/0984c6c6e78c420fa37a91173d74446b.json, covering October 12 UTC 01:50:16–01:53:08. Prod-style journal: data/runs/1c68826173754a39aeed101b3a09f607.json, covering 01:53:59–01:57:09. These are October 11 evening in Toronto.

Each environment exercised an invalid request (HTTP 400), a pre-provider injection refusal, a supported public-document answer with citations, an invalid workflow, and healthy unchanged ingestion. The healthy workflow reused all five representative chunks with zero embedding calls. All metric sums matched their corresponding invocation log fields for every stage and all seven metrics. Monitoring backend for every counter and latency below: local Floci, with Azure selected for the supported query.

| Observation per environment | Dev | Prod-style local |
| --- | --- | --- |
| Query invocations | 3 | 3 |
| Query rejections / refusals / guardrail blocks | 1 / 1 / 1 | 1 / 1 / 1 |
| Retained evidence chunks across queries | 5 | 5 |
| Query operational errors | 0 | 0 |
| Parse invocations / errors | 2 / 1 | 2 / 1 |
| Chunk / embed invocations | 1 / 1 | 1 / 1 |
| Maximum query handler latency, ms | 2881.904 | 3096.103 |
| Healthy parse / chunk / embed latency, ms | 79.405 / 276.787 / 298.002 | 77.912 / 289.675 / 293.278 |

The query latency maximum is over three distinct handler cases, including validation and injection refusal. Latency measures handler work through response/journal creation, excluding platform initialization and telemetry emission. These tiny local samples are not throughput, percentile, or production latency benchmarks. RetrievedChunks measures retained evidence count; the previously planned retrieval-score metric was not added. Similarity remains in query journals rather than being presented as confidence telemetry.

The deployed parse-errors alarm automatically entered ALARM after the invalid execution, then returned to OK after a healthy execution in the next completed period. Observed UTC transitions:

| Environment | ALARM | OK |
| --- | --- | --- |
| Dev | 01:51:09 | 01:52:09 |
| Prod-style | 01:55:08 | 01:56:08 |

All eight deployed alarms were OK at the verification snapshot. Actual request latencies did not breach the latency threshold.

## Isolated evaluator probes

Each verifier created eight temporary alarms mirroring deployed metric/statistic/period/threshold/dimensions in a unique Verification namespace. Below-threshold samples produced OK; additional error and latency samples produced ALARM; healthy samples in a later completed period produced OK. All eight clones completed this sequence in both environments. GetMetricStatistics independently showed the breaching sums/averages. No SetAlarmState call was used. All temporary alarms were deleted; their clearly synthetic metric samples remain in isolated namespaces, outside application statistics.

Dev's clone group reached OK / ALARM / OK at UTC 01:52:19 / 01:52:29 / 01:53:08; prod-style reached those states at 01:56:19 / 01:56:29 / 01:57:09. This demonstrates evaluator behavior for mirrored configurations. Only the deployed parse error alarm was driven into ALARM by actual application work; it does not claim actual latency breaches or failure transitions on every deployed stage alarm.

## Privacy and Azure usage

A separate raw-log audit checked 111 dev and 113 prod-style handler CloudWatch events. The synthetic email and actual Azure key were absent. Structured log unit tests cover free-text exclusion, known versus evidence-based refusals, invalid dimensions/nonfinite latency, disabled telemetry, preserved original exceptions, and logging failure isolation. Audit/usage journal: data/runs/45f6ec8b17d94896b0c3ea38d791dbc9.json.

All paid calls used Azure AI Foundry. Embedding model: text-embedding-3-small; chat model: gpt-5.4-mini-2026-03-17. There were two query embedding requests consuming 34 input tokens, and two chat requests consuming 2208 input and 395 output tokens. Dev chat used 197 output tokens and prod-style used 198. Usage was complete; no requests lacked reported usage. Invalid/injection/workflow checks, repeat ingestion, inspection, and synthetic metric probes made no paid provider requests. No evaluation/judge requests ran. Output caps and disabled provider retries remain unchanged. Token counts are not a dollar estimate.

## Reproduction and limits

Use the canonical build/apply commands in design-principles.md, then run:

```bash
uv run python infra/monitoring.py verify --environment dev --document-id pipeda-accountability
uv run python infra/monitoring.py verify --environment prod --document-id pipeda-accountability
uv run python infra/monitoring.py inspect --environment dev
uv run python infra/monitoring.py inspect --environment prod
uv run pytest --db-integration
terraform fmt -check -recursive infra
terragrunt hcl fmt --check --working-dir infra
uv run pre-commit run --all-files
```

The verification document must already exist in the raw bucket/index. Each command may take several minutes because alarms consider completed periods. The inspector returns projected log events, metric statistics, alarm states, and historical delivery-failure counts without making inference calls. The final image fingerprint is 0219daebbf69521db434355182141bb1c94c92aa7d1399b712b64b4b8e7de9ea.

All 182 tests including PostgreSQL integration tests passed. Both Terraform environments validated; formatting, repeat plans, Ruff, secret checks, and the Markdown naming restriction passed. Azure keys and SQL passwords remain absent from Terraform state. The original 530-chunk CLI corpus and both five-chunk application indexes are intact.

The [Floci CloudWatch documentation](https://floci.io/floci/services/cloudwatch/) describes single-metric evaluation, metric filters, limited log queries, and inert metric streams. The [2.2.0 alarm evaluator](https://github.com/floci-io/floci/blob/2.2.0/src/main/java/io/github/hectorvent/floci/services/cloudwatch/metrics/AlarmEvaluator.java) uses completed periods and a background tick; runtime transitions above are separately observed evidence. FilterLogEvents uses substring matching in Floci, while metric filters parse JSON patterns. Timed retention, delivery notifications, metric-math evaluation, real AWS security/scale, cold-start accounting, and terminated invocations without completed telemetry were not established. Missing-data policy cannot replace an unavailable handler event. Phase 8 remains not started.
