import numpy as np

class PuttableSwapPricer:
    def __init__(self, notional, maturity, fixed_rate, frequency, a, sigma, discount_curve, projection_curve):
        self.notional = notional
        self.maturity = maturity
        self.fixed_rate = fixed_rate
        self.n_payments = {"3M": 4, "6M": 2, "1Y": 1}[frequency]
        self.a = a
        self.sigma = sigma
        self.discount_curve = discount_curve
        self.projection_curve = projection_curve

    def price(self, custom_sigma=None):
        # Permet de tester différents scénarios de volatilité
        sig = custom_sigma if custom_sigma is not None else self.sigma
        
        times = np.linspace(1/self.n_payments, self.maturity, int(self.maturity * self.n_payments))
        pv_vanilla = 0
        details = []
        
        for t in times:
            df = self.discount_curve.get_discount_factor(t)
            fwd = self.projection_curve.get_forward_rate(max(0, t - 1/self.n_payments), t)
            
            # Jambe Flottante - Jambe Fixe
            flow_fixed = self.fixed_rate * (1/self.n_payments) * self.notional
            flow_float = fwd * (1/self.n_payments) * self.notional
            pv_flow = (flow_float - flow_fixed) * df
            
            pv_vanilla += pv_flow
            details.append({
                "Maturité": t,
                "DF": df,
                "Forward": fwd,
                "Flux Net": flow_float - flow_fixed,
                "PV Flux": pv_flow
            })
            
        # Valeur de l'option (Put) : Droit de résilier si la PV du swap devient trop négative
        # Modélisation via l'approximation de la valeur temps de Hull-White
        time_value_factor = (sig * np.sqrt(self.maturity)) / (self.a + 0.05)
        option_value = max(0, -pv_vanilla) * time_value_factor * 0.5
        
        return pv_vanilla, option_value, details
