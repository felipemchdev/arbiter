from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import async_session_maker, init_models
from app.core.security import generate_raw_api_key, hash_api_key
from app.models.organization import Organization


async def main() -> None:
    await init_models()
    async with async_session_maker() as session:
        result = await session.execute(select(Organization).limit(1))
        if result.first() is None:
            raw_api_key = generate_raw_api_key()
            org = Organization(name="default", api_key=hash_api_key(raw_api_key))
            session.add(org)
            await session.commit()
            print(raw_api_key)


if __name__ == "__main__":
    asyncio.run(main())