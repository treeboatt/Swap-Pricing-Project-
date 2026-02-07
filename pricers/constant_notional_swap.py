from core.curves import ZeroCouponCurve

class ConstantNotionalSwapPricer:
    def __init__(
        self,
        notional: float,
        maturity: float,
        payment_freq: int,
        fixed_rate: float,
        discount_curve: ZeroCouponCurve,
        projection_curve: ZeroCouponCurve
    ):
        self.N = notional
        self.T0 = 0.0
        self.Tn = maturity
        self.f = payment_freq
        self.dt_pay = 1 / payment_freq
        self.K = fixed_rate
        self.discount_curve = discount_curve
        self.projection_curve = projection_curve

    # Création des dates de paiement
    def create_payment_times(self):
        times = []
        t = self.T0
        while t <= self.Tn + 1e-12:
            times.append(t)
            t += self.dt_pay
        return times

    # Calcul des cashflows fixes
    def compute_fixed_cashflows(self):
        cashflows = []

        for i in range(1, len(self.payment_times)):
            alpha_i = self.payment_times[i] - self.payment_times[i - 1]
            Ci = self.N * self.K * alpha_i
            cashflows.append(Ci)

        return cashflows

    # Calcul des cashflows flottants (forward IBOR déterministe)
    def compute_floating_cashflows(self):
        cashflows = []

        for i in range(1, len(self.payment_times)):
            t_prev = self.payment_times[i - 1]
            t = self.payment_times[i]
            alpha_i = t - t_prev

            P0 = self.projection_curve.get_discount_factor(t_prev)
            P1 = self.projection_curve.get_discount_factor(t)

            forward_rate = (P0 / P1 - 1.0) / alpha_i
            Ci = self.N * forward_rate * alpha_i

            cashflows.append(Ci)

        return cashflows

    # Actualisation OIS
    def compute_present_value(self, cashflows):
        pv = 0.0

        for i, Ci in enumerate(cashflows):
            Ti = self.payment_times[i + 1]
            df = self.discount_curve.get_discount_factor(Ti)
            pv += Ci * df

        return pv

    def price_constant_notional(self) -> float:
        # Dates de paiement
        self.payment_times = self.create_payment_times()

        # Cashflows
        fixed_cfs = self.compute_fixed_cashflows()
        float_cfs = self.compute_floating_cashflows()

        # Valeurs actuelles
        pv_fixed = self.compute_present_value(fixed_cfs)
        pv_float = self.compute_present_value(float_cfs)

        # Receive float - pay fixed
        pv = pv_float - pv_fixed

        return pv
