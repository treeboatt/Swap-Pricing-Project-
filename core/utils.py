# Fonctions génériques
import numpy as np

def year_fraction(t1: float, t2: float, convention: str = "ACT/365") -> float:
    # calcule la fraction d'annee entre deux dates (en annees)
    # t1 et t2 sont deja des flottants (ex: 0.0, 0.5)
    
    if t2 < t1:
        raise ValueError(f"date fin {t2} < date debut {t1}")

    dt_raw = t2 - t1

    if convention == "ACT/365":
        # standard pour ce projet (1.0 = 1 an)
        return dt_raw
    
    elif convention == "ACT/360":
        # convention marche monetaire eur (euribor)
        # on convertit en jours puis div par 360
        return (dt_raw * 365.0) / 360.0
    
    elif convention == "30/360":
        # approximation classique obligations
        return dt_raw * (365.0 / 360.0)
    
    else:
        raise ValueError(f"convention inconnue: {convention}")

if __name__ == "__main__":
    # test rapide
    print(f"act/365 (0 -> 0.5): {year_fraction(0, 0.5, 'ACT/365'):.6f}")
    print(f"act/360 (0 -> 0.5): {year_fraction(0, 0.5, 'ACT/360'):.6f}")