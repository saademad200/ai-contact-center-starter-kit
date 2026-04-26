"""
DynamoDB Client & Table Helpers
================================
See PROJECT_PLAN.md §5 for all table schemas and GSIs.

Provides:
- get_dynamodb_resource() → boto3 DynamoDB resource (respects DYNAMODB_ENDPOINT_URL for local)
- get_table(table_suffix) → Table object with correct prefix
- Table suffixes: "funds", "conversations", "messages", "tickets", "documents", "users", "response-ratings"
"""
