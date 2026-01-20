import numpy as np
from typing import List

from core.hull_white import HullWhiteModel
from core.curves import ZeroCouponCurve
from core.utils import year_fraction

class HullWhiteTree:
    def __init__(
        self,
        hw_model: HullWhiteModel,
        discount_curve: ZeroCouponCurve,
        times: List[float]
    ):
        self.hw = hw_model
        self.curve = discount_curve
        self.times = times
        self.dt = np.diff(times)

        self.tree = []
        self._build_tree()

    def _build_tree(self):
        r0 = self.curve.get_zero_rate(0.0)
        self.tree = [[r0]]

        for i, t in enumerate(self.times[1:]):
            var = self.hw.calc_variance(t)
            dx = np.sqrt(var)

            level = []
            for j in range(i + 2):
                rate = r0 + (2 * j - (i + 1)) * dx
                level.append(rate)

            self.tree.append(level)

    def discount(self, level_index: int, r: float) -> float:
        dt = self.dt[level_index]
        return np.exp(-r * dt)


class CallableSwapPricer:
    def __init__(
        self,
        notional: float,
        fixed_rate: float,
        payment_times: List[float],
        call_times: List[float],
        discount_curve: ZeroCouponCurve,
        hw_model: HullWhiteModel
    ):
        self.N = notional
        self.fixed_rate = fixed_rate
        self.times = payment_times
        self.call_times = call_times
        self.curve = discount_curve
        self.hw = hw_model

        self.tree = HullWhiteTree(hw_model, discount_curve, payment_times)

    def _is_call_date(self, t: float, tol: float = 1e-10) -> bool:
        return any(abs(t - tc) < tol for tc in self.call_times)

    def fixed_leg_cf(self, dt: float) -> float:
        return self.N * self.fixed_rate * dt

    def floating_leg_cf(self, t1: float, t2: float) -> float:
        fwd = self.curve.get_forward_rate(t1, t2)
        dt = year_fraction(t1, t2)
        return self.N * fwd * dt

    def price(self) -> float:
        n = len(self.times)
        values = []

        #condition finale
        dt_last = year_fraction(self.times[-2], self.times[-1])

        last_values = []
        for _ in self.tree.tree[-1]:
            cf_fixed = self.fixed_leg_cf(dt_last)
            cf_float = self.floating_leg_cf(self.times[-2], self.times[-1])
            last_values.append(cf_fixed - cf_float)

        values.append(last_values)

        #backward induction
        for i in reversed(range(n - 1)):
            t = self.times[i]
            dt = year_fraction(t, self.times[i + 1])

            current = []
            next_values = values[-1]

            for j, r in enumerate(self.tree.tree[i]):
                cont = 0.5 * next_values[j] + 0.5 * next_values[j + 1]
                cont *= self.tree.discount(i, r)

                cf_fixed = self.fixed_leg_cf(dt)
                cf_float = self.floating_leg_cf(t, self.times[i + 1])
                cont += cf_fixed - cf_float

                if self._is_call_date(t):
                    value = min(cont, 0.0)
                else:
                    value = cont

                current.append(value)

            values.append(current)

        return values[-1][0]
