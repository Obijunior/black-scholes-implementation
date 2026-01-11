# **Black–Scholes Implementation**

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
- **Data helpers**: [src/data.py](src/data.py) — functions should be fairly self-explanitory, but essentially grab live data for all the inputs for the model, after a user inputs the ticker and time to maturity
- **Model**: [src/model.py](src/model.py) — `BlackScholesModel` with `call_price()` and `put_price()` methods.

**Usage**

- Run the CLI (from the repository root):

```bash
uv run python src/main.py
```

- Example using the library in a Python session:

```python
from src.model import BlackScholesModel
import src.data

S = data.stock_price("AAPL")
sigma = data.calculate_annualized_volatility("AAPL")
r = data.risk_free_rate(0.5)  # 0.5 years

# can be calculated automatically, or can be set manually
K = data.strike_from_expiration(ticker, exp_date, strike_rule="ATM") 

model = BlackScholesModel(S=S, K=K, T=0.5, r=r, sigma=sigma)
print("Call:", model.call_price())
print("Put:", model.put_price())
```

**Notes & Caveats**
- `risk_free_rate` scrapes the U.S. Treasury website; it requires network access and may break if the site layout changes.
- Only prices European options, may underprice American options
- The model assumes constant volatility until expiration, which is rarely true 

### **Actual Math involved** 
```math
\begin{equation}
	\frac{\partial \mathrm C}{ \partial \mathrm t } + \frac{1}{2}\sigma^{2} \mathrm S^{2} \frac{\partial^{2} \mathrm C}{\partial \mathrm C^2}
	+ \mathrm r \mathrm S \frac{\partial \mathrm C}{\partial \mathrm S}\ =
	\mathrm r \mathrm C 
\end{equation}
```
```math
\begin{equation}
	\mathrm C(\mathrm S,\mathrm t)= \mathrm N(\mathrm d_1)\mathrm S - \mathrm N(\mathrm d_2) \mathrm K \mathrm e^{-rt}
\end{equation}
```
```math
\begin{equation}
	\mathrm d_1= \frac{1}{\sigma \sqrt{\mathrm t}} \left[\ln{\left(\frac{S}{K}\right)} + t\left(r + \frac{\sigma^2}{2} \right) \right]
\end{equation}
```
```math
\begin{equation}
d_{2}=d_{1}-\sigma\sqrt{\tau}
\end{equation}
```
```math
\begin{equation}
	N(x)=\frac{1}{\sqrt{2\pi}} \int_{-\infty}^{x} \mathrm e^{-\frac{1}{2}z^2} dz
\end{equation}
```