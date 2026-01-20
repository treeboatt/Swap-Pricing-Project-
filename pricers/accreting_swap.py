import numpy as np
from core.curves import ZeroCouponCurve
from core.utils import year_fraction

class AccretingSwapPricer:
    def __init__(self, notionals, payment_times, fixed_rate, discount_curve):
        self.notionals = np.array(notionals)
        self.times = np.array(payment_times)
        self.fixed_rate = fixed_rate
        self.curve = discount_curve

    def price(self) -> float:
        pv = 0.0
        for i in range(len(self.notionals)):
            t_start = self.times[i]
            t_end = self.times[i+1]
            dt = year_fraction(t_start, t_end)
            
            fwd = self.curve.get_forward_rate(t_start, t_end)
            df = self.curve.get_discount_factor(t_end)
            
            pv += self.notionals[i] * (fwd - self.fixed_rate) * dt * df
            
        return pv