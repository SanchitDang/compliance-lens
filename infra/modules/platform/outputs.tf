output "names" { value = local.names }
output "buckets" { value = { for key, bucket in aws_s3_bucket.artifacts : key => bucket.id } }
output "functions" { value = { for key, function in aws_lambda_function.stages : key => function.arn } }
output "workflow_arn" { value = aws_sfn_state_machine.ingestion.arn }
output "database" { value = { address = aws_db_instance.vectors.address, port = aws_db_instance.vectors.port, name = var.database_name, user = var.database_user } }
output "api_id" { value = aws_api_gateway_rest_api.query.id }
output "api_url" { value = "${trimsuffix(var.endpoint, "/")}/restapis/${aws_api_gateway_rest_api.query.id}/${aws_api_gateway_stage.query.stage_name}/_user_request_/query" }

output "authorization_role_arn" { value = aws_iam_role.authorization_probe.arn }

output "monitoring" {
  value = {
    namespace   = var.telemetry_namespace
    environment = var.environment
    alarms = { for key, alarm in aws_cloudwatch_metric_alarm.stages : key => {
      name       = alarm.alarm_name
      metric     = alarm.metric_name
      statistic  = alarm.statistic
      threshold  = alarm.threshold
      period     = alarm.period
      dimensions = alarm.dimensions
    } }
    log_groups = { for stage, group in aws_cloudwatch_log_group.functions : stage => group.name }
  }
}
