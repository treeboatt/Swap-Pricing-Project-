from typing import List
from core.curves import ZeroCouponCurve
from core.utils import year_fraction 

class StepDownPricer:
    def __init__(
            self, 
            notional : float, 
            payment_times: List[float],
            fixed_rates : List[float], 
            discount_curve : ZeroCouponCurve, 
    ):
        self.N = notional
        self.times = payment_times
        self.rates = fixed_rates 
        self.curve = discount_curve

        assert len(self.times) - 1 == len(self.rates)

    def fixed_leg(self, i: int) -> float:
        t1, t2 = self.times[i], self.times[i+1]
        dt = year_fraction(t1, t2)
        return self.N * self.rates[i] * dt
    
    def floating_leg(self, i: int) -> float :
        t1, t2 = self.times[i], self.times[i+1]
        dt = year_fraction(t1, t2)
        fwd = self.curve.get_forward_rate(t1, t2)
        return self.N * fwd * dt
    
    def price(self) -> float:
        pv = 0.0

        for i in range(len(self.fixed_rates)):
            t_pay = self.times[i+1]
            cf_fixed = self.fixed_leg(i)
            cf_float = self.floating_leg(i)
            df = self.curve.get_discount_factor(t_pay)
            pv+=df*(cf_fixed - cf_float)
            
        return pv

