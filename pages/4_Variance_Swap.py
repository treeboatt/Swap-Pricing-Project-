import streamlit as st
import numpy as np
import pandas as pd

from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes

st.set_page_config(page_title="Variance Swap", layout="wide")
st.title("Variance Swap")

st.markdown("""
Un **Variance Swap** est un produit dérivé dont le payoff dépend de la différence entre 
la **variance réalisée** du taux (ou actif) et un niveau fixé à l'avance (le **Variance Strike**).
""")

# --- Données de marché ---
st.header("Données de marché")
ois_curve = ZeroCouponCurve.bootstrap_ois_curve(get_mock_ois_quotes(), "EUR-OIS")

# --- Paramètres du Swap ---
st.header("Paramètres du Variance Swap")
col1, col2 = st.columns(2)

with col1:
    notional_vega = st.number_input("Notionnel Vega (Montant par point de vol)", value=50000.0, step=1000.0)
    strike_vol = st.number_input("Strike Volatilité (en %, ex: 20 pour 20%)", value=20.0, step=0.5) / 100
    expected_vol = st.number_input("Volatilité réalisée estimée (en %)", value=22.0, step=0.5) / 100

with col2:
    maturity = st.number_input("Maturité (années)", value=1.0, step=0.5)
    # Dans un var swap, on regarde souvent la fréquence d'observation (quotidienne par défaut)
    nb_observations = st.number_input("Nombre d'observations par an", value=252, step=1)

# --- Logique de Pricing ---
st.header("Pricing")

if st.button("Pricer le Variance Swap"):
    # 1. Calcul des strikes et variance
    variance_strike = strike_vol**2
    realized_variance = expected_vol**2
    
    # 2. Facteur d'actualisation pour la maturité
    df = ois_curve.get_discount_factor(maturity)
    
    # 3. Calcul du Payoff (Notionnel Variance * (Var_Réalisée - Var_Strike))
    # Note : Notionnel Variance = Notionnel Vega / (2 * Strike_Vol)
    notional_variance = notional_vega / (2 * strike_vol)
    
    payoff = notional_variance * (realized_variance - variance_strike)
    pv = payoff * df

    # --- Affichage ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Variance Strike", f"{variance_strike:.4f}")
    c2.metric("Variance Réalisée", f"{realized_variance:.4f}")
    c3.metric("Valeur Actuelle (PV)", f"{pv:,.2f} €", delta=f"{payoff:,.2f} à l'échéance")

    # --- Graphique de sensibilité ---
    st.subheader("Sensibilité au changement de Volatilité Réalisée")
    vols = np.linspace(0.05, 0.40, 50)
    payoffs = notional_variance * (vols**2 - variance_strike) * df
    
    chart_data = pd.DataFrame({
        "Volatilité Réalisée (%)": vols * 100,
        "PV du Swap (€)": payoffs
    }).set_index("Volatilité Réalisée (%)")
    
    st.line_chart(chart_data)
    st.info("Le payoff d'un Variance Swap est convexe par rapport à la volatilité, contrairement à un Volatility Swap qui est linéaire.")
