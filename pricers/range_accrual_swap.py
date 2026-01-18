from core.curves import ZeroCouponCurve


"""
################################
    # Données générales
    ################################
    N = 1_000_000 # Notionel
    T0 = 0 # Date de début
    Tn = 5 # Date de fin
    f = 4 # Frequence des paiements par an
    dt_pay = 1 / f # Intervalle entre paiements
    day_count = "ACT/360" # convention de calcul des fractions annuelles

    ################################
    # Discount curve
    ################################

    # Quotes de marché OIS (exemple)
    ois_market_quotes = {
        1.0: 0.030,
        2.0: 0.032,
        3.0: 0.034,
        5.0: 0.038,
        10.0: 0.040
    }

    # Construction de la courbe OIS par bootstrapping (0 coupons)
    discount_curve = ZeroCouponCurve.bootstrap_ois_curve(
        ois_market_quotes,
        curve_name="EUR-OIS"
    )

    ################################
    # Projection curve
    ################################

    # Zéros IBOR fictifs (exemple pédagogique)
    ibor_times = [0.0, 1.0, 2.0, 3.0, 5.0, 10.0]
    ibor_zero_rates = [0.031, 0.033, 0.035, 0.037, 0.039, 0.041]

    # Construction de la courbe IBOR
    projection_curve = ZeroCouponCurve(
        ibor_times,
        ibor_zero_rates,
        curve_name="EUR-IBOR-3M"
    )

    ################################
    # Jambe range accrual
    ################################
    c = 0.05 # Coupon promis
    lower_bound = 0.02 # bornes inf du range
    upper_bound = 0.04 # bornes sup du range
    
"""



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
        projection_curve: ZeroCouponCurve
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
        return self.dt_pay # supposons que le tenor IBOR est égal à la fréquence de paiement

    # Ai represent le pourcentage de temps passé dans l'intervalle [lower_bound, upper_bound] pour la période i
    def Ai_computation(self):
        Ai_list = []

        for obs_times_i in self.observation_times:
            count_in_range = 0
            total_obs = len(obs_times_i)

            for t in obs_times_i:
                forward_rate_t = self.projection_curve.get_forward_rate(t, t + self.get_tenor_ibor())
                if self.lower <= forward_rate_t <= self.upper:
                    count_in_range += 1

            # fraction de temps passé dans l'intervalle
            Ai = count_in_range / total_obs if total_obs > 0 else 0.0
            Ai_list.append(Ai)

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
        Pricing complet d'un Range Accrual Swap (jambe range seule)
        """
        # Dates de paiement
        self.payment_times = self.create_payment_times()

        # Dates d'observation (daily business days)
        self.observation_times = self.create_observation_times()

        # Calcul des Ai (fractions in-range)
        self.Ai_list = self.Ai_computation()

        # Cashflows
        self.cashflows = self.compute_cashflows()

        # Actualisation OIS
        pv = self.compute_present_value()

        return pv
    