resource "aws_cloudwatch_log_metric_filter" "invocations" {
  for_each       = local.filter_specs
  name           = local.names.metric_filters[each.key]
  log_group_name = aws_cloudwatch_log_group.functions[each.value.stage].name
  pattern        = "{ $.telemetry_event = \"invocation\" }"
  metric_transformation {
    name       = each.value.name
    namespace  = var.telemetry_namespace
    value      = "$.${each.value.field}"
    unit       = each.value.unit
    dimensions = { Environment = "$.environment", Stage = "$.stage" }
  }
}
resource "aws_cloudwatch_metric_alarm" "stages" {
  for_each            = local.alarm_specs
  alarm_name          = local.names.alarms[each.key]
  namespace           = var.telemetry_namespace
  metric_name         = each.value.metric
  statistic           = each.value.statistic
  period              = 60
  evaluation_periods  = 1
  threshold           = each.value.threshold
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  actions_enabled     = false
  dimensions          = { Environment = var.environment, Stage = each.value.stage }
}
