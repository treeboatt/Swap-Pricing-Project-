import numpy as np

class HullWhiteModel:
    
    def __init__(self, a: float, sigma: float):
        # a: vitesse retour moyenne
        # sigma: volatilite du taux court
        self.a = a
        self.sigma = sigma

    def calc_b(self, t: float, T: float) -> float:
        #transforme le taux en prix
        dt = T - t
        if self.a == 0:
            return dt
        return (1.0 - np.exp(-self.a * dt)) / self.a

    def calc_variance(self, t: float) -> float:
        #pour calculer l'écartement de l'arbre
        if self.a == 0:
            return (self.sigma ** 2) * t
        return (self.sigma ** 2) / (2 * self.a) * (1.0 - np.exp(-2 * self.a * t))

if __name__ == "__main__":
    # test rapide
    hw = HullWhiteModel(a=0.03, sigma=0.01)
    print(f"modele hw initie: a={hw.a}, sigma={hw.sigma}")
    
    # test coefficient B pour 1 an
    b_val = hw.calc_b(0, 1.0)
    print(f"coeff B(0, 1): {b_val:.6f}")
    
    # test variance a 5 ans
    var_val = hw.calc_variance(5.0)
    print(f"variance taux a 5 ans: {var_val:.8f}")