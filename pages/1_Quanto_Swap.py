import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from pricers.quanto_swap_pricer import QuantoSwapPricer
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes, get_mock_ibor_quotes

st.set_page_config(page_title="Quanto Swap Pricing", layout="wide")
st.title(" Quanto Swap - Analyse de Risque")

st.markdown("""
Cette interface permet de valoriser un **Quanto Swap** en intégrant l'ajustement de convexité lié à la corrélation 
entre les taux d'intérêt étrangers et le taux de change (FX).
""")

st.sidebar.header("Données de Marché")
ois_curve = ZeroCouponCurve.bootstrap_ois_curve(get_mock_ois_quotes(), "EUR-OIS")
ibor_curve = ZeroCouponCurve(list(get_mock_ibor_quotes().keys()), list(get_mock_ibor_quotes().values()), "USD-LIBOR")
st.sidebar.success("Courbes OIS et IBOR chargées.")

st.header("1. Paramètres du Contrat")
col1, col2, col3 = st.columns(3)

with col1:
    notional = st.number_input("Notionnel (Devise Domestique)", value=1_000_000, step=10000)
    maturity = st.slider("Maturité (années)", 1, 20, 5)
    
with col2:
    rate_vol = st.number_input("Volatilité du Taux Étranger", value=0.012, format="%.4f")
    fx_vol = st.number_input("Volatilité FX", value=0.10, format="%.4f")

with col3:
    correlation = st.slider("Corrélation (Taux vs FX)", -1.0, 1.0, 0.3)
    freq = st.selectbox("Fréquence de paiement", ["3M", "6M", "1Y"], index=0)

st.divider()
pricer = QuantoSwapPricer(notional, maturity, freq, rate_vol, fx_vol, correlation, ois_curve, ibor_curve)

if st.button("Lancer le Pricing"):
    pv, details = pricer.price()
    df_details = pd.DataFrame(details)

    st.header("2. Résultats du Pricing")
    m1, m2, m3 = st.columns(3)
    m1.metric("Valeur Actuelle (PV)", f"{pv:,.2f} €")
    avg_adj = df_details["Ajustement"].mean()
    m2.metric("Ajustement Moyen", f"{avg_adj:.6f}", help="Moyenne des ajustements de convexité sur la durée")
    m3.metric("Impact Corrélation", "Positif" if correlation > 0 else "Négatif")

    st.subheader("Structure Temporelle des Flux Quanto")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_details["Maturité"], y=df_details["Taux Ajusté"], name="Taux Ajusté", mode='lines+markers'))
    fig.add_trace(go.Bar(x=df_details["Maturité"], y=df_details["Fwd Rate"], name="Taux Forward (Base)", opacity=0.5))
    
    fig.update_layout(title="Évolution du Taux Ajusté (Quanto) vs Forward", template="plotly_white", xaxis_title="Temps", yaxis_title="Taux")
    st.plotly_chart(fig, use_container_width=True)

    st.header("3. Analyse de Sensibilité")
    st.write("Impact de la corrélation sur la PV totale :")
    
    corr_range = np.linspace(-1.0, 1.0, 20)
    sensi_pvs = [pricer.price(custom_corr=c)[0] for c in corr_range]
    
    sensi_df = pd.DataFrame({"Corrélation": corr_range, "PV (€)": sensi_pvs})
    fig_sensi = px.line(sensi_df, x="Corrélation", y="PV (€)", markers=True)
    fig_sensi.add_vline(x=correlation, line_dash="dash", line_color="red", annotation_text="Position Actuelle")
    st.plotly_chart(fig_sensi, use_container_width=True)

    with st.expander("Voir le tableau d'amortissement complet"):
        st.dataframe(df_details.style.format({
            "Maturité": "{:.2f}Y",
            "Fwd Rate": "{:.4%}",
            "Ajustement": "{:.6f}",
            "Taux Ajusté": "{:.4%}",
            "PV Flux": "{:,.2f} €"
        }), use_container_width=True)
