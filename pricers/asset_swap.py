from typing import List
import numpy as np
from core.curves import ZeroCouponCurve
from core.utils import year_fraction

class AssetSwapPricer:

    def __init__(
            self, 
            nominal: float, 
            maturity_years: float,
            bond_coupon_rate: float,
            bond_market_price_pct: float,
            discount_curve: ZeroCouponCurve,
            payment_frequency: str = "1Y"
    ):
        self.N = nominal
        self.maturity = maturity_years
        self.coupon = bond_coupon_rate  
        self.P_mkt = bond_market_price_pct / 100.0 
        self.curve = discount_curve
        
        freq_map = {"1Y": 1.0, "6M": 0.5, "3M": 0.25}
        self.dt = freq_map.get(payment_frequency, 1.0)
        
        self.times = np.arange(self.dt, self.maturity + 0.001, self.dt)

    def calculate_spread(self):
        pv_fix_leg = 0.0
        pv_float_clean = 0.0 
        pv_01 = 0.0          

        for t in self.times:
            t_prev = max(0, t - self.dt)
            
            df = self.curve.get_discount_factor(t)
            
            flow_fix = self.N * self.coupon * self.dt
            pv_fix_leg += df * flow_fix
            
            fwd_rate = self.curve.get_forward_rate(t_prev, t)
            flow_float = self.N * fwd_rate * self.dt
            pv_float_clean += df * flow_float
            
            pv_01 += df * self.N * self.dt

        
        target_swap_pv = (1.0 - self.P_mkt) * self.N
        
        numerator = target_swap_pv + pv_fix_leg - pv_float_clean
        spread = numerator / pv_01
        
        return {
            "spread": spread,           
            "bond_price_val": self.P_mkt * self.N,
            "upfront_payment": target_swap_pv,
            "pv_fix_leg": pv_fix_leg,
            "pv_float_clean": pv_float_clean
        }
