import streamlit as st
import numpy as np
import pandas as pd
from pricers.mtm_swap import price_mtm_swap

st.set_page_config(page_title="MtM Swap")
st.title("🔄 Mark-to-Market Swap Pricing")

st.sidebar.header("Paramètres du Marché")
base_n = st.sidebar.number_input("Notionnel de base (EUR)", value=1000000)
fx_vol = st.sidebar.slider("Volatilité FX simulée", 0.0, 0.5, 0.2)
fixed_r = st.sidebar.number_input("Taux Fixe", value=0.04)

np.random.seed(42)
steps = 12
fx_rates = 1.1 * np.exp(np.cumsum(np.random.normal(0, fx_vol/np.sqrt(12), steps)))
fx_rates = np.insert(fx_rates, 0, 1.1)

st.subheader("Trajectoire du Taux de Change (EUR/USD)")
st.line_chart(pd.DataFrame(fx_rates, columns=["Taux de Change"]))

mtm_notionals = base_n * (fx_rates / fx_rates[0])

st.subheader("Ajustement du Notionnel Mark-to-Market")
st.area_chart(pd.DataFrame(mtm_notionals, columns=["Notionnel MtM (USD)"]))

if st.button("Calculer la NPV MtM"):
    fx_rates_for_pricing = fx_rates[1:] 
    
    floating_rates = np.full(12, 0.035)
    periods = np.full(12, 1/12)
    
    discount_factors = np.exp(-0.03 * np.arange(13))
    discount_factors_for_pricing = discount_factors[1:]
    
    mtm_notionals_for_pricing = base_n * (fx_rates_for_pricing / fx_rates[0])
    
    npv = price_mtm_swap(base_n, fx_rates_for_pricing, fixed_r, floating_rates, periods, discount_factors_for_pricing)
    st.success(f"La NPV du MtM Swap est de : {npv:,.2f} USD")