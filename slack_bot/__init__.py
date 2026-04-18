# Slack Bot — KMS Interface
# Built with Slack Bolt for Python (Socket Mode — no public URL needed)
#
# Handles:
#   - Slash command:  /kms <question>    → RAG answer posted in thread
#   - App mention:    @kms-bot <question> → same as above
#   - DM to bot:      any message → treated as /kms question
#   - Admin DM:       DM a file → triggers document upload + ingestion
#
# See PROJECT_PLAN.md §16 for full Slack bot spec and Block Kit layouts.
