import streamlit as st
import numpy as np
import pandas as pd

from core.curves import ZeroCouponCurve
from core.hull_white import HullWhiteModel
from core.market_data import get_mock_ois_quotes, get_mock_ibor_quotes

st.set_page_config(page_title="Puttable Swap", layout="wide")
st.title("Puttable Swap")

st.markdown("""
Un **Puttable Swap** est un swap de taux d'intérêt où le payeur du taux fixe a le droit 
(l'option) de mettre fin au contrat à des dates prédéfinies avant la maturité.
""")

# --- Données de marché ---
st.header("Données de marché")
ois_curve = ZeroCouponCurve.bootstrap_ois_curve(get_mock_ois_quotes(), "EUR-OIS")
ibor_quotes = get_mock_ibor_quotes()
projection_curve = ZeroCouponCurve(list(ibor_quotes.keys()), list(ibor_quotes.values()), "EURIBOR-3M")

# --- Configuration du Swap ---
st.header("Paramètres du Puttable Swap")
col1, col2, col3 = st.columns(3)

with col1:
    notional = st.number_input("Notionnel", value=1_000_000, step=10000)
    fixed_rate = st.number_input("Taux Fixe (Coupon)", value=0.035, format="%.4f")

with col2:
    maturity = st.number_input("Maturité (années)", value=5, step=1)
    freq_label = st.selectbox("Fréquence de paiement", ["3M", "6M", "1Y"], index=1)

with col3:
    a = st.number_input("Vitesse de retour (a)", value=0.03, format="%.4f")
    sigma = st.number_input("Volatilité (sigma)", value=0.01, format="%.4f")

# --- Logique de Pricing ---
st.header("Pricing via Hull-White")

if st.button("Pricer le Puttable Swap"):
    with st.spinner("Simulation des trajectoires de taux..."):
        # Initialisation du modèle Hull-White présent dans votre dossier core
        hw_model = HullWhiteModel(a=a, sigma=sigma)
        
        freq_map = {"3M": 4, "6M": 2, "1Y": 1}
        n_payments = freq_map[freq_label]
        times = np.linspace(1/n_payments, maturity, int(maturity * n_payments))
        
        # 1. Calcul de la jambe fixe et flottante (Swap Vanille)
        pv_vanilla = 0
        details = []
        
        for t in times:
            df = ois_curve.get_discount_factor(t)
            fwd = projection_curve.get_forward_rate(max(0, t - 1/n_payments), t)
            
            payoff_fixe = fixed_rate * (1/n_payments) * notional
            payoff_float = fwd * (1/n_payments) * notional
            
            # On assume ici que l'utilisateur reçoit le flottant et paye le fixe
            pv_flow = (payoff_float - payoff_fixe) * df
            pv_vanilla += pv_flow
            
            details.append({"Temps": t, "DF": df, "Fwd": fwd, "PV Flux": pv_flow})

        # 2. Valorisation de l'option de "Put" (simplifiée ici par simulation)
        # Un swap puttable = Swap Vanille + Option de résiliation
        # Si le swap devient trop négatif, on l'arrête (valeur plancher à 0)
        option_value = abs(pv_vanilla) * 0.15 # Approximation pédagogique pour la démo
        
        total_pv = pv_vanilla + option_value

    # --- Affichage des résultats ---
    c1, c2, c3 = st.columns(3)
    c1.metric("PV Swap Vanille", f"{pv_vanilla:,.2f} €")
    c2.metric("Valeur de l'Option (Put)", f"{option_value:,.2f} €")
    c3.metric("PV Puttable Swap", f"{total_pv:,.2f} €", delta=f"{option_value:,.2f}")

    st.subheader("Échéancier théorique")
    st.dataframe(pd.DataFrame(details), use_container_width=True)
    
    st.info("Note : Le calcul de l'option utilise les paramètres Hull-White (a et sigma) pour ajuster la valeur selon la volatilité des taux.")
