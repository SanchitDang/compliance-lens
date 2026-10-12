import json
import math
import time
from collections.abc import Callable
from functools import wraps
from typing import Any
from uuid import UUID, uuid4

from compliancelens.config import Settings

METRICS = {
    "requests": ("Requests", "Count"),
    "latency_ms": ("LatencyMs", "Milliseconds"),
    "retrieved_chunks": ("RetrievedChunks", "Count"),
    "refusals": ("Refusals", "Count"),
    "guardrail_blocks": ("GuardrailBlocks", "Count"),
    "errors": ("Errors", "Count"),
    "rejected_requests": ("RejectedRequests", "Count"),
}
REASONS = {
    "input_injection",
    "context_injection",
    "weak_evidence",
    "unsupported_by_context",
    "incomplete_or_filtered_output",
    "invalid_output",
    "invalid_citations",
    "output_pii",
    "unsafe_output_markup",
    "output_injection",
    "invalid_request",
    "method_not_allowed",
    "unsupported_media_type",
    "index_identity_mismatch",
    "query_failed",
}
GUARD_REFUSALS = {
    "input_injection",
    "context_injection",
    "incomplete_or_filtered_output",
    "invalid_output",
    "invalid_citations",
    "output_pii",
    "unsafe_output_markup",
    "output_injection",
}
STAGES = {"parse", "chunk", "embed", "query"}


def invocation_event(
    stage: str,
    environment: str,
    result: Any,
    failed: bool,
    latency_ms: float,
    invocation_id: str,
) -> dict[str, Any]:
    if stage not in STAGES or environment not in {"dev", "prod"}:
        raise ValueError("Telemetry dimensions must be registered enums")
    if not math.isfinite(latency_ms) or latency_ms < 0:
        raise ValueError("Telemetry latency must be finite and nonnegative")
    result = result if isinstance(result, dict) else {}
    body = result
    code = result.get("statusCode")
    code = code if type(code) is int and 100 <= code <= 599 else None
    if stage == "query":
        raw = result.get("body")
        try:
            body = json.loads(raw) if isinstance(raw, str) and len(raw) <= 128000 else {}
        except ValueError:
            body = {}
        body = body if isinstance(body, dict) else {}
    error = failed or code == 409 or (code is not None and code >= 500)
    rejected = code in {400, 405, 415}
    refused = not error and not rejected and body.get("status") == "refused"
    reason = body.get("reason") or body.get("error")
    reason = reason if isinstance(reason, str) and reason in REASONS else None
    if failed:
        reason = "handler_exception"
    retrieved = body.get("retrieved")
    count = min(len(retrieved), 20) if isinstance(retrieved, list) else 0
    status = (
        "error"
        if error
        else "rejected"
        if rejected
        else "refused"
        if refused
        else ("answered" if body.get("status") == "answered" else "completed")
    )
    run_id = body.get("run_id")
    try:
        run_id = UUID(run_id).hex if isinstance(run_id, str) else None
    except ValueError:
        run_id = None
    return {
        "telemetry_event": "invocation",
        "invocation_id": UUID(invocation_id).hex,
        "stage": stage,
        "environment": environment,
        "status": status,
        "reason": reason,
        "run_id": run_id,
        "http_status": code,
        "requests": 1,
        "latency_ms": round(latency_ms, 3),
        "retrieved_chunks": count,
        "refusals": int(refused),
        "guardrail_blocks": int(refused and reason in GUARD_REFUSALS),
        "errors": int(error),
        "rejected_requests": int(rejected),
    }


def observe(stage: str, settings_factory: Callable[[], Settings]) -> Callable:
    def decorate(handler: Callable) -> Callable:
        @wraps(handler)
        def observed(event: dict, context: Any) -> dict:
            started = time.perf_counter()
            result, failed = None, False
            invocation_id = uuid4().hex
            try:
                result = handler(event, context)
                return result
            except Exception:
                failed = True
                raise
            finally:
                elapsed = (time.perf_counter() - started) * 1000
                try:
                    settings = settings_factory()
                    if getattr(settings, "telemetry_enabled", False):
                        record = invocation_event(
                            stage,
                            settings.telemetry_environment,
                            result,
                            failed,
                            elapsed,
                            invocation_id,
                        )
                        for field, value in (
                            ("embedding_backend", settings.embedding_backend),
                            ("chat_backend", settings.llm_backend),
                        ):
                            record[field] = (
                                value if value in {"azure", "ollama", "bedrock"} else None
                            )
                        print(json.dumps(record, allow_nan=False), flush=True)
                except Exception:
                    try:
                        print(
                            json.dumps(
                                {
                                    "telemetry_event": "delivery_failed",
                                    "invocation_id": invocation_id,
                                }
                            ),
                            flush=True,
                        )
                    except Exception:
                        pass

        return observed

    return decorate
