import numpy as np
from core.curves import ZeroCouponCurve
from core.utils import year_fraction

class MtMSwapPricer:
    def __init__(self, base_notional, fx_rates, payment_times, fixed_rate, discount_curve):
        self.n0 = base_notional
        self.fx_rates = np.array(fx_rates)
        self.times = np.array(payment_times)
        self.fixed_rate = fixed_rate
        self.curve = discount_curve

    def price(self) -> float:
        pv = 0.0
        s0 = self.fx_rates[0]
        
        for i in range(len(self.times) - 1):
            t_start = self.times[i]
            t_end = self.times[i+1]
            dt = year_fraction(t_start, t_end)
            
            notional_i = self.n0 * (self.fx_rates[i+1] / s0)
            
            fwd = self.curve.get_forward_rate(t_start, t_end)
            df = self.curve.get_discount_factor(t_end)
            
            pv += notional_i * (fwd - self.fixed_rate) * dt * df
            
        return pv