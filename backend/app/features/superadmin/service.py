"""SuperAdmin business logic — user management and role transfer."""

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import User
from app.core.enums import Role, UserStatus


class SuperAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all_users(self, page: int = 1, limit: int = 50) -> dict:
        """List all platform users with pagination, ORM-based."""
        offset = (page - 1) * limit

        # Count total
        count_q = select(func.count(User.id))
        count_result = await self.db.execute(count_q)
        total = count_result.scalar() or 0

        # Fetch page
        stmt = (
            select(User)
            .offset(offset)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        return {
            "data": [
                {
                    "id": str(u.id),
                    "email": u.email,
                    "name": u.name,
                    "role": u.role.value if hasattr(u.role, "value") else str(u.role),
                    "status": u.status.value if hasattr(u.status, "value") else str(u.status),
                    "photo_url": u.photo_url,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in users
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit else 1,
        }

    async def transfer_superadmin(self, target_id: str, current_user: User) -> dict:
        """Transfer superadmin role to another ADMIN user.

        Demotes current superadmin to ADMIN, promotes target to SUPERADMIN.
        Raises ValueError with a user-facing message on validation failure.
        """
        # Fetch target user
        stmt = select(User).where(User.id == target_id)
        result = await self.db.execute(stmt)
        target = result.scalar_one_or_none()

        if not target:
            raise ValueError("Target user not found")

        # Validate target role
        target_role = target.role.value if hasattr(target.role, "value") else str(target.role)
        if target_role != Role.ADMIN.value:
            raise ValueError(
                f"Cannot promote user with role '{target_role}'. "
                "Only ADMIN users can be promoted to SUPERADMIN."
            )

        # Validate target status
        target_status = target.status.value if hasattr(target.status, "value") else str(target.status)
        if target_status != UserStatus.ACTIVE.value:
            raise ValueError(
                "Cannot promote an inactive user. The target user must have ACTIVE status."
            )

        # Prevent self-transfer
        if target_id == str(current_user.id):
            raise ValueError(
                "You cannot transfer the superadmin role to yourself. "
                "Select another ADMIN user."
            )

        # Execute transfer: demote current superadmin to ADMIN, promote target to SUPERADMIN
        await self.db.execute(
            update(User).where(User.id == str(current_user.id)).values(role=Role.ADMIN)
        )
        await self.db.execute(
            update(User).where(User.id == target_id).values(role=Role.SUPERADMIN)
        )
        await self.db.commit()

        return {
            "message": "Superadmin role transferred successfully",
            "previous_superadmin": str(current_user.id),
            "new_superadmin": target_id,
            "previous_role": "ADMIN",
            "new_role": "SUPERADMIN",
        }
