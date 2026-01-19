import numpy as np
from core.curves import ZeroCouponCurve

class VolatilitySwapPricer:
    def __init__(
            self, 
            notional : float, 
            vol_strike: float,
            maturity : float, 
            nb_obs : int, 
            discount_curve : ZeroCouponCurve, 
            sigma_model : float = 0.20
    ):
        self.N = notional
        self.K = vol_strike
        self.T = maturity 
        self.n = nb_obs
        self.curve = discount_curve
        self.sigma = sigma_model
    
    def simulate_log_returns(self) -> np.ndarray:
        dt = self.T/self.n
        return np.random.normal(
            loc = 0.0,
            scale = self.sigma * np.sqrt(dt),
            size = self.n
        )
    
    def realized_vol(self, returns : np.ndarray) -> float : 
        realized_var = np.sum(returns**2)/self.T
        return np.sqrt(realized_var)
    
    def price(self):
        returns = self.simulate_log_returns()
        rv = self.realized_vol(returns)

        payoff = self.N * (rv - self.K)

        df = self.curve.get_discount_factor(self.T)
        price = df * payoff

        return price, rv