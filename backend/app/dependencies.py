"""
Shared FastAPI dependencies.

These are the building blocks that route handlers declare via Depends().
Each dependency is composable — for example, `current_user` depends on
`get_db` internally but only exposes the resolved User object.

Currently only the database session dependency is implemented. Future
dependencies will include:
  - current_user:  resolves the authenticated user from the JWT
  - current_tenant: resolves the tenant context from the JWT
  - require_role: parameterized dependency for RBAC
"""

from app.database import get_db

__all__ = ["get_db"]
