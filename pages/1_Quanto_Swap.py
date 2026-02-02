import streamlit as st
import pandas as pd
from pricers.quanto_swap_pricer import QuantoSwapPricer
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes, get_mock_ibor_quotes

st.set_page_config(page_title="Quanto Swap", layout="wide")
st.title("🛡️ Quanto Swap Pricing")

# Initialisation des courbes via le Core
ois_curve = ZeroCouponCurve.bootstrap_ois_curve(get_mock_ois_quotes(), "EUR-OIS")
ibor_curve = ZeroCouponCurve(list(get_mock_ibor_quotes().keys()), list(get_mock_ibor_quotes().values()), "USD-LIBOR")

st.header("Paramètres du Swap")
col1, col2 = st.columns(2)

with col1:
    notional = st.number_input("Notionnel (Devise Domestique)", value=1_000_000)
    rate_vol = st.number_input("Volatilité Taux Étranger", value=0.01, format="%.4f")
    fx_vol = st.number_input("Volatilité FX (Change)", value=0.10, format="%.4f")

with col2:
    correlation = st.slider("Corrélation (Taux vs FX)", -1.0, 1.0, 0.3)
    maturity = st.number_input("Maturité (années)", value=5, step=1)
    freq = st.selectbox("Fréquence", ["3M", "6M", "1Y"], index=0)

if st.button("Pricer le Swap"):
    # Appel du pricer situé dans le dossier /pricers
    pricer = QuantoSwapPricer(
        notional, maturity, freq, rate_vol, fx_vol, correlation, ois_curve, ibor_curve
    )
    
    pv, details = pricer.price()
    
    st.metric("Valeur Actuelle (PV)", f"{pv:,.2f} €")
    
    with st.expander("Détail des flux calculés"):
        st.table(pd.DataFrame(details))
