from __future__ import annotations

import asyncio
import os
import uuid

from sqlalchemy import select

from app.core.database import async_session_maker, init_models
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User


async def main() -> None:
    admin_user = os.getenv("ARBITER_ADMIN_USER", "").strip()
    admin_pass = os.getenv("ARBITER_ADMIN_PASSWORD", "").strip()
    viewer_user = os.getenv("ARBITER_VIEWER_USER", "").strip()
    viewer_pass = os.getenv("ARBITER_VIEWER_PASSWORD", "").strip()

    if not admin_user or not admin_pass:
        print("[seed:prod] Skipping — ARBITER_ADMIN_USER/PASSWORD not set")
        return

    async with async_session_maker() as session:
        result = await session.execute(select(Organization).limit(1))
        org = result.scalar_one_or_none()
        if org is None:
            org = Organization(name="default")
            session.add(org)
            await session.flush()
            print("[seed:prod] Org created: default")

        users = [
            {"email": admin_user, "password": admin_pass, "role": "owner"},
            {"email": viewer_user, "password": viewer_pass, "role": "viewer"},
        ]

        for u in users:
            if not u["email"] or not u["password"]:
                continue
            result = await session.execute(select(User).where(User.email == u["email"]))
            existing = result.scalar_one_or_none()
            if existing is None:
                user = User(
                    id=uuid.uuid4(),
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    role=u["role"],
                    org_id=org.id,
                )
                session.add(user)
                print(f"[seed:prod] User created: {u['email']} ({u['role']})")
            else:
                existing.hashed_password = hash_password(u["password"])
                existing.role = u["role"]
                session.add(existing)
                print(f"[seed:prod] User updated: {u['email']} ({u['role']})")

        await session.commit()
        print("[seed:prod] Done.")


if __name__ == "__main__":
    asyncio.run(main())
