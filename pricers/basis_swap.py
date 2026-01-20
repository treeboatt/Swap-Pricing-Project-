import numpy as np
from typing import List

from core.curves import ZeroCouponCurve
from core.utils import year_fraction


class BasisSwapPricer:
    """
    Pricer pour un Basis Swap.
    
    Un basis swap échange deux taux flottants différents avec un spread (basis).
    Exemple: 
    - Jambe 1: EURIBOR 3M
    - Jambe 2: EURIBOR 6M + spread
    
    Le basis spread rémunère la différence de terme entre les deux taux.
    """
    
    def __init__(
        self,
        notional: float,
        basis_spread: float,        # spread appliqué à la jambe 2 (en % annualisé)
        payment_times: List[float], # dates de paiement (en années)
        discount_curve: ZeroCouponCurve,
        tenor_1: float = 0.25,      # tenor jambe 1 en années (ex: 3M = 0.25)
        tenor_2: float = 0.5        # tenor jambe 2 en années (ex: 6M = 0.5)
    ):
        """
        Args:
            notional: notionnel du swap (constant)
            basis_spread: spread appliqué à la jambe 2 (annualisé)
            payment_times: dates de paiement (en années)
            discount_curve: courbe ZeroCoupon pour l'actualisation
            tenor_1: tenor de la jambe 1 (ex: 0.25 pour 3M)
            tenor_2: tenor de la jambe 2 (ex: 0.5 pour 6M)
        """
        self.notional = notional
        self.basis_spread = basis_spread
        self.times = payment_times
        self.curve = discount_curve
        self.tenor_1 = tenor_1
        self.tenor_2 = tenor_2

    def leg1_cf(self, period_idx: int) -> float:
        """Calcule le flux de la jambe 1 (taux flottant 1) pour la période."""
        if period_idx >= len(self.times) - 1:
            return 0.0
        
        t1 = self.times[period_idx]
        t2 = self.times[period_idx + 1]
        
        # Forward rate pour le tenor 1
        # Exemple: si tenor_1 = 0.25 (3M), on prend le forward EURIBOR 3M
        fwd1 = self.curve.get_forward_rate(t1, t1 + self.tenor_1)
        dt = year_fraction(t1, t2)
        
        return self.notional * fwd1 * dt

    def leg2_cf(self, period_idx: int) -> float:
        """Calcule le flux de la jambe 2 (taux flottant 2 + spread) pour la période."""
        if period_idx >= len(self.times) - 1:
            return 0.0
        
        t1 = self.times[period_idx]
        t2 = self.times[period_idx + 1]
        
        # Forward rate pour le tenor 2
        fwd2 = self.curve.get_forward_rate(t1, t1 + self.tenor_2)
        dt = year_fraction(t1, t2)
        
        # Ajouter le spread
        total_rate = fwd2 + self.basis_spread
        
        return self.notional * total_rate * dt

    def discount_factor(self, t: float) -> float:
        """Facteur d'actualisation à la date t."""
        return self.curve.get_discount_factor(t)

    def price(self) -> float:
        """
        Calcule le PV du basis swap (du point de vue du payeur de la jambe 1).
        
        PV = somme des flux actualisés
        PV = jambe 2 (reçue) - jambe 1 (payée)
        
        Si PV > 0: recevoir jambe 2 est avantageux pour le payeur 1.
        Si PV < 0: recevoir jambe 2 est désavantageux pour le payeur 1.
        """
        pv = 0.0
        
        for period_idx in range(len(self.times) - 1):
            t1 = self.times[period_idx]
            t2 = self.times[period_idx + 1]
            t_mid = (t1 + t2) / 2
            
            df = self.discount_factor(t_mid)
            
            # Flux: jambe 2 (reçue) - jambe 1 (payée)
            cf1 = self.leg1_cf(period_idx)
            cf2 = self.leg2_cf(period_idx)
            
            net_cf = cf2 - cf1  # Recevoir jambe 2, payer jambe 1
            pv += net_cf * df
        
        return pv

    def calculate_fair_basis_spread(self) -> float:
        """
        Calcule le spread d'équilibre (fair spread) qui rend le PV = 0.
        
        C'est le spread auquel le basis swap devrait être initié pour que sa valeur soit nulle.
        """
        # PV de la jambe 1
        pv_leg1 = 0.0
        for period_idx in range(len(self.times) - 1):
            t1 = self.times[period_idx]
            t2 = self.times[period_idx + 1]
            t_mid = (t1 + t2) / 2
            
            cf1 = self.leg1_cf(period_idx)
            df = self.discount_factor(t_mid)
            pv_leg1 += cf1 * df
        

        denominator = 0.0
        pv_leg2_base = 0.0
        
        for period_idx in range(len(self.times) - 1):
            t1 = self.times[period_idx]
            t2 = self.times[period_idx + 1]
            dt = year_fraction(t1, t2)
            t_mid = (t1 + t2) / 2
            df = self.discount_factor(t_mid)
            
            # Forward pour leg2
            fwd2 = self.curve.get_forward_rate(t1, t1 + self.tenor_2)
            cf2_base = self.notional * fwd2 * dt
            pv_leg2_base += cf2_base * df
            
            denominator += self.notional * dt * df
        
        if denominator == 0:
            return 0.0
        
        fair_spread = (pv_leg1 - pv_leg2_base) / denominator
        return fair_spread

    def get_schedule_summary(self) -> list:
        """Retourne un résumé du calendrier et des flux."""
        summary = []
        
        for period_idx in range(len(self.times) - 1):
            t1 = self.times[period_idx]
            t2 = self.times[period_idx + 1]
            dt = year_fraction(t1, t2)
            
            # Forwards
            fwd1 = self.curve.get_forward_rate(t1, t1 + self.tenor_1)
            fwd2 = self.curve.get_forward_rate(t1, t1 + self.tenor_2)
            
            cf1 = self.leg1_cf(period_idx)
            cf2 = self.leg2_cf(period_idx)
            df = self.discount_factor((t1 + t2) / 2)
            
            tenor_1_label = f"{int(self.tenor_1*12)}M" if self.tenor_1 < 1 else f"{int(self.tenor_1)}Y"
            tenor_2_label = f"{int(self.tenor_2*12)}M" if self.tenor_2 < 1 else f"{int(self.tenor_2)}Y"
            
            summary.append({
                "période": period_idx + 1,
                "début": f"{t1:.2f}Y",
                "fin": f"{t2:.2f}Y",
                f"fwd_{tenor_1_label}": f"{fwd1*100:.3f}%",
                f"fwd_{tenor_2_label}": f"{fwd2*100:.3f}%",
                f"cf_{tenor_1_label}": f"{cf1:,.2f}",
                f"cf_{tenor_2_label}+spread": f"{cf2:,.2f}",
                "df": f"{df:.4f}"
            })
        
        return summary
