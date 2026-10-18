"""Unit tests for HistoryFetcher service."""

from datetime import date
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.history_fetcher import HistoryFetcher


class TestHistoryFetcher(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fetcher = HistoryFetcher()

    @patch("httpx.AsyncClient.get")
    async def test_fetch_history_success_nse(self, mock_get):
        """Verify successful fetch and parsing from NSE symbol."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "chart": {
                "result": [
                    {
                        "meta": {"symbol": "INFY.NS"},
                        "timestamp": [1700000000, 1700086400],
                        "indicators": {
                            "quote": [
                                {
                                    "close": [1400.0, 1428.0],
                                    "volume": [1000000, 1500000],
                                }
                            ]
                        },
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        points = await self.fetcher.fetch_history("INFY", range_str="1mo")
        self.assertEqual(len(points), 2)
        self.assertEqual(points[0]["ltp"], 1400.0)
        self.assertIsNone(points[0]["change_pct"])
        self.assertEqual(points[1]["ltp"], 1428.0)
        self.assertEqual(points[1]["change_pct"], 2.0)  # ((1428 - 1400) / 1400) * 100

    @patch("httpx.AsyncClient.get")
    async def test_fetch_history_fallback_to_bse(self, mock_get):
        """Verify fallback from .NS to .BO if .NS returns 404."""
        resp_404 = MagicMock()
        resp_404.status_code = 404

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {
            "chart": {
                "result": [
                    {
                        "meta": {"symbol": "SPECIAL.BO"},
                        "timestamp": [1700000000],
                        "indicators": {
                            "quote": [
                                {
                                    "close": [50.0],
                                    "volume": [10000],
                                }
                            ]
                        },
                    }
                ]
            }
        }
        # First call (.NS) fails with 404, second call (.BO) succeeds with 200
        mock_get.side_effect = [resp_404, resp_200]

        points = await self.fetcher.fetch_history("SPECIAL", range_str="1mo")
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0]["ltp"], 50.0)

    @patch("httpx.AsyncClient.get")
    async def test_fetch_history_all_fail_returns_empty(self, mock_get):
        """Verify empty list is returned if all endpoints fail."""
        resp_404 = MagicMock()
        resp_404.status_code = 404
        mock_get.return_value = resp_404

    @patch.object(HistoryFetcher, "fetch_history")
    async def test_backfill_stock_deduplicates_intra_batch_dates(self, mock_fetch):
        """Verify that duplicate dates within the fetched batch are deduplicated."""
        mock_fetch.return_value = [
            {"date": date(2026, 3, 15), "ltp": 1400.0, "volume": 1000, "change_pct": 1.0},
            {"date": date(2026, 3, 15), "ltp": 1405.0, "volume": 1200, "change_pct": 1.3},  # Duplicate date!
            {"date": date(2026, 3, 16), "ltp": 1410.0, "volume": 1500, "change_pct": 0.7},
        ]

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        added_count = await self.fetcher.backfill_stock(
            stock_id=1,
            symbol="INFY",
            screener_id=1,
            session=mock_session,
        )

        self.assertEqual(added_count, 2)
        saved_snapshots = mock_session.add_all.call_args[0][0]
        self.assertEqual(len(saved_snapshots), 2)
        self.assertEqual(saved_snapshots[0].snapshot_date, date(2026, 3, 15))
        self.assertEqual(saved_snapshots[1].snapshot_date, date(2026, 3, 16))

    @patch("httpx.AsyncClient.get")
    async def test_fetch_history_with_ohlc(self, mock_get):
        """Verify full OHLC extraction when provided by Yahoo Finance."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "chart": {
                "result": [
                    {
                        "meta": {"symbol": "TCS.NS"},
                        "timestamp": [1700000000],
                        "indicators": {
                            "quote": [
                                {
                                    "open": [3500.0],
                                    "high": [3550.0],
                                    "low": [3480.0],
                                    "close": [3530.0],
                                    "volume": [800000],
                                }
                            ]
                        },
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        points = await self.fetcher.fetch_history("TCS", range_str="1mo")
        self.assertEqual(len(points), 1)
        pt = points[0]
        self.assertEqual(pt["open"], 3500.0)
        self.assertEqual(pt["high"], 3550.0)
        self.assertEqual(pt["low"], 3480.0)
        self.assertEqual(pt["close"], 3530.0)
        self.assertEqual(pt["ltp"], 3530.0)
        self.assertEqual(pt["volume"], 800000)


if __name__ == "__main__":
    unittest.main()

