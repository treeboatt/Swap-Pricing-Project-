import streamlit as st
import numpy as np

from pricers.volatility_swap import VolatilitySwapPricer
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes 

st.set_page_config(page_title = "Volatility Swap", layout = "wide")
st.title("Volatility Swap")

st.header("Données du marché (courbe d'actualisation)")

with st.expander("Voir les quotes OIS"):
    quotes = get_mock_ois_quotes()
    edited = {}
    for T, r in quotes.items():
        edited[T] = st.number_input(
            f"Taux swap OIS {T}Y",
            value = float(r),
            step = 0.0001,
            format = "%.4f"
        )
    quotes = edited

ois_curve = ZeroCouponCurve.bootstrap_ois_curve(quotes, curve_name = "EUR-OIS")
st.success("Courbe OIS construite.")

st.header("Paramètres")
col1, col2, col3 = st.columns(3)

with col1:
    notionnel = st.number_input("Notionnel N", value = 1_000_000.0, step = 10_000.0)
    
with col2 : 
    vol_strike = st.number_input("Volatility strike K_vol (%)", value = 20.0, step = 0.1)

with col3 : 
    maturity = st.number_input("Maturité (années)", value = 1.0, step = 0.25)

freq = st.selectbox(
    "Fréquence d'observation",
    ["Daily", "Weekly", "Monthly"],
    index = 0
)

freq_map = {"Daily":252, "Weekly" : 52, "Monthly" : 12}
nb_obs = int(freq_map[freq] * maturity)

st.write(f"Nombre d'observations : {nb_obs}"
         )


st.header("Pricing")

if st.button("Pricer le Volatility Swap"):
    pricer = VolatilitySwapPricer(
        notional = notionnel,
        vol_strike = vol_strike/100.0,
        maturity=maturity,
        nb_obs= nb_obs,
        discount_curve=ois_curve   
    )

    price, realized_vol = pricer.price()

    st.metric("Volatilité réalisée simulée", f"{100*realized_vol:.2f} %")
    st.metric("Prix (PV) du volatility swap", f"{price:,.2f}")
    st.caption("V1 : volatilité réalisée simulée, pricing sous mesure neutre, pas de convexité")