import numpy as np

class VarianceSwapPricer:
    def __init__(self, notional_vega, strike_vol, realized_vol, maturity, discount_curve):
        self.notional_vega = notional_vega
        self.strike_vol = strike_vol
        self.realized_vol = realized_vol
        self.maturity = maturity
        self.discount_curve = discount_curve

    def calculate_pv(self, custom_vol=None):
        """Calcule la PV avec une volatilité réalisée spécifique ou celle par défaut."""
        vol = custom_vol if custom_vol is not None else self.realized_vol
        
        # Notionnel Variance = N_vega / (2 * K_vol)
        # C'est la conversion standard pour que 1 point de vol = N_vega en profit/perte
        notional_var = self.notional_vega / (2 * self.strike_vol)
        
        variance_strike = self.strike_vol**2
        variance_realized = vol**2
        
        df = self.discount_curve.get_discount_factor(self.maturity)
        
        payoff = notional_var * (variance_realized - variance_strike)
        return payoff * df
