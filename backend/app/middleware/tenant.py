"""Tenant context injection middleware.

Reads the tenant_id from the decoded JWT and sets it on request.state.
SQLAlchemy event hooks then auto-filter all queries by this tenant_id.

Placeholder — to be implemented in Phase 2 (multi-tenant enforcement).
"""
