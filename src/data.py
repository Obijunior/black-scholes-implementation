from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf
from typing import Optional, Literal, Tuple
import datetime
import math
import requests
from io import StringIO

# used for mapping tenor strings to numerical values in years
_DEFAULT_TENORS = {
    "1 Mo": 1/12,
    "2 Mo": 2/12,
    "3 Mo": 3/12,
    "4 Mo": 4/12,
    "6 Mo": 6/12,
    "1 Yr": 1.0,
    "2 Yr": 2.0,
    "3 Yr": 3.0,
    "5 Yr": 5.0,
    "7 Yr": 7.0,
    "10 Yr": 10.0,
    "20 Yr": 20.0,
    "30 Yr": 30.0,
}


# gets volatility from historical stock data. defaults to last 365 days, but can be changed
def calculate_annualized_volatility(
    ticker_symbol: str, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    lookback_days: int = 365,
    trading_days: int = 252
) -> Optional[float]:
    
    # Set default dates if not provided
    if end_date is None or start_date is None:
        now = datetime.datetime.now()
        start_date = (now - datetime.timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
    
    try:
        # Retrieve historical stock data
        stock_data = yf.download(ticker_symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
        
        # Need at least 2 data points to calculate returns
        if stock_data.empty or len(stock_data) < 2:
            print(f"[ ERROR ] :: Insufficient data for '{ticker_symbol}'")
            return None
        
        # Calculate daily logarithmic returns
        log_returns = (np.log(stock_data['Close'] / stock_data['Close'].shift(1))).dropna()
        
        # Annualize the volatility
        volatility = log_returns.std() * np.sqrt(trading_days)

        return volatility 
        
    except Exception as e:
        print(f"Error calculating volatility for {ticker_symbol}: {str(e)}")
        return None

# gets current stock price of a ticker
def stock_price(ticker_symbol: str) -> Optional[float]:
    try:
        stock = yf.Ticker(ticker_symbol)
        current_price = stock.history(period='1d')['Close'].iloc[0]
        return current_price
    except Exception as e:
        print(f"Error retrieving stock price for {ticker_symbol}: {str(e)}")
        return None
    
# Convert a nominal yield y (decimal, e.g. 0.05 for 5%) to a continuously-compounded rate.
def _to_continuous_rate(y: float, comp: Literal["annual", "semiannual"] = "annual") -> float:
    if y < -0.999999:
        raise ValueError("Yield too low to convert safely.")
    if comp == "annual":
        return math.log(1.0 + y)
    if comp == "semiannual":
        return 2.0 * math.log(1.0 + y / 2.0)
    raise ValueError("comp must be 'annual' or 'semiannual'.")

# approximates the risk free interest rate using US Treasury data
def risk_free_rate(
    T_years: float,
    asof: Optional[datetime.date] = None,
    *,
    continuous: bool = True,
    comp_assumption: Literal["annual", "semiannual"] = "annual",
    session: Optional[requests.Session] = None,
) -> float:
    """
    Approximate the Black–Scholes risk-free rate (USD) using the U.S. Treasury
    Daily Treasury Yield Curve table.

    - Fetches the table for the year of `asof` (or today).
    - Uses the latest available row on/ before `asof`.
    - Linearly interpolates yield to match T_years.
    - Returns a continuously-compounded rate by default.

    Returns -> r (decimal)
    """
    if T_years <= 0:
        raise ValueError("T_years must be > 0.")

    asof = asof or datetime.date.today()
    year = asof.year

    # Treasury table page (HTML)
    url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView"
    params = {"type": "daily_treasury_yield_curve", "field_tdr_date_value": str(year)}

    s = session or requests.Session()
    resp = s.get(url, params=params, timeout=20)
    resp.raise_for_status()

    # Parse first table on page
    tables = pd.read_html(StringIO(resp.text))
    if not tables:
        raise RuntimeError("No tables found on Treasury page (page layout may have changed).")

    df = tables[0].copy()

    # Normalize date column name (usually "Date")
    date_col = [c for c in df.columns if str(c).lower().strip() == "date"]
    if not date_col:
        raise RuntimeError("Couldn't find a Date column in the Treasury table.")
    date_col = date_col[0]

    df[date_col] = pd.to_datetime(df[date_col]).dt.date
    df = df[df[date_col] <= asof].sort_values(date_col)
    if df.empty:
        raise RuntimeError(f"No rate rows available on or before {asof} for year={year}.")

    row = df.iloc[-1]  # latest available

    # Extract available tenors from the row
    tenors = []
    yields = []
    for col, tau in _DEFAULT_TENORS.items():
        if col in df.columns:
            val = row[col]
            if pd.notna(val):
                tenors.append(tau)
                yields.append(float(val) / 100.0)  # percent -> decimal

    if len(tenors) < 2:
        raise RuntimeError("Not enough tenor points found to interpolate.")

    # Linear interpolation in maturity space
    pairs = sorted(zip(tenors, yields), key=lambda x: x[0])
    ts, ys = zip(*pairs)

    # Clamp if outside range
    if T_years <= ts[0]:
        yT = ys[0]
    elif T_years >= ts[-1]:
        yT = ys[-1]
    else:
        # find bracket
        for i in range(len(ts) - 1):
            if ts[i] <= T_years <= ts[i + 1]:
                t0, t1 = ts[i], ts[i + 1]
                y0, y1 = ys[i], ys[i + 1]
                w = (T_years - t0) / (t1 - t0)
                yT = y0 + w * (y1 - y0)
                break

    return _to_continuous_rate(yT, comp=comp_assumption) if continuous else yT

def _parse_expirations(ticker: str) -> list[datetime.date]:
    t = yf.Ticker(ticker)
    # yfinance gives strings like "2026-01-16"
    return [datetime.date.fromisoformat(x) for x in t.options]


# Map a user-supplied T (years) to the nearest available listed option expiration date.
def choose_expiration_from_T(ticker: str, T_years: float) -> datetime.date:
    if T_years <= 0:
        raise ValueError("T_years must be > 0")

    today = datetime.date.today()
    target = today + datetime.timedelta(days=int(round(T_years * 365)))

    expirations = _parse_expirations(ticker)
    if not expirations:
        raise RuntimeError(f"No option expirations found for ticker={ticker}")

    # Choose expiration closest to the target date
    return min(expirations, key=lambda d: abs((d - target).days))


def strike_from_expiration(
    ticker: str,
    expiration: datetime.date,
    *,
    strike_rule: Literal["ATM", "OTM_PCT", "ITM_PCT"] = "ATM",
    pct: float = 0.0,
) -> float:
    """
    Pick a strike automatically from the option chain for a specific expiration.

    - ATM: strike closest to spot
    - OTM_PCT: call OTM by pct (e.g. pct=0.05 => nearest strike >= spot*(1+0.05))
    - ITM_PCT: call ITM by pct (e.g. pct=0.05 => nearest strike <= spot*(1-0.05))

    Returns the chosen strike (float).
    """
    t = yf.Ticker(ticker)
    exp_str = expiration.isoformat()
    chain = t.option_chain(exp_str)

    # spot
    spot = t.fast_info.get("last_price")
    if spot is None:
        spot = t.history(period="1d")["Close"].iloc[-1]
    S = float(spot)

    strikes = sorted(set(chain.calls["strike"]).union(set(chain.puts["strike"])))
    strikes = [float(k) for k in strikes]
    if not strikes:
        raise RuntimeError(f"No strikes found for {ticker} exp={exp_str}")

    if strike_rule == "ATM":
        return min(strikes, key=lambda k: abs(k - S))

    if pct <= 0:
        raise ValueError("pct must be > 0 for OTM_PCT / ITM_PCT")

    if strike_rule == "OTM_PCT":
        target = S * (1.0 + pct)
        candidates = [k for k in strikes if k >= target]
        return candidates[0] if candidates else strikes[-1]  # clamp

    if strike_rule == "ITM_PCT":
        target = S * (1.0 - pct)
        candidates = [k for k in strikes if k <= target]
        return candidates[-1] if candidates else strikes[0]  # clamp

    raise ValueError("Unknown strike_rule")

