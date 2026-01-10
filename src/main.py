from model import BlackScholesModel
import data

import datetime

def main():

    ticker = input("Enter the stock ticker symbol (e.g., AAPL): ").upper()
    T_input = float(input("Enter time to expiration: (in years, e.g., 0.5 for 6 months): "))

    exp_date = data.choose_expiration_from_T(ticker, T_input)
    T = (exp_date - datetime.date.today()).days / 365.0
    if T <= 0:
        raise RuntimeError(f"Chosen expiration date {exp_date} is not in the future.")
    
    K = data.strike_from_expiration(ticker, exp_date, strike_rule="ATM")

    r = data.risk_free_rate(T)
    sigma = data.calculate_annualized_volatility(ticker)
    S = data.stock_price(ticker)

    model = BlackScholesModel(S=S, K=K, T=T, r=r, sigma=sigma)
    call_price = model.call_price()
    put_price = model.put_price()

    print(f"Ticker: {ticker}")
    print(f"Expiration chosen: {exp_date} (T={T:.4f} years)")
    print(f"Stock Price (S): {S:.2f}")
    print(f"Auto Strike (K): {K:.2f}")
    print(f"Call Option Price: {call_price}")
    print(f"Put Option Price: {put_price}")

if __name__ == "__main__":
    main()