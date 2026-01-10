**Black–Scholes Implementation**

**Summary**

Small project that implements the Black–Scholes option pricing model and helpers to fetch/compute inputs (historical volatility, current stock price, and an approximate USD risk-free rate).

**Requirements**
- **Python**: 3.8+
- **Dependencies**: see [pyproject.toml](pyproject.toml).  I used uv, so they can be installed with:

```bash
uv sync
```

**Files**
- **Main script**: [src/main.py](src/main.py) — simple CLI that asks for a ticker and computes call/put prices.
- **Data helpers**: [src/data.py](src/data.py) — functions: `calculate_annualized_volatility`, `stock_price`, and `risk_free_rate` (scrapes Treasury site).
- **Model**: [src/model.py](src/model.py) — `BlackScholesModel` with `call_price()` and `put_price()` methods.

**Usage**

- Run the CLI (from the repository root):

```bash
uv run python src/main.py
```

- Example using the library in a Python session:

```python
from src.model import BlackScholesModel
from src.data import calculate_annualized_volatility, stock_price, risk_free_rate

S = stock_price("AAPL")
sigma = calculate_annualized_volatility("AAPL")
r = risk_free_rate(0.5)  # 0.5 years
model = BlackScholesModel(S=S, K=270, T=0.5, r=r, sigma=sigma)
print("Call:", model.call_price())
print("Put:", model.put_price())
```

**Notes & Caveats**
- `risk_free_rate` scrapes the U.S. Treasury website; it requires network access and may break if the site layout changes. 
