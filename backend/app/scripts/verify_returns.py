"""Verification script to inspect returns on the stocks from user's screenshot."""

import json
import urllib.request

symbols = [
    'IBULLSLTD', 'GRWRHITECH', 'BHAGYANGR', 'HEG', 'ITDC',
    'AEROENTER', 'BELRISE', 'ASIANENE', 'CUPID'
]

url = 'http://127.0.0.1:8000/api/stocks?limit=250'
req = urllib.request.urlopen(url)
data = json.loads(req.read())

matches = [s for s in data if s['symbol'] in symbols]
print(f"{'SYMBOL':12} {'LTP':>8} {'52W HIGH':>10} {'1D':>8} {'1W':>8} {'1M':>8} {'3M':>8} {'6M':>8} {'1Y':>8}")
print("-" * 88)
for m in matches:
    print(
        f"{m['symbol']:12} "
        f"{str(m['ltp']):>8} "
        f"{str(m['drawdown_52w_high']) + '%':>10} "
        f"{str(m['return_1d']) + '%':>8} "
        f"{str(m['return_1w']) + '%':>8} "
        f"{str(m['return_1m']) + '%':>8} "
        f"{str(m['return_3m']) + '%':>8} "
        f"{str(m['return_6m']) + '%':>8} "
        f"{str(m['return_1y']) + '%':>8}"
    )
