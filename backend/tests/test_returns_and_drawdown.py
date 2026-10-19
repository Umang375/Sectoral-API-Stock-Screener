from datetime import date, timedelta
import unittest
from unittest.mock import AsyncMock, MagicMock

from app.models.stock import DailySnapshot, Stock
from app.models.returns import WeeklyReturns
from app.services.chartlink_scraper import ChartlinkScraper
from app.services.returns_calculator import ReturnsCalculator


class TestReturnsAndDrawdown(unittest.IsolatedAsyncioTestCase):
    def test_chartlink_scraper_preserves_zero_change(self):
        scraper = ChartlinkScraper()
        
        # Row with 0.0% change
        row_zero = {
            "nsecode": "TCS",
            "name": "Tata Consultancy Services",
            "close": "3500.0",
            "volume": "1000",
            "per_chg": "0.0",
        }
        parsed_zero = scraper._parse_row(row_zero)
        self.assertEqual(parsed_zero.change_pct, 0.0)
        self.assertIsNotNone(parsed_zero.change_pct)

        # Row with 0 volume
        row_zero_vol = {
            "nsecode": "INFY",
            "name": "Infosys",
            "close": "1500.0",
            "volume": 0,
            "per_chg": 1.5,
        }
        parsed_zero_vol = scraper._parse_row(row_zero_vol)
        self.assertEqual(parsed_zero_vol.volume, 0)
        self.assertEqual(parsed_zero_vol.change_pct, 1.5)

    async def test_returns_calculator_single_snapshot_not_zero(self):
        """Single snapshot in a week should use change_pct instead of returning 0.0%."""
        calc = ReturnsCalculator()
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        week_start = date(2026, 1, 19)
        week_end = date(2026, 1, 23)

        # Stock IDs returned
        mock_exec_stocks = MagicMock()
        mock_exec_stocks.all.return_value = [101]

        # Single snapshot on Friday with +15% move
        friday_snap = DailySnapshot(
            id=1,
            stock_id=101,
            screener_id=1,
            ltp=115.0,
            change_pct=15.0,
            snapshot_date=date(2026, 1, 23),
        )
        mock_exec_snaps = MagicMock()
        mock_exec_snaps.all.return_value = [friday_snap]

        # No prior snapshot
        mock_exec_prior = MagicMock()
        mock_exec_prior.first.return_value = None

        # No existing weekly_returns
        mock_exec_existing = MagicMock()
        mock_exec_existing.first.return_value = None

        mock_session.exec.side_effect = [
            mock_exec_stocks,    # select stock_ids
            mock_exec_snaps,     # select week_snaps
            mock_exec_prior,     # select prior_ltp
            mock_exec_existing,  # select existing WeeklyReturns
        ]

        count = await calc._calculate_stock_returns(mock_session, week_start, week_end)
        self.assertEqual(count, 1)
        self.assertEqual(mock_session.add.call_count, 1)

        saved_return: WeeklyReturns = mock_session.add.call_args[0][0]
        self.assertEqual(saved_return.stock_id, 101)
        # Should not be 0.0%!
        self.assertEqual(saved_return.return_pct, 15.0)
        self.assertEqual(saved_return.close_ltp, 115.0)
        self.assertEqual(saved_return.open_ltp, 100.0)

    async def test_returns_calculator_anchors_to_prior_close(self):
        """Multi-day week should anchor to prior week's close if available."""
        calc = ReturnsCalculator()
        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        week_start = date(2026, 1, 19)
        week_end = date(2026, 1, 23)

        mock_exec_stocks = MagicMock()
        mock_exec_stocks.all.return_value = [102]

        # Monday close 105, Friday close 110
        mon_snap = DailySnapshot(
            id=2, stock_id=102, screener_id=1, ltp=105.0, snapshot_date=date(2026, 1, 19)
        )
        fri_snap = DailySnapshot(
            id=3, stock_id=102, screener_id=1, ltp=110.0, snapshot_date=date(2026, 1, 23)
        )
        mock_exec_snaps = MagicMock()
        mock_exec_snaps.all.return_value = [mon_snap, fri_snap]

        # Prior week closed at 100.0
        mock_exec_prior = MagicMock()
        mock_exec_prior.first.return_value = 100.0

        mock_exec_existing = MagicMock()
        mock_exec_existing.first.return_value = None

        mock_session.exec.side_effect = [
            mock_exec_stocks,
            mock_exec_snaps,
            mock_exec_prior,
            mock_exec_existing,
        ]

        count = await calc._calculate_stock_returns(mock_session, week_start, week_end)
        self.assertEqual(count, 1)
        saved_return: WeeklyReturns = mock_session.add.call_args[0][0]
        # (110 - 100) / 100 * 100 = 10.0%
        self.assertEqual(saved_return.return_pct, 10.0)
        self.assertEqual(saved_return.open_ltp, 100.0)
        self.assertEqual(saved_return.close_ltp, 110.0)

    def test_52w_high_excludes_older_than_365_days(self):
        """Snapshots older than 365 calendar days should never pollute 52W high."""
        ref_date = date(2026, 10, 19)
        
        # Snapshot from 2 years ago (700 days ago) with peak price 500
        old_snap = DailySnapshot(
            id=1, stock_id=1, screener_id=1, high=500.0, ltp=490.0, snapshot_date=ref_date - timedelta(days=700)
        )
        # Snapshot within 52 weeks (100 days ago) with high 300
        recent_snap = DailySnapshot(
            id=2, stock_id=1, screener_id=1, high=300.0, ltp=290.0, snapshot_date=ref_date - timedelta(days=100)
        )
        # Latest snapshot today at 270
        latest_snap = DailySnapshot(
            id=3, stock_id=1, screener_id=1, high=275.0, ltp=270.0, snapshot_date=ref_date
        )

        snaps = [latest_snap, recent_snap, old_snap]

        # Applying the 365-day calendar filter
        valid_52w_prices = [
            s.high if s.high is not None else s.ltp for s in snaps
            if (s.high is not None or s.ltp is not None)
            and 0 <= (ref_date - s.snapshot_date).days <= 365
        ]
        max_price = max(valid_52w_prices)

        # 52W high should be 300, NOT 500!
        self.assertEqual(max_price, 300.0)
        drawdown_52w = round(((latest_snap.ltp - max_price) / max_price) * 100, 1)
        # Drawdown from 300 to 270 is -10.0%
        self.assertEqual(drawdown_52w, -10.0)


if __name__ == "__main__":
    unittest.main()
