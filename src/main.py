from model import BlackScholesModel
import data

def main():

    ticker = input("Enter the stock ticker symbol (e.g., AAPL): ").upper()
    T = float(input("Enter time to expiration: (in years, e.g., 0.5 for 6 months): "))

    r = data.risk_free_rate(T)
    sigma = data.calculate_annualized_volatility(ticker)
    S = data.stock_price(ticker)

    model = BlackScholesModel(S=S, K=270, T=float(T), r=r, sigma=sigma)
    call_price = model.call_price()
    put_price = model.put_price()

    print(f"Ticker: {ticker}")
    print(f"Stock Price: {S:.2f}")
    print(f"Call Option Price: {call_price}")
    print(f"Put Option Price: {put_price}")

if __name__ == "__main__":
    main()