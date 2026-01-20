import numpy as np
from typing import List

from core.curves import ZeroCouponCurve
from core.utils import year_fraction


class AmortizingSwapPricer:
    """
    Pricer pour un Amortizing Swap.
    
    Un amortizing swap est un swap de taux d'intérêt où le notionnel 
    décroît selon un calendrier prédéfini (ex: remboursement progressif d'un prêt).
    
    Structure:
    - Jambe fixe: paie taux_fixe * notionnel_courant * dt
    - Jambe flottante: paie taux_forward * notionnel_courant * dt
    """
    
    def __init__(
        self,
        notional_schedule: List[float],  # notionnel à chaque période
        fixed_rate: float,                # taux fixe du swap
        payment_times: List[float],       # dates de paiement
        discount_curve: ZeroCouponCurve   # courbe d'actualisation
    ):
        """
        Args:
            notional_schedule: liste des notionnels correspondant à chaque période
            fixed_rate: taux fixe du swap (annualisé)
            payment_times: dates de paiement (en années)
            discount_curve: courbe ZeroCoupon pour l'actualisation
        """
        self.notional_schedule = notional_schedule
        self.fixed_rate = fixed_rate
        self.times = payment_times
        self.curve = discount_curve
        
        assert len(notional_schedule) == len(payment_times) - 1, \
            "notional_schedule doit avoir une longueur = len(payment_times) - 1"

    def fixed_leg_cf(self, period_idx: int) -> float:
        """Calcule le flux de la jambe fixe pour la période."""
        if period_idx >= len(self.notional_schedule):
            return 0.0
        
        t1 = self.times[period_idx]
        t2 = self.times[period_idx + 1]
        dt = year_fraction(t1, t2)
        notional = self.notional_schedule[period_idx]
        
        return notional * self.fixed_rate * dt

    def floating_leg_cf(self, period_idx: int) -> float:
        """Calcule le flux de la jambe flottante pour la période."""
        if period_idx >= len(self.notional_schedule):
            return 0.0
        
        t1 = self.times[period_idx]
        t2 = self.times[period_idx + 1]
        
        # Forward rate entre t1 et t2
        fwd = self.curve.get_forward_rate(t1, t2)
        dt = year_fraction(t1, t2)
        notional = self.notional_schedule[period_idx]
        
        return notional * fwd * dt

    def discount_factor(self, t: float) -> float:
        """Facteur d'actualisation à la date t."""
        return self.curve.get_discount_factor(t)

    def price(self) -> float:
        """
        Calcule le PV du swap (du point de vue du payeur de taux fixe).
        
        PV = somme des flux actualisés
        Un swap "vanilla" a PV = 0 en initiation.
        Si PV > 0, le swap vaut plus qu'une valeur nulle.
        """
        pv = 0.0
        
        for period_idx in range(len(self.notional_schedule)):
            t1 = self.times[period_idx]
            t2 = self.times[period_idx + 1]
            
            # Milieu de la période pour l'actualisation (approximation)
            t_mid = (t1 + t2) / 2
            df = self.discount_factor(t_mid)
            
            # Flux: jambe flottante (reçue) - jambe fixe (payée)
            fixed_cf = self.fixed_leg_cf(period_idx)
            floating_cf = self.floating_leg_cf(period_idx)
            
            net_cf = floating_cf - fixed_cf
            pv += net_cf * df
        
        return pv

    def get_schedule_summary(self) -> dict:
        """Retourne un résumé du calendrier d'amortissement et des flux."""
        summary = []
        
        for period_idx in range(len(self.notional_schedule)):
            t1 = self.times[period_idx]
            t2 = self.times[period_idx + 1]
            dt = year_fraction(t1, t2)
            
            notional = self.notional_schedule[period_idx]
            fixed_cf = self.fixed_leg_cf(period_idx)
            floating_cf = self.floating_leg_cf(period_idx)
            fwd = self.curve.get_forward_rate(t1, t2)
            df = self.discount_factor((t1 + t2) / 2)
            
            summary.append({
                "période": period_idx + 1,
                "début": f"{t1:.2f}Y",
                "fin": f"{t2:.2f}Y",
                "notionnel": f"{notional:,.0f}",
                "taux_fwd": f"{fwd*100:.3f}%",
                "cf_fixe": f"{fixed_cf:,.2f}",
                "cf_flottant": f"{floating_cf:,.2f}",
                "df": f"{df:.4f}"
            })
        
        return summary

    def calculate_fair_swap_rate(self) -> float:
        """
        Calcule le taux fixe d'équilibre (fair rate) qui rend le PV = 0.
        
        C'est le taux auquel le swap devrait être initié pour que sa valeur soit nulle.
        """
        # PV de la jambe flottante
        pv_floating = 0.0
        for period_idx in range(len(self.notional_schedule)):
            t1 = self.times[period_idx]
            t2 = self.times[period_idx + 1]
            t_mid = (t1 + t2) / 2
            
            floating_cf = self.floating_leg_cf(period_idx)
            df = self.discount_factor(t_mid)
            pv_floating += floating_cf * df
        
        denominator = 0.0
        for period_idx in range(len(self.notional_schedule)):
            t1 = self.times[period_idx]
            t2 = self.times[period_idx + 1]
            dt = year_fraction(t1, t2)
            notional = self.notional_schedule[period_idx]
            df = self.discount_factor((t1 + t2) / 2)
            denominator += notional * dt * df
        
        if denominator == 0:
            return 0.0
        
        fair_rate = pv_floating / denominator
        return fair_rate
