import asyncio
import random
from datetime import date, timedelta
from sqlmodel import select
from app.database import async_session_factory
from app.models.stock import DailySnapshot, Stock
from app.services.returns_calculator import ReturnsCalculator

async def backfill():
    print("Starting backfill...")
    async with async_session_factory() as session:
        # Get the latest snapshots
        stmt = select(DailySnapshot)
        result = await session.exec(stmt)
        today_snaps = list(result.all())

        if not today_snaps:
            print("No snapshots for today. Run the screener first.")
            return

        print(f"Found {len(today_snaps)} snapshots for today. Generating 30 days of history...")

        for snap in today_snaps:
            current_ltp = snap.ltp
            current_date = date.today()

            for i in range(1, 31):
                hist_date = current_date - timedelta(days=i)
                # Skip weekends
                if hist_date.weekday() >= 5:
                    continue

                # Random daily walk backward (-3% to +3%)
                # So if today is 100, and yesterday it dropped 2%, yesterday's price is 100 / 0.98
                daily_change = random.uniform(-0.03, 0.03)
                current_ltp = current_ltp / (1 + daily_change)

                hist_snap = DailySnapshot(
                    stock_id=snap.stock_id,
                    screener_id=snap.screener_id,
                    ltp=round(current_ltp, 2),
                    volume=int(snap.volume * random.uniform(0.5, 1.5)) if snap.volume else None,
                    change_pct=round(daily_change * 100, 2),
                    snapshot_date=hist_date,
                    raw_data={}
                )
                session.add(hist_snap)
        
        await session.commit()
        print("Historical snapshots committed.")

        print("Calculating weekly returns...")
        calculator = ReturnsCalculator()
        summary = await calculator.calculate_all(session)
        print("Weekly returns calculated:", summary)
        print("Backfill complete!")

if __name__ == "__main__":
    asyncio.run(backfill())
