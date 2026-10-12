import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from compliancelens import telemetry


def record(payload, code=200, failed=False):
    return telemetry.invocation_event(
        "query", "dev", {"statusCode": code, "body": json.dumps(payload)}, failed, 42.5, uuid4().hex
    )


def test_log_schema_excludes_all_free_text_and_sensitive_fields():
    value = record(
        {
            "status": "answered",
            "question": "person@example.com",
            "answer": "Account: 123456789",
            "citations": [{"text": "private"}],
            "reason": "sensitive exception",
            "run_id": "untrusted identifier",
            "retrieved": [{"text": "sensitive excerpt"}],
        }
    )
    assert value["retrieved_chunks"] == 1
    assert value["run_id"] is None and value["reason"] is None
    serialized = json.dumps(value)
    for fragment in ("person@", "123456789", "private", "sensitive", "untrusted"):
        assert fragment not in serialized


@pytest.mark.parametrize(
    "reason,guard",
    [
        ("input_injection", 1),
        ("context_injection", 1),
        ("output_pii", 1),
        ("unsafe_output_markup", 1),
        ("weak_evidence", 0),
        ("unsupported_by_context", 0),
        ("unknown private reason", 0),
    ],
)
def test_refusals_distinguish_guards_from_evidence(reason, guard):
    value = record({"status": "refused", "reason": reason})
    assert value["refusals"] == 1
    assert value["guardrail_blocks"] == guard
    assert value["errors"] == 0


@pytest.mark.parametrize(
    "code,error,rejected",
    [(400, 0, 1), (405, 0, 1), (415, 0, 1), (409, 1, 0), (502, 1, 0), (200, 0, 0)],
)
def test_error_and_rejection_denominators(code, error, rejected):
    value = record({}, code)
    assert value["requests"] == 1
    assert value["errors"] == error
    assert value["rejected_requests"] == rejected


def test_invalid_dimensions_and_nonfinite_latency_are_never_serialized():
    for stage, environment, latency in [
        ("person@example.com", "dev", 1),
        ("query", "private", 1),
        ("query", "dev", float("nan")),
    ]:
        with pytest.raises(ValueError):
            telemetry.invocation_event(stage, environment, {}, False, latency, uuid4().hex)


@pytest.fixture
def settings():
    return SimpleNamespace(
        telemetry_enabled=True,
        telemetry_namespace="ComplianceLens",
        telemetry_environment="dev",
        embedding_backend="azure",
        llm_backend="azure",
        aws_endpoint_url="http://127.0.0.1:4566",
        aws_default_region="ca-central-1",
    )


def test_telemetry_failure_preserves_result_without_exception_text(settings, monkeypatch, capsys):
    def fail(*args):
        raise RuntimeError("secret delivery failure")

    monkeypatch.setattr(telemetry, "invocation_event", fail)

    @telemetry.observe("query", lambda: settings)
    def handler(event, context):
        return {"statusCode": 400, "body": '{"error":"invalid_request"}'}

    result = handler({"body": "secret question"}, None)
    assert result["statusCode"] == 400
    output = capsys.readouterr().out
    assert "secret" not in output
    logs = [json.loads(line) for line in output.splitlines()]
    assert logs[0]["telemetry_event"] == "delivery_failed"


def test_original_handler_exception_is_preserved(settings, monkeypatch, capsys):
    error = ValueError("private failure detail")

    @telemetry.observe("parse", lambda: settings)
    def handler(event, context):
        raise error

    with pytest.raises(ValueError) as caught:
        handler({}, None)
    assert caught.value is error
    output = capsys.readouterr().out
    assert "private" not in output
    assert json.loads(output)["errors"] == 1


def test_disabled_telemetry_makes_no_network_requests(settings, monkeypatch, capsys):
    settings.telemetry_enabled = False

    @telemetry.observe("query", lambda: settings)
    def handler(event, context):
        return {}

    assert handler({}, None) == {}
    assert capsys.readouterr().out == ""


def test_emitted_event_includes_every_metric_and_zero_counters(settings, capsys):
    @telemetry.observe("query", lambda: settings)
    def handler(event, context):
        return {"statusCode": 200, "body": '{"status":"answered","retrieved":[{},{}]}'}

    handler({}, None)
    value = json.loads(capsys.readouterr().out)
    assert value["errors"] == 0 and value["requests"] == 1
    assert value["retrieved_chunks"] == 2
    assert value["latency_ms"] >= 0
    assert set(telemetry.METRICS) <= set(value)
    assert value["stage"] == "query" and value["environment"] == "dev"


def test_stdout_failure_does_not_replace_handler_result(settings, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("private stdout error")

    monkeypatch.setattr("builtins.print", fail)

    @telemetry.observe("query", lambda: settings)
    def handler(event, context):
        return {"statusCode": 400}

    assert handler({}, None) == {"statusCode": 400}
