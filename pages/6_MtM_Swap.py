import streamlit as st
import numpy as np
import pandas as pd
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes
from pricers.mtm_swap import MtMSwapPricer

st.set_page_config(page_title="MtM Swap", layout="wide")
st.title("Mark-to-Market Swap Pricing")

quotes = get_mock_ois_quotes()
ois_curve = ZeroCouponCurve.bootstrap_ois_curve(quotes)

st.sidebar.header("Paramètres")
base_n = st.sidebar.number_input("Notionnel de base", value=1_000_000.0)
fx_vol = st.sidebar.slider("Volatilité FX", 0.0, 0.5, 0.2)
fixed_r = st.sidebar.number_input("Taux Fixe", value=0.04, format="%.4f")
maturity = st.sidebar.number_input("Maturité (ans)", value=5, step=1)

np.random.seed(42)
steps = int(maturity)
payment_times = [float(i) for i in range(steps + 1)]
fx_rates = 1.1 * np.exp(np.cumsum(np.random.normal(0, fx_vol/np.sqrt(steps), steps + 1)))
fx_rates[0] = 1.1

st.subheader("Visualisation du risque")
c1, c2 = st.columns(2)
with c1:
    st.line_chart(pd.DataFrame(fx_rates, columns=["Taux de Change"]))
with c2:
    mtm_notionals = base_n * (fx_rates / fx_rates[0])
    st.area_chart(pd.DataFrame(mtm_notionals, columns=["Notionnel MtM"]))

if st.button("Pricer le MtM Swap"):
    pricer = MtMSwapPricer(base_n, fx_rates, payment_times, fixed_r, ois_curve)
    npv = pricer.price()
    st.metric("NPV du MtM Swap", f"{npv:,.2f} EUR")