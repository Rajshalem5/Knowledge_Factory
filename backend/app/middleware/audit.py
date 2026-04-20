"""Audit log middleware.

Intercepts all state-changing requests (POST, PUT, PATCH, DELETE) and
writes an audit_logs row with actor, action, entity, before/after state,
IP, user-agent, and request_id.

Placeholder — to be implemented in Phase 2.
"""
