import numpy as np

def price_accreting_swap(notional_schedule, fixed_rate, floating_rates, periods, discount_factors):
    fixed_leg = np.sum(notional_schedule * fixed_rate * periods * discount_factors)
    floating_leg = np.sum(notional_schedule * floating_rates * periods * discount_factors)
    return floating_leg - fixed_leg