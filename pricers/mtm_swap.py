import numpy as np

def price_mtm_swap(base_notional, fx_rates, fixed_rate, floating_rates, periods, discount_factors):
    mtm_notionals = base_notional * (fx_rates / fx_rates[0])
    fixed_leg = np.sum(mtm_notionals * fixed_rate * periods * discount_factors)
    floating_leg = np.sum(mtm_notionals * floating_rates * periods * discount_factors)
    return floating_leg - fixed_leg