import streamlit as st
import numpy as np
import pandas as pd

from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes, get_mock_ibor_quotes

st.set_page_config(page_title="Quanto Swap", layout="wide")
st.title("Quanto Swap")

# --- Initialisation des courbes ---
ois_quotes = get_mock_ois_quotes()
ibor_quotes = get_mock_ibor_quotes()
discount_curve = ZeroCouponCurve.bootstrap_ois_curve(ois_quotes, "EUR-OIS")
projection_curve = ZeroCouponCurve(list(ibor_quotes.keys()), list(ibor_quotes.values()), "USD-LIBOR")

# --- Paramètres de saisie ---
st.header("Paramètres du Swap")
col1, col2 = st.columns(2)

with col1:
    notional = st.number_input("Notionnel (Domestique)", value=1_000_000, step=10000)
    rate_vol = st.number_input("Volatilité Taux Étranger", value=0.01, format="%.4f")
    fx_vol = st.number_input("Volatilité FX", value=0.10, format="%.4f")

with col2:
    correlation = st.slider("Corrélation (Taux vs FX)", -1.0, 1.0, 0.3)
    maturity = st.number_input("Maturité (années)", value=5, step=1)
    freq_label = st.selectbox("Fréquence", ["1M", "3M", "6M", "1Y"], index=1)

freq_map = {"1M": 12, "3M": 4, "6M": 2, "1Y": 1}
n_payments = freq_map[freq_label]

# --- Calcul du Pricing ---
if st.button("Calculer la PV"):
    times = np.linspace(1/n_payments, maturity, int(maturity * n_payments))
    total_pv = 0
    details = []
    
    for t in times:
        df = discount_curve.get_discount_factor(t)
        fwd_rate = projection_curve.get_forward_rate(max(0, t - 1/n_payments), t)
        
        # Ajustement de convexité Quanto : rho * sigma_r * sigma_fx * t
        convexity_adj = correlation * rate_vol * fx_vol * t
        adjusted_rate = fwd_rate + convexity_adj
        
        cash_flow = notional * adjusted_rate * (1/n_payments)
        pv_flow = cash_flow * df
        total_pv += pv_flow
        
        details.append({
            "Maturité": round(t, 2),
            "Fwd Rate": fwd_rate,
            "Taux Quanto": adjusted_rate,
            "PV Flux": pv_flow
        })

    st.metric("Valeur Actuelle (PV)", f"{total_pv:,.2f} €")
    
    with st.expander("Détail des flux"):
        st.table(pd.DataFrame(details))
