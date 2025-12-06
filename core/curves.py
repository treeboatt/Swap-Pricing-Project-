# Construction et interpolation des courbes
import numpy as np
from scipy.interpolate import PchipInterpolator

class ZeroCouponCurve:
    """
    Classe représentant une courbe de taux Zéro-Coupon.
    Implémente l'interpolation par Spline Cubique Monotone (PCHIP)
    conformément aux spécifications techniques.
    """
    
    def __init__(self, dates_in_years: list, zero_rates: list, curve_name: str = "OIS"):
        """
        Initialise la courbe avec des maturités et des taux zéro-coupon.
        
        :param dates_in_years: Liste des maturités en années (ex: [0.5, 1.0, 2.0])
        :param zero_rates: Liste des taux zéro-coupon correspondants (ex: [0.03, 0.035, ...])
        :param curve_name: Nom de la courbe (ex: "EUR-OIS-ESTR" ou "EUR-IBOR-3M")
        """
        # Tri des données par date pour assurer la cohérence de l'interpolation
        sorted_indices = np.argsort(dates_in_years)
        self.times = np.array(dates_in_years)[sorted_indices]
        self.rates = np.array(zero_rates)[sorted_indices]
        self.name = curve_name
        
        # Initialisation de l'interpolateur Spline Cubique Monotone
        # PCHIP = Piecewise Cubic Hermite Interpolating Polynomial
        self.interpolator = PchipInterpolator(self.times, self.rates)

    def get_zero_rate(self, t: float) -> float:
        """
        Récupère le taux zéro-coupon interpolé à la date t.
        
        :param t: Maturité en années
        :return: Taux zéro-coupon interpolé
        """
        # Gestion des cas limites (extrapolation plate si t < min ou t > max)
        if t <= self.times[0]:
            return self.rates[0]
        if t >= self.times[-1]:
            return self.rates[-1]
            
        return float(self.interpolator(t))

    def get_discount_factor(self, t: float) -> float:
        """
        Calcule le facteur d'actualisation DF(t) = exp(-r * t).
        C'est la méthode principale utilisée par les Pricers.
        
        :param t: Maturité en années
        :return: Facteur d'actualisation
        """
        # Si t=0, le facteur d'actualisation est 1.0
        if t == 0:
            return 1.0
            
        r = self.get_zero_rate(t)
        return np.exp(-r * t)

    def get_forward_rate(self, t1: float, t2: float) -> float:
        """
        Calcule le taux forward implicite entre t1 et t2.
        Utile pour la courbe de projection (IBOR).
        
        :param t1: Date de début
        :param t2: Date de fin
        :return: Taux forward annualisé
        """
        if t1 == t2:
            return self.get_zero_rate(t1)
        
        df1 = self.get_discount_factor(t1)
        df2 = self.get_discount_factor(t2)
        
        # Formule : DF(t2) = DF(t1) * exp(-fwd * (t2-t1))
        # Donc fwd = -ln(DF2/DF1) / (t2-t1)
        dt = t2 - t1
        fwd = -np.log(df2 / df1) / dt
        return fwd

# --- Bloc de test rapide (ne s'exécute que si on lance ce fichier directement) ---
if __name__ == "__main__":
    # Données fictives pour tester
    maturities = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    rates = [0.02, 0.025, 0.028, 0.030, 0.035, 0.040]
    
    # Création de la courbe
    curve = ZeroCouponCurve(maturities, rates, "Test-Curve")
    
    # Test d'interpolation à 1.5 an
    t_test = 1.5
    rate = curve.get_zero_rate(t_test)
    df = curve.get_discount_factor(t_test)
    
    print(f"--- Test de la courbe {curve.name} ---")
    print(f"Taux interpolé à {t_test} ans : {rate:.4%}")
    print(f"Facteur d'actualisation (DF)  : {df:.6f}")
    
    # Vérification graphique (optionnel, si matplotlib est installé)
    try:
        import matplotlib.pyplot as plt
        x_range = np.linspace(0, 10, 100)
        y_range = [curve.get_zero_rate(x) for x in x_range]
        plt.plot(maturities, rates, 'o', label='Données Marché')
        plt.plot(x_range, y_range, '-', label='Spline Monotone (PCHIP)')
        plt.title("Interpolation Spline Cubique Monotone")
        plt.legend()
        plt.show()
    except ImportError:
        print("Matplotlib non installé, pas de graphe généré.")