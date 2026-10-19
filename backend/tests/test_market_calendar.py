from datetime import date
import unittest
from unittest.mock import AsyncMock, patch

from app.services.market_calendar import (
    _HOLIDAY_CACHE,
    BASELINE_HOLIDAYS_SEED,
    is_trading_day,
    get_expected_trading_days,
    sync_market_holidays_from_upstox,
)


class TestMarketCalendar(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        _HOLIDAY_CACHE.clear()
        _HOLIDAY_CACHE.update(BASELINE_HOLIDAYS_SEED.keys())

    def test_baseline_seed_and_weekend_check(self):
        # Weekend checks (Saturday: 2026-01-24, Sunday: 2026-01-25)
        self.assertFalse(is_trading_day(date(2026, 1, 24)))
        self.assertFalse(is_trading_day(date(2026, 1, 25)))

        # Republic Day 2026 (Monday 2026-01-26 is in baseline seed)
        self.assertFalse(is_trading_day(date(2026, 1, 26)))

        # Normal Tuesday (2026-01-27) is a trading day
        self.assertTrue(is_trading_day(date(2026, 1, 27)))

    def test_get_expected_trading_days(self):
        # Normal week: Monday 2026-01-19 to Friday 2026-01-23 -> 5 trading days
        self.assertEqual(get_expected_trading_days(date(2026, 1, 19), date(2026, 1, 23)), 5)

        # Republic Day week: Monday 2026-01-26 to Friday 2026-01-30 -> 4 trading days
        self.assertEqual(get_expected_trading_days(date(2026, 1, 26), date(2026, 1, 30)), 4)

    async def test_sync_market_holidays_filtering(self):
        """Verify that only TRADING_HOLIDAY on NSE/BSE are saved, ignoring SETTLEMENT_HOLIDAY & SPECIAL_TIMING."""
        mock_payload = {
            "status": "success",
            "data": [
                {
                    "date": "2026-01-26",
                    "description": "Republic Day",
                    "holiday_type": "TRADING_HOLIDAY",
                    "closed_exchanges": ["NSE", "BSE"],
                },
                {
                    "date": "2026-02-01",
                    "description": "Budget Day Session",
                    "holiday_type": "SPECIAL_TIMING",
                    "closed_exchanges": ["CDS", "BCD"],
                },
                {
                    "date": "2026-02-19",
                    "description": "Chhatrapati Shivaji Maharaj Jayanti",
                    "holiday_type": "SETTLEMENT_HOLIDAY",
                    "closed_exchanges": ["CDS", "BCD"],
                },
                {
                    "date": "2026-03-03",
                    "description": "Commodity Holiday",
                    "holiday_type": "TRADING_HOLIDAY",
                    "closed_exchanges": ["MCX"],
                },
            ],
        }

        mock_resp = AsyncMock()
        mock_resp.raise_for_status = lambda: None
        mock_resp.json = lambda: mock_payload

        from unittest.mock import MagicMock
        # Mock AsyncSession
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_exec_res = MagicMock()
        mock_exec_res.first.return_value = None
        mock_session.exec.return_value = mock_exec_res

        with patch("httpx.AsyncClient.get", return_value=mock_resp), patch(
            "app.services.market_calendar.load_market_calendar_cache", new=AsyncMock()
        ):
            result = await sync_market_holidays_from_upstox(mock_session)
            self.assertEqual(result["status"], "ok")
            # Only Republic Day meets TRADING_HOLIDAY + NSE/BSE criteria
            self.assertEqual(result["added"], 1)
            self.assertEqual(mock_session.add.call_count, 1)
            added_obj = mock_session.add.call_args[0][0]
            self.assertEqual(added_obj.holiday_date, date(2026, 1, 26))
            self.assertEqual(added_obj.description, "Republic Day")


if __name__ == "__main__":
    unittest.main()
