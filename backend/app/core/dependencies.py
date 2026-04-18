"""
FastAPI Dependencies
====================
get_current_user  — verifies Bearer JWT, returns user dict from DynamoDB
                    raises HTTP 401 if token invalid/expired
require_admin     — calls get_current_user, then checks role == "admin"
                    raises HTTP 403 if role != admin
"""
