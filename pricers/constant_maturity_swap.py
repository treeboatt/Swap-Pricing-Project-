import numpy as np

class CMSPricer:
    def __init__(self, discount_curve, swap_surface):
        self.discount_curve = discount_curve
        self.swap_surface = swap_surface

    def get_discount_factor(self, date):
        return 1 / (1 + 0.03 * date)

    def get_forward_swap_rate(self, date, tenor):
        return 0.035  # 3.5%

    def get_convexity_adjustment(self, fwd_rate, vol, time):
        convexity = 0.5 * (fwd_rate ** 2) * (vol ** 2) * time 
        return convexity

    def calculate_price(self, nominal, fix_rate, maturity_years, cms_tenor, payment_frequency=1):
        pv_cms_leg = 0
        pv_fix_leg = 0
        
        schedule = np.arange(1, maturity_years + 1, 1/payment_frequency)
        
        for ti in schedule:
            year_frac = 1.0 / payment_frequency
            df = self.get_discount_factor(ti)
            
            fwd_s = self.get_forward_swap_rate(ti, cms_tenor)
            
            vol_swap = 0.20
            conv_adj = self.get_convexity_adjustment(fwd_s, vol_swap, ti)
            
            adjusted_cms_i = fwd_s + conv_adj
            
            flow_cms = adjusted_cms_i * year_frac
            
            pv_cms_leg += df * flow_cms
            
            flow_fix = fix_rate * year_frac
            pv_fix_leg += df * flow_fix

        pv_cms_leg *= nominal
        pv_fix_leg *= nominal
        
        price = pv_cms_leg - pv_fix_leg
        
        return {
            "price": price,
            "leg_cms": pv_cms_leg,
            "leg_fix": pv_fix_leg
        }