import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from pricers.puttable_swap_pricer import PuttableSwapPricer
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes, get_mock_ibor_quotes

st.set_page_config(page_title="Puttable Swap Pricing", layout="wide")
st.title("Puttable Swap - Évaluation d'Option")

st.markdown("""
Un **Puttable Swap** offre au payeur de taux fixe le droit de résilier le contrat. 
Cette page décompose la valeur entre le swap vanille et la valeur de l'option de sortie.
""")

# Paramètres de Marché 
st.sidebar.header("Market Environment")
ois_curve = ZeroCouponCurve.bootstrap_ois_curve(get_mock_ois_quotes())
ibor_curve = ZeroCouponCurve(list(get_mock_ibor_quotes().keys()), list(get_mock_ibor_quotes().values()))

# Inputs 
st.header("1. Caractéristiques du Swap")
c1, c2, c3 = st.columns(3)

with c1:
    notional = st.number_input("Notionnel (€)", value=1_000_000, step=50000)
    fixed_rate = st.number_input("Taux Fixe", value=0.032, format="%.4f")
with c2:
    maturity = st.slider("Maturité (ans)", 1, 25, 10)
    freq = st.selectbox("Fréquence", ["3M", "6M", "1Y"], index=1)
with c3:
    a = st.number_input("Hull-White 'a' (Mean Reversion)", value=0.03, format="%.3f")
    sigma = st.number_input("Hull-White 'sigma' (Vol)", value=0.015, format="%.3f")

# Exécution du Pricing
st.divider()
pricer = PuttableSwapPricer(notional, maturity, fixed_rate, freq, a, sigma, ois_curve, ibor_curve)

if st.button("Calculer la Valeur du Puttable Swap"):
    pv_v, opt_v, details = pricer.price()
    df_details = pd.DataFrame(details)

    # Métriques principales
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PV Swap Vanille", f"{pv_v:,.2f} €")
    m2.metric("Valeur Optionnelle", f"{opt_v:,.2f} €")
    m3.metric("PV Puttable Swap", f"{(pv_v + opt_v):,.2f} €")
    m4.metric("Option / Notional", f"{(opt_v / notional * 100):.3f} %")

    # Visualisation 
    st.header("2. Analyse Graphique")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Profil des Flux Net (Non actualisés)")
        fig_flux = px.bar(df_details, x="Maturité", y="Flux Net", 
                          title="Flux périodiques estimés", color="Flux Net",
                          color_continuous_scale="RdYlGn")
        st.plotly_chart(fig_flux, use_container_width=True)

    with col_b:
        st.subheader("Actualisation (DF) sur la période")
        fig_df = px.line(df_details, x="Maturité", y="DF", markers=True, 
                         title="Courbe des facteurs d'actualisation")
        st.plotly_chart(fig_df, use_container_width=True)

    # Sensibilité 
    st.header("3. Sensibilité à la Volatilité (Hull-White)")
    vol_range = np.linspace(0.005, 0.05, 15)
    sensi_data = []
    for v in vol_range:
        _, o_v, _ = pricer.price(custom_sigma=v)
        sensi_data.append({"Volatilité": v, "Valeur Option": o_v})
    
    df_sensi = pd.DataFrame(sensi_data)
    fig_sensi = px.area(df_sensi, x="Volatilité", y="Valeur Option", 
                        title="Impact de la volatilité sur la valeur du Put")
    st.plotly_chart(fig_sensi, use_container_width=True)

    # Tableau Détail 
    with st.expander("Voir l'échéancier détaillé"):
        st.table(df_details.style.format({
            "Maturité": "{:.2f}",
            "DF": "{:.4f}",
            "Forward": "{:.4%}",
            "Flux Net": "{:,.2f} €",
            "PV Flux": "{:,.2f} €"
        }))
