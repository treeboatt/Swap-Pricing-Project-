import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from pricers.total_return_swap_pricer import TotalReturnSwapPricer
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes, get_mock_ibor_quotes

st.set_page_config(page_title="Total Return Swap Pricing", layout="wide")
st.title("📈 Total Return Swap (TRS) - Analyse")

st.sidebar.header("Configuration Marché")
ois_curve = ZeroCouponCurve.bootstrap_ois_curve(get_mock_ois_quotes())
ibor_curve = ZeroCouponCurve(list(get_mock_ibor_quotes().keys()), list(get_mock_ibor_quotes().values()))

st.header("1. Paramètres de l'Actif et du Financement")
c1, c2, c3 = st.columns(3)

with c1:
    notional = st.number_input("Notionnel (€)", value=1_000_000, step=100000)
    start_price = st.number_input("Prix initial de l'actif", value=100.0)
    current_price = st.number_input("Prix actuel de l'actif", value=105.0)

with c2:
    maturity = st.slider("Maturité (ans)", 1, 10, 2)
    freq = st.selectbox("Fréquence de financement", ["3M", "6M", "1Y"], index=0)
    spread = st.number_input("Spread de financement (bps)", value=50) / 10000

with c3:
    st.info("Le TRS permet de s'exposer à un actif sans le posséder physiquement, en échange d'un paiement d'intérêt.")

st.divider()

pricer = TotalReturnSwapPricer(notional, start_price, current_price, spread, freq, maturity, ois_curve, ibor_curve)

if st.button("Calculer la NPV du TRS"):
    total_pv, asset_leg, funding_leg = pricer.calculate_pv()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("NPV Totale", f"{total_pv:,.2f} €", delta=f"{(asset_leg/notional)*100:.2f}% perf")
    m2.metric("Jambe Actif (Performance)", f"{asset_leg:,.2f} €")
    m3.metric("Jambe Financement (Coût)", f"{-funding_leg:,.2f} €")

    st.header("2. Analyse de Sensibilité au Prix")
    
    prices = np.linspace(start_price * 0.8, start_price * 1.2, 50)
    pvs = [pricer.calculate_pv(p)[0] for p in prices]
    
    fig = px.line(x=prices, y=pvs, labels={'x': 'Prix de l\'actif', 'y': 'NPV (€)'}, title="Profil de P&L du TRS")
    fig.add_vline(x=start_price, line_dash="dash", line_color="red", annotation_text="Prix d'entrée")
    fig.add_hline(y=0, line_color="black", opacity=0.3)
    st.plotly_chart(fig, use_container_width=True)

    st.header("3. Structure du Financement")
    times = np.linspace(1/pricer.n_payments, maturity, int(maturity * pricer.n_payments))
    funding_details = []
    for t in times:
        fwd = ibor_curve.get_forward_rate(max(0, t - 1/pricer.n_payments), t)
        funding_details.append({
            "Période": f"{t:.2f}Y",
            "Taux Forward": f"{fwd:.4%}",
            "Flux Financement": f"{notional * (fwd + spread) * (1/pricer.n_payments):,.2f} €"
        })
    
    st.table(pd.DataFrame(funding_details))

    with st.expander("Explication du Payoff"):
        st.write("""
        Le Payoff du TRS se décompose ainsi :
        - **Asset Leg** : $N \times \\frac{P_{final} - P_{initial}}{P_{initial}}$
        - **Funding Leg** : $\sum N \times (Libor + Spread) \times \Delta t \times DF$
        """)
