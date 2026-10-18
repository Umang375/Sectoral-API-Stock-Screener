import os
import sys
sys.path.insert(0, os.path.abspath("backend"))

from datetime import date, timedelta
import unittest
from unittest.mock import AsyncMock, MagicMock

from app.models.stock import DailySnapshot, Stock
from app.services.scheduler import soft_delete_inactive_stocks


class TestStockSoftDelete(unittest.IsolatedAsyncioTestCase):
    def test_stock_model_defaults(self):
        """Verify default active state and last_activated_at timestamp on Stock creation."""
        stock = Stock(symbol="RELIANCE", name="Reliance Industries")
        self.assertTrue(stock.is_active)
        self.assertEqual(stock.last_activated_at, date.today())

    def test_stock_reactivation_logic(self):
        """Verify that a soft-deleted stock can be reactivated with a new baseline date."""
        past_date = date.today() - timedelta(days=60)
        stock = Stock(
            symbol="INFY",
            name="Infosys Ltd",
            is_active=False,
            last_activated_at=past_date,
        )
        self.assertFalse(stock.is_active)
        self.assertEqual(stock.last_activated_at, past_date)

        # Simulate reactivation upon reappearing in screener
        today = date.today()
        stock.is_active = True
        stock.last_activated_at = today

        self.assertTrue(stock.is_active)
        self.assertEqual(stock.last_activated_at, today)

    async def test_soft_delete_inactive_stocks_marks_inactive(self):
        """Verify that soft_delete_inactive_stocks marks inactive stocks and commits."""
        inactive_stock = Stock(
            id=1,
            symbol="DORMANT",
            name="Dormant Corp",
            is_active=True,
            last_activated_at=date(2026, 1, 1),
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [inactive_stock]
        mock_session.exec.return_value = mock_result

        deleted_count = await soft_delete_inactive_stocks(
            session=mock_session,
            threshold_days=21,
            reference_date=date(2026, 10, 17),
        )

        self.assertEqual(deleted_count, 1)
        self.assertFalse(inactive_stock.is_active)
        mock_session.add.assert_called_once_with(inactive_stock)
        mock_session.commit.assert_awaited_once()

    async def test_soft_delete_inactive_stocks_none_eligible(self):
        """Verify that no changes occur when no stocks exceed the threshold."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        deleted_count = await soft_delete_inactive_stocks(
            session=mock_session,
            threshold_days=21,
            reference_date=date(2026, 10, 17),
        )

        self.assertEqual(deleted_count, 0)
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_anchor_ltp_respects_reactivation_baseline(self):
        """Verify that return lookbacks exclude snapshots prior to last_activated_at."""
        reactivated_at = date(2026, 10, 10)
        stock = Stock(
            id=1,
            symbol="RESURRECTED",
            name="Resurrected Stock",
            is_active=True,
            last_activated_at=reactivated_at,
        )

        # Snapshots: one recent, one right at reactivation, one ancient before gap
        snap_today = DailySnapshot(stock_id=1, snapshot_date=date(2026, 10, 17), ltp=110.0)
        snap_reactivated = DailySnapshot(stock_id=1, snapshot_date=date(2026, 10, 10), ltp=100.0)
        snap_pre_gap = DailySnapshot(stock_id=1, snapshot_date=date(2026, 8, 1), ltp=50.0)

        snaps = [snap_today, snap_reactivated, snap_pre_gap]
        ref_date = snap_today.snapshot_date

        # Lookback candidate filtering with stock.last_activated_at boundary
        candidates = [
            s for s in snaps
            if s.ltp is not None
            and 20 <= (ref_date - s.snapshot_date).days <= 90
            and (stock.last_activated_at is None or s.snapshot_date >= stock.last_activated_at)
        ]

        # snap_pre_gap is 77 days ago, but occurred before last_activated_at, so it must be excluded!
        self.assertEqual(len(candidates), 0)
