"""
The 6 variables required for Black-Scholes option pricing model.
    1. Volatility
    2. Price of underlying asset
    3. Strike price
    4. Time to expiration
    5. Risk-free interest rate
    6. The type of option (call or put)
"""

# Call = S*N(d1) - K*e^(-rT)*N(d2)
# Put = N(-d2)*K*e^(-rT) - N(-d1)*S

# d1 = [ln(S/X) + (r + σ^2/2)T] / (σ√T)
# d2 = d1 - σ√T

# C = Call option price
# S = Current stock price
# K = Strike price
# r = Risk-free interest rate
# T = Time to maturity
# N = a normal distribution
# σ (sigma) = Volatility of the stock (standard deviation of the stock's returns)

import numpy as np
from scipy.stats import norm

class BlackScholesModel:
    def __init__(self, S, K, T, r, sigma):
        self.S = S  # Current stock price
        self.K = K  # Strike price
        self.T = T  # Time to maturity
        self.r = r  # Risk-free interest rate
        self.sigma = sigma  # Volatility of the stock

    def d1(self):
        # I split up the d1 formula for better readability
        first_term = np.log(self.S / self.K)
        second_term = (self.r + (0.5 * (self.sigma ** 2))) * self.T

        numerator = first_term + second_term
        denominator = self.sigma * np.sqrt(self.T)

        return (numerator / denominator)
    
    def d2(self):
        return self.d1() - (self.sigma * np.sqrt(self.T))
    
    def call_price(self):
        d1 = self.d1()
        d2 = self.d2()

        call_price = (self.S * norm.cdf(d1)) - (self.K * np.exp(-self.r * self.T) * norm.cdf(d2))
        return call_price
    
    def put_price(self):
        d1 = self.d1()
        d2 = self.d2()

        put_price = (norm.cdf(-d2) * self.K * np.exp(-self.r * self.T)) - (norm.cdf(-d1) * self.S)
        return put_price