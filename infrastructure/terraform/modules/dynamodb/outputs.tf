output "users_table_name"           { value = aws_dynamodb_table.users.name }
output "conversations_table_name"   { value = aws_dynamodb_table.conversations.name }
output "messages_table_name"        { value = aws_dynamodb_table.messages.name }
output "tickets_table_name"         { value = aws_dynamodb_table.tickets.name }
output "documents_table_name"       { value = aws_dynamodb_table.documents.name }
output "ratings_table_name"         { value = aws_dynamodb_table.response_ratings.name }
output "prompt_registry_table_name" { value = aws_dynamodb_table.prompt_registry.name }
output "model_registry_table_name"  { value = aws_dynamodb_table.model_registry.name }
