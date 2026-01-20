from core.curves import ZeroCouponCurve
from core.hull_white import HullWhiteModel
import numpy as np

class RangeAccrualSwapPricer:
    def __init__(
        self,
        notional: float,
        maturity: float,
        payment_freq: int,
        coupon: float,
        lower_bound: float,
        upper_bound: float,
        discount_curve: ZeroCouponCurve,
        projection_curve: ZeroCouponCurve,
        hw_model,
        n_paths=10000,
        seed=42
    ):
        self.N = notional
        self.T0 = 0.0
        self.Tn = maturity
        self.f = payment_freq
        self.dt_pay = 1 / payment_freq
        self.c = coupon
        self.lower = lower_bound
        self.upper = upper_bound
        self.discount_curve = discount_curve
        self.projection_curve = projection_curve
        self.hw_model = hw_model
        self.n_paths = n_paths
        self.seed = seed

    # Simulation Ornstein-Uhlenbeck des x(t)
    def simulate_x_paths(self, obs_grid):
        rng = np.random.default_rng(self.seed)
        n_times = len(obs_grid)
        x = np.zeros((self.n_paths, n_times))

        a = self.hw_model.a
        sigma = self.hw_model.sigma

        for j in range(1, n_times):
            dt = obs_grid[j] - obs_grid[j - 1]
            z = rng.normal(size=self.n_paths)

            # schéma exact OU
            x[:, j] = (
                x[:, j - 1] * np.exp(-a * dt)
                + sigma * np.sqrt((1 - np.exp(-2 * a * dt)) / (2 * a)) * z
            )

        return x
    
    def bond_price_hw(self, t, T, x_t):
        P0T = self.projection_curve.get_discount_factor(T)
        P0t = self.projection_curve.get_discount_factor(t)

        B = self.hw_model.calc_b(t, T)
        var = self.hw_model.calc_variance(t)

        return (
            P0T / P0t
            * np.exp(-B * x_t - 0.5 * B * B * var)
        )
    
    # InterBank Offered Rate (IBOR) utilisé pour le forward rate
    def forward_ibor_hw(self, t, delta, x_t):
        P = self.bond_price_hw(t, t + delta, x_t)
        P = np.maximum(P, 1e-12)
        return (1.0 / P - 1.0) / delta


    # On crée une liste des dates de paiement
    def create_payment_times(self):
        times = []
        t = self.T0
        while t <= self.Tn + 1e-12:
            times.append(t)
            t += self.dt_pay
        return times

    # On crée une liste des dates d'observation pour le range accrual (on simule un les jours ouvrés : 252 jours par an)
    def create_observation_times(self):
        observation_times = []
        dt_obs = 1 / 252  # pas "jour ouvré" approximé

        for i in range(1, len(self.payment_times)):
            Ti_minus_1 = self.payment_times[i - 1]
            Ti = self.payment_times[i]

            t = Ti_minus_1
            obs_times_i = []

            while t < Ti + 1e-12: # pour inclure Ti avec une petite tolérance pour les erreurs de flottement
                obs_times_i.append(t)
                t += dt_obs

            observation_times.append(obs_times_i)

        return observation_times


    def get_tenor_ibor(self):
        return self.dt_pay # On suppose que le tenor IBOR est égal à la fréquence de paiement

    # Ai represent le pourcentage de temps passé dans l'intervalle [lower_bound, upper_bound] pour la période i
    # On transforme en montcarlo
    def Ai_computation_mc(self, obs_grid, x_paths):
        Ai_list = []
        delta = self.get_tenor_ibor()

        # On parcourt chaque période de paiement
        for obs_times_i in self.observation_times:

            # Nombre de jours d'observation dans la période
            n_obs = len(obs_times_i)

            # Tableau pour stocker, pour chaque scénario,nle nombre de jours où le taux est dans le range
            count_in_range = np.zeros(self.n_paths)

            # Boucle sur les jours de la période
            for t in obs_times_i:
                t_key = round(t, 10) # arrondi pour éviter les problèmes de flottement
                time_index = obs_grid.index(t_key)

                x_t = x_paths[:, time_index]

                L = self.forward_ibor_hw(t_key, delta, x_t)
                in_range = (L >= self.lower) & (L <= self.upper)
                count_in_range += in_range.astype(float)


            # Fraction de temps dans le range pour chaque scénario
            fraction_in_range = count_in_range / n_obs

            # Moyenne Monte Carlo
            Ai = fraction_in_range.mean()

            Ai_list.append(float(Ai))

        return Ai_list


    def compute_cashflows(self):
        cashflows = []

        for i in range(1, len(self.payment_times)):
            alpha_i = self.payment_times[i] - self.payment_times[i - 1]
            Ai = self.Ai_list[i - 1]
            Ci = self.N * self.c * alpha_i * Ai
            cashflows.append(Ci)

        return cashflows

    def compute_present_value(self):
        pv = 0.0

        # cashflows[i] est payé à payment_times[i+1]
        for i, Ci in enumerate(self.cashflows):
            Ti = self.payment_times[i + 1]
            df = self.discount_curve.get_discount_factor(Ti)
            pv += Ci * df

        return pv


    def price_range_accrual(self) -> float:
        """
        Pricing complet d'un Range Accrual Swap (jambe range)
        """
        # Dates de paiement
        self.payment_times = self.create_payment_times()

        # Dates d'observation (daily business days)
        self.observation_times = self.create_observation_times()

        # Calcul des Ai (fractions in-range)
        obs_grid = sorted(
            {round(t,10) for period in self.observation_times for t in period}
        )
        x_paths = self.simulate_x_paths(obs_grid)
        self.Ai_list = self.Ai_computation_mc(obs_grid, x_paths)

        # Cashflows
        self.cashflows = self.compute_cashflows()

        # Actualisation OIS (Overnight Index Swap)
        pv = self.compute_present_value()

        return pv
    