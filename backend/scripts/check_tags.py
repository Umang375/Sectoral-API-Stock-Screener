import asyncio
from sqlmodel import select
from app.database import async_session_factory
from app.models.tag import Tag

async def main():
    async with async_session_factory() as session:
        tags = (await session.exec(select(Tag))).all()
        print(f"Total tags: {len(tags)}")
        for t in tags[:20]:
            print(t.label)

if __name__ == "__main__":
    asyncio.run(main())
