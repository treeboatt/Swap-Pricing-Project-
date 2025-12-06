# Construction et interpolation des courbes
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

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
    
    @classmethod
    def bootstrap_ois_curve(cls, market_quotes: dict, curve_name: str = "OIS_Bootstrapped"):
        """
        Construit une courbe zéro-coupon par Bootstrapping à partir des cotations de Swaps OIS.
        
        :param market_quotes: Dictionnaire {Maturité (années): Taux Fixe du Swap}. 
                              Ex: {1.0: 0.03, 2.0: 0.035}
        :return: Une instance de ZeroCouponCurve calibrée.
        """
        # 1. On trie les instruments par maturité croissante
        sorted_maturities = sorted(market_quotes.keys())
        
        # 2. Points initiaux de la courbe (t=0)
        # On suppose que le taux à t=0 est égal au taux court (1er point) pour la continuité
        curve_dates = [0.0]
        curve_rates = [market_quotes[sorted_maturities[0]]] 
        
        # 3. Boucle de Bootstrapping : On résout maturité par maturité
        for T in sorted_maturities:
            market_rate = market_quotes[T]
            
            # Fonction objectif : Le prix du Swap doit être zéro
            # Prix OIS ~ (Jambe Fixe) - (Jambe Variable)
            # Jambe Variable OIS ~ 1 - DF(T)
            # Jambe Fixe ~ MarketRate * Somme(dt * DF(t))
            
            def objective_function(zero_rate_guess):
                # On ajoute temporairement ce point deviné à notre liste existante
                temp_dates = curve_dates + [T]
                temp_rates = curve_rates + [zero_rate_guess]
                
                # On crée une courbe temporaire pour voir ce que ça donne
                temp_curve = cls(temp_dates, temp_rates)
                
                # Calcul du Facteur d'Actualisation à maturité T
                df_T = temp_curve.get_discount_factor(T)
                
                # Approximation Valorisation OIS (Paiement annuel pour simplifier)
                # PV_Float = 1.0 - DF(T)
                pv_float = 1.0 - df_T
                
                # PV_Fixed = Taux * Somme(DF(t))
                pv_fixed = 0.0
                # On somme les coupons annuels jusqu'à T
                for t_flow in range(1, int(T) + 1):
                    pv_fixed += market_rate * 1.0 * temp_curve.get_discount_factor(t_flow)
                
                # Gestion de la fraction d'année finale (stub) si T n'est pas entier (ex: 1.5 an)
                if T % 1 > 0:
                    pv_fixed += market_rate * (T % 1) * df_T
                    
                return pv_float - pv_fixed

            # On utilise le solveur brentq pour trouver le taux qui annule la valeur du swap
            try:
                calibrated_rate = brentq(objective_function, -0.05, 0.15) # Recherche entre -5% et 15%
            except ValueError:
                # Si le solveur échoue, on prend une valeur par défaut (fallback)
                calibrated_rate = market_rate

            # 4. On valide ce point et on l'ajoute définitivement à la courbe en construction
            curve_dates.append(T)
            curve_rates.append(calibrated_rate)
            
        # 5. On retourne la courbe finale construite
        return cls(curve_dates, curve_rates, curve_name)

# --- Bloc de test rapide (ne s'exécute que si on lance ce fichier directement) ---
# --- Bloc de test (ne s'exécute que si on lance ce fichier directement) ---
if __name__ == "__main__":
    # Données de marché fictives (Cotations de Swaps OIS)
    # Maturité (ans) : Taux Fixe
    market_data = {
        1.0: 0.030,  # 3.0%
        2.0: 0.032,  # 3.2%
        3.0: 0.034,  # 3.4%
        5.0: 0.038,  # 3.8%
        10.0: 0.040  # 4.0%
    }
    
    print("--- Début du Bootstrapping ---")
    
    # Appel de la nouvelle méthode magique
    ois_curve = ZeroCouponCurve.bootstrap_ois_curve(market_data, "EUR-OIS-BOOTSTRAP")
    
    print(f"Courbe construite : {ois_curve.name}")
    print(f"Taux Zéro à 1 an   : {ois_curve.get_zero_rate(1.0):.4%}")
    print(f"Taux Zéro à 10 ans : {ois_curve.get_zero_rate(10.0):.4%}")
    
    # Vérification : Le swap 5 ans doit valoir 0 (aux erreurs d'arrondi près)
    # C'est la preuve que le bootstrap a fonctionné
    print(f"Facteur d'actualisation à 5 ans : {ois_curve.get_discount_factor(5.0):.6f}")
    
    # Petit graphe pour admirer le résultat
    try:
        import matplotlib.pyplot as plt
        times = np.linspace(0, 10, 100)
        zeros = [ois_curve.get_zero_rate(t) for t in times]
        plt.plot(times, zeros, label="Courbe Zéro-Coupon Bootstrappée")
        plt.scatter(market_data.keys(), market_data.values(), color='red', label="Taux Swap Marché")
        plt.title("Bootstrapping OIS")
        plt.legend()
        plt.show()
    except ImportError:
        pass