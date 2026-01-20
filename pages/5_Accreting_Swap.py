import streamlit as st
import numpy as np
import pandas as pd
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes
from pricers.accreting_swap import AccretingSwapPricer

st.set_page_config(page_title="Accreting Swap", layout="wide")
st.title("Accreting Swap Pricing")

quotes = get_mock_ois_quotes()
ois_curve = ZeroCouponCurve.bootstrap_ois_curve(quotes)

st.sidebar.header("Paramètres")
n0 = st.sidebar.number_input("Notionnel Initial", value=1_000_000.0)
growth = st.sidebar.slider("Croissance (%)", 0.0, 10.0, 2.5)
fixed_r = st.sidebar.number_input("Taux Fixe", value=0.03, format="%.4f")
maturity = st.sidebar.number_input("Maturité (ans)", value=5, step=1)

payment_times = [float(i) for i in range(int(maturity) + 1)]
notionals = [n0 * (1 + growth/100)**i for i in range(int(maturity))]

st.subheader("Calendrier du Notionnel")
st.line_chart(pd.DataFrame(notionals, columns=["Notionnel"]))

if st.button("Calculer la NPV"):
    pricer = AccretingSwapPricer(notionals, payment_times, fixed_r, ois_curve)
    npv = pricer.price()
    st.metric("NPV du Swap", f"{npv:,.2f} EUR")