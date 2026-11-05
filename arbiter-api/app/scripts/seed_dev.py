from __future__ import annotations

import asyncio
import os
import secrets
import uuid

from sqlalchemy import select

from app.core.database import async_session_maker, init_models
from app.core.security import generate_raw_api_key, hash_api_key, hash_password
from app.models.api_key import ApiKey
from app.models.organization import Organization
from app.models.user import User

DEFAULT_ADMIN_EMAIL = "admin@arbiter.local"
DEFAULT_VIEWER_EMAIL = "viewer@arbiter.local"


def _resolve_password(env_var: str) -> tuple[str, bool]:
    """Return (password, came_from_env). Unset means a one-time random password."""
    configured = os.getenv(env_var, "").strip()
    if configured:
        return configured, True
    return secrets.token_urlsafe(18), False


async def main() -> None:
    """Create the local organization, collector key and two users, once each.

    An existing user keeps its password: the seeder never re-hashes, so a password
    changed from the dashboard survives a container restart.
    """
    await init_models()
    async with async_session_maker() as session:
        result = await session.execute(select(Organization).limit(1))
        org = result.scalar_one_or_none()

        if org is None:
            org = Organization(name="default")
            session.add(org)
            await session.flush()
            print("[seed] Org created: default")

            raw_api_key = generate_raw_api_key("development")
            api_key = ApiKey(
                org_id=org.id,
                name="Default Collector Key",
                environment="development",
                prefix=raw_api_key[:12],
                hashed_key=hash_api_key(raw_api_key),
            )
            session.add(api_key)
            print(f"[seed] API Key (SDK/Collector): {raw_api_key}")
        else:
            print("[seed] Org already exists: default")

        admin_password, admin_from_env = _resolve_password("ARBITER_ADMIN_PASSWORD")
        viewer_password, viewer_from_env = _resolve_password("ARBITER_VIEWER_PASSWORD")
        users = [
            {
                "email": os.getenv("ARBITER_ADMIN_USER", DEFAULT_ADMIN_EMAIL).strip(),
                "password": admin_password,
                "role": "owner",
                "from_env": admin_from_env,
            },
            {
                "email": os.getenv("ARBITER_VIEWER_USER", DEFAULT_VIEWER_EMAIL).strip(),
                "password": viewer_password,
                "role": "viewer",
                "from_env": viewer_from_env,
            },
        ]

        for u in users:
            result = await session.execute(select(User).where(User.email == u["email"]))
            existing = result.scalar_one_or_none()
            if existing is not None:
                print(f"[seed] User already exists: {u['email']}")
                continue
            session.add(
                User(
                    id=uuid.uuid4(),
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    role=u["role"],
                    org_id=org.id,
                )
            )
            if u["from_env"]:
                print(f"[seed] User created: {u['email']} ({u['role']})")
            else:
                # Printed once, never stored in the repo: keep it out of logs you commit.
                print(f"[seed] User created: {u['email']} ({u['role']}) password: {u['password']}")

        await session.commit()
        print("[seed] Done.")


if __name__ == "__main__":
    asyncio.run(main())
