import numpy as np

class QuantoSwapPricer:
    def __init__(self, notional, maturity, frequency, rate_vol, fx_vol, correlation, 
                 discount_curve, projection_curve):
        self.notional = notional
        self.maturity = maturity
        # Conversion de la fréquence (ex: '3M' -> 4 paiements par an)
        self.n_payments = 12 // int(frequency.replace('M', '').replace('Y', '12'))
        self.rate_vol = rate_vol
        self.fx_vol = fx_vol
        self.correlation = correlation
        self.discount_curve = discount_curve
        self.projection_curve = projection_curve

    def price(self):
        # Génération des dates de flux (ex: 0.25, 0.5, ...)
        times = np.linspace(1/self.n_payments, self.maturity, int(self.maturity * self.n_payments))
        total_pv = 0
        details = []
        
        for t in times:
            df = self.discount_curve.get_discount_factor(t)
            # Taux forward sur la courbe étrangère
            fwd_rate = self.projection_curve.get_forward_rate(max(0, t - 1/self.n_payments), t)
            
            # Ajustement Quanto (Convexity Adjustment)
            # E[R] = Fwd + rho * sigma_rate * sigma_fx * t
            convexity_adj = self.correlation * self.rate_vol * self.fx_vol * t
            adjusted_rate = fwd_rate + convexity_adj
            
            # Calcul du flux actualisé
            cash_flow = self.notional * adjusted_rate * (1/self.n_payments)
            pv_flow = cash_flow * df
            total_pv += pv_flow
            
            details.append({
                "Maturité": round(t, 2),
                "Fwd Rate": fwd_rate,
                "Ajustement": convexity_adj,
                "PV Flux": pv_flow
            })
            
        return total_pv, details
