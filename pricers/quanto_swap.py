import numpy as np

class QuantoSwapPricer:
    def __init__(self, notional, maturity, frequency, rate_vol, fx_vol, correlation, 
                 discount_curve, projection_curve):
        self.notional = notional
        self.maturity = maturity
        self.n_payments = {"3M": 4, "6M": 2, "1Y": 1}[frequency]
        self.rate_vol = rate_vol
        self.fx_vol = fx_vol
        self.correlation = correlation
        self.discount_curve = discount_curve
        self.projection_curve = projection_curve

    def price(self, custom_corr=None):
        # Utilise la corrélation fournie ou celle par défaut
        corr = custom_corr if custom_corr is not None else self.correlation
        
        times = np.linspace(1/self.n_payments, self.maturity, int(self.maturity * self.n_payments))
        total_pv = 0
        details = []
        
        for t in times:
            df = self.discount_curve.get_discount_factor(t)
            # Taux forward (courbe étrangère)
            fwd_rate = self.projection_curve.get_forward_rate(max(0, t - 1/self.n_payments), t)
            
            # Ajustement de convexité Quanto : rho * sigma_r * sigma_fx * t
            quanto_adj = corr * self.rate_vol * self.fx_vol * t
            adjusted_rate = fwd_rate + quanto_adj
            
            cash_flow = self.notional * adjusted_rate * (1/self.n_payments)
            pv_flow = cash_flow * df
            
            total_pv += pv_flow
            details.append({
                "Maturité": t,
                "Fwd Rate": fwd_rate,
                "Ajustement": quanto_adj,
                "Taux Ajusté": adjusted_rate,
                "PV Flux": pv_flow
            })
            
        return total_pv, details
