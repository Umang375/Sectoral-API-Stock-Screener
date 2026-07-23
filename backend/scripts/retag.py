import asyncio
from sqlmodel import select, delete
from app.database import async_session_factory
from app.models.tag import StockTag, Tag
from app.models.screener import ScreenerRun
from app.services.background_worker import BackgroundWorker
import redis.asyncio as aioredis
from app.config import get_settings

async def retag():
    print("Clearing old tags...")
    settings = get_settings()
    redis_client = aioredis.from_url(settings.REDIS_URL)
    await redis_client.flushall()
    print("Redis cleared.")

    async with async_session_factory() as session:
        await session.exec(delete(StockTag))
        await session.exec(delete(Tag))
        await session.commit()
        print("Database tags cleared.")

        # Find the latest screener run
        stmt = select(ScreenerRun).order_by(ScreenerRun.run_time.desc()).limit(1)
        latest_run = (await session.exec(stmt)).first()

        if latest_run:
            print(f"Triggering background tagging for screener_run {latest_run.id}")
            worker = BackgroundWorker()
            await worker.tag_stocks_for_screener(latest_run.id)
            print("Tagging complete!")
        else:
            print("No screener run found.")

if __name__ == "__main__":
    asyncio.run(retag())
