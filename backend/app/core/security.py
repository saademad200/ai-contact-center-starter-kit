"""
Security Utilities
==================
JWT: create_access_token, create_refresh_token, verify_token
     - Use python-jose, HS256 algorithm, SECRET_KEY from settings
     - Access token expires: ACCESS_TOKEN_EXPIRE_MINUTES
     - Refresh token expires: REFRESH_TOKEN_EXPIRE_DAYS

Password: hash_password (bcrypt cost 12), verify_password
"""
