"""
DynamoDB Client & Helpers
=========================
Create boto3 DynamoDB resource and expose table references.
See PROJECT_PLAN.md §6 Data Models for full table schemas.

Tables: users, documents, chat-sessions, chat-messages
Provide helper functions: get_item, put_item, update_item, delete_item, query_gsi
"""
