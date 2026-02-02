import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from pricers.variance_swap_pricer import VarianceSwapPricer
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes

st.set_page_config(page_title="Variance Swap Analysis", layout="wide")
st.title("📈 Variance Swap - Volatility Trading")

st.markdown("""
Un **Variance Swap** permet de s'exposer directement à la variance réalisée d'un actif. 
Le payoff est **convexe** : les gains augmentent plus rapidement quand la volatilité monte 
que les pertes ne s'accumulent quand elle baisse.
""")

# --- Données de Marché ---
st.sidebar.header("Paramètres de Marché")
ois_curve = ZeroCouponCurve.bootstrap_ois_curve(get_mock_ois_quotes())

# --- Section 1 : Inputs de l'instrument ---
st.header("1. Configuration du Swap")
c1, c2, c3 = st.columns(3)

with c1:
    n_vega = st.number_input("Notionnel Vega (€ per vol point)", value=50000.0, step=1000.0)
    mat = st.number_input("Maturité (ans)", value=1.0, step=0.5)

with c2:
    k_vol = st.slider("Strike Volatilité (%)", 5.0, 60.0, 20.0) / 100
    r_vol = st.slider("Volatilité Réalisée Attendue (%)", 5.0, 60.0, 25.0) / 100

with c3:
    st.info(f"**Notionnel Variance :** \n\n {n_vega / (2 * k_vol):,.2f} €")

# --- Section 2 : Exécution du Pricing ---
st.divider()
pricer = VarianceSwapPricer(n_vega, k_vol, r_vol, mat, ois_curve)

if st.button("Lancer l'Analyse de Variance"):
    final_pv = pricer.calculate_pv()
    
    # Métriques
    m1, m2, m3 = st.columns(3)
    m1.metric("Variance Strike (K²)", f"{k_vol**2:.4f}")
    m2.metric("Variance Réalisée (σ²)", f"{r_vol**2:.4f}")
    m3.metric("Valeur Actuelle (PV)", f"{final_pv:,.2f} €", delta=f"{(r_vol-k_vol)*100:.2f} pts de vol")

    # --- Section 3 : Graphique de Convexité ---
    st.header("2. Analyse de la Convexité")
    vols = np.linspace(0.01, 0.70, 100)
    pvs = [pricer.calculate_pv(v) for v in vols]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=vols*100, y=pvs, name="Payoff du Swap", line=dict(color='royalblue', width=3)))
    
    # Ajout du point mort (Strike)
    fig.add_vline(x=k_vol*100, line_dash="dash", line_color="red", annotation_text="Strike (Break-even)")
    # Ajout du point actuel
    fig.add_trace(go.Scatter(x=[r_vol*100], y=[final_pv], mode="markers", name="Position Actuelle", marker=dict(size=12, color='orange')))

    fig.update_layout(title="Profil de Profit/Perte vs Volatilité Réalisée", 
                      xaxis_title="Volatilité Réalisée (%)", yaxis_title="PV (€)",
                      template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    # --- Section 4 : Table de Scénarios ---
    st.header("3. Matrice de Stress-Test")
    scenarios = np.array([0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50])
    results = []
    
    for s in scenarios:
        res_pv = pricer.calculate_pv(s)
        results.append({
            "Vol Réalisée (%)": f"{s*100:.1f}%",
            "Variance": f"{s**2:.4f}",
            "Payoff (€)": res_pv,
            "Statut": "Profit" if res_pv > 0 else "Perte"
        })
    
    st.table(pd.DataFrame(results))
    
    st.caption("Note : Le payoff est calculé en utilisant l'actualisation OIS pour la maturité choisie.")
