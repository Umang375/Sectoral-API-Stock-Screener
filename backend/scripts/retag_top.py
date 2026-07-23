import asyncio
from sqlmodel import select, delete
from app.database import async_session_factory
from app.models.tag import StockTag, Tag
from app.models.stock import Stock, DailySnapshot
from app.models.returns import WeeklyReturns
from app.services.gemini_tagger import GeminiTagger
from app.utils.rate_limiter import RateLimiter
import redis.asyncio as aioredis
from app.config import get_settings

async def retag_top_stocks():
    print("Fetching top stocks...")
    settings = get_settings()
    redis_client = aioredis.from_url(settings.REDIS_URL)
    rate_limiter = RateLimiter(settings.GEMINI_RPM_LIMIT, 60.0)
    tagger = GeminiTagger(rate_limiter, redis_client)

    async with async_session_factory() as session:
        # Get "uncategorised" tag
        uncat_tag = (await session.exec(select(Tag).where(Tag.label == 'uncategorised'))).first()
        if uncat_tag:
            print("Removing 'uncategorised' tag from DB...")
            await session.exec(delete(StockTag).where(StockTag.tag_id == uncat_tag.id))
            await session.exec(delete(Tag).where(Tag.id == uncat_tag.id))
            await session.commit()

        # Get top stocks this week
        top_stocks_stmt = (
            select(Stock)
            .join(WeeklyReturns, Stock.id == WeeklyReturns.stock_id)
            .order_by(WeeklyReturns.week_start.desc(), WeeklyReturns.return_pct.desc())
            .limit(20)
        )
        top_stocks = list((await session.exec(top_stocks_stmt)).all())

        print(f"Tagging {len(top_stocks)} top stocks...")
        for stock in top_stocks:
            # Get latest LTP
            ltp_stmt = select(DailySnapshot.ltp, DailySnapshot.change_pct).where(DailySnapshot.stock_id == stock.id).order_by(DailySnapshot.snapshot_date.desc()).limit(1)
            ltp_row = (await session.exec(ltp_stmt)).first()
            if ltp_row:
                ltp, change_pct = ltp_row
                # Generate tags (this bypasses cache if we deleted the stock tags)
                # But wait, we didn't delete stock_tags for other tags, which is good.
                tags = await tagger.generate_tags(
                    stock=stock,
                    current_ltp=ltp,
                    change_pct=change_pct,
                    screener_name="Top 20 Retag",
                    screener_id=1,
                    session=session
                )
                print(f"Tagged {stock.symbol}: {tags}")

        print("Done!")

if __name__ == "__main__":
    asyncio.run(retag_top_stocks())
