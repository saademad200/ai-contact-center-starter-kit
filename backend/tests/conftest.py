"""
Test Fixtures — See PROJECT_PLAN.md §14
Fixtures: client, ws_client, dynamo_tables, chroma_client, mock_groq, admin_user, sample_funds
"""

import sys
from unittest.mock import MagicMock

# Stub sentence_transformers before any app imports to avoid the broken
# transformers → keras v3 dependency chain in the local environment.
_mock_st = MagicMock()
_mock_st.SentenceTransformer = MagicMock
sys.modules.setdefault("sentence_transformers", _mock_st)
