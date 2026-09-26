output "users_table_name" {
  value = aws_dynamodb_table.users.name
}

output "chats_table_name" {
  value = aws_dynamodb_table.chats.name
}

output "messages_table_name" {
  value = aws_dynamodb_table.messages.name
}

output "users_table_arn" {
  value = aws_dynamodb_table.users.arn

}

output "chats_table_arn" {
  value = aws_dynamodb_table.chats.arn

}

output "messages_table_arn" {
  value = aws_dynamodb_table.messages.arn

}