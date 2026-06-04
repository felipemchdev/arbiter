from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from app.core.database import async_session_maker, init_models
from app.core.security import generate_raw_api_key, hash_api_key, hash_password
from app.models.organization import Organization
from app.models.user import User


async def main() -> None:
    await init_models()
    async with async_session_maker() as session:
        # Create org if not exists
        result = await session.execute(select(Organization).limit(1))
        org = result.scalar_one_or_none()

        if org is None:
            raw_api_key = generate_raw_api_key()
            org = Organization(name="default", api_key=hash_api_key(raw_api_key))
            session.add(org)
            await session.flush()
            print(f"[seed] Org created: default")
            print(f"[seed] API Key (SDK/Collector): {raw_api_key}")
        else:
            print("[seed] Org already exists: default")

        # Create fixed users
        users = [
            {"email": "mch@default", "password": "@Camis#1", "role": "owner"},
            {"email": "user@common", "password": "123", "role": "viewer"},
        ]

        for u in users:
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
                print(f"[seed] User created: {u["email"]} ({u["role"]})")
            else:
                print(f"[seed] User already exists: {u["email"]}")

        await session.commit()
        print("[seed] Done.")


if __name__ == "__main__":
    asyncio.run(main())
