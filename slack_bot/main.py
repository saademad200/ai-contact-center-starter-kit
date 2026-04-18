"""
Slack Bot Entry Point
=====================
Uses Slack Bolt with Socket Mode (free plan, no public URL required).

Startup:
  1. Create Bolt App with SLACK_BOT_TOKEN + SLACK_SIGNING_SECRET
  2. Create SocketModeHandler with SLACK_APP_TOKEN
  3. Register handlers: slash_command, app_mention, message_dm, file_shared_dm
  4. Start SocketModeHandler (blocking)

See PROJECT_PLAN.md §16 for full handler specs.
"""
