"""
Application Settings
====================
Use pydantic-settings to load all environment variables.
See PROJECT_PLAN.md §14 Environment Variables Reference for full list.

Key settings to define:
- ENVIRONMENT, SECRET_KEY, CORS_ORIGINS
- AWS_REGION, S3_BUCKET_NAME
- DYNAMODB_ENDPOINT_URL (local dev only), TABLE_* names
- CHROMA_HOST, CHROMA_PORT, CHROMA_COLLECTION
- LLM_PROVIDER (groq | huggingface), LLM_MODEL_NAME, GROQ_API_KEY, HUGGINGFACE_API_KEY
- ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
- ADMIN_EMAIL, ADMIN_PASSWORD
"""
