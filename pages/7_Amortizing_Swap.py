import streamlit as st
import numpy as np
import pandas as pd

from pricers.amortizing_swap import AmortizingSwapPricer
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes

st.set_page_config(page_title="Amortizing Swap", layout="wide")
st.title("Amortizing Swap")

st.markdown("""
Un **Amortizing Swap** est un swap où le notionnel décroît selon un calendrier prédéfini.
Utile pour couvrir des prêts/emprunts en remboursement progressif.
""")

# Courbe OIS
st.header("Données de marché (courbe d'actualisation OIS)")

with st.expander("Voir les quotes OIS (en dur)"):
    quotes = get_mock_ois_quotes()

    edited = {}
    for T, r in quotes.items():
        edited[T] = st.number_input(
            f"Taux swap OIS {T}Y", 
            value=float(r), 
            step=0.0001, 
            format="%.4f",
            key=f"ois_{T}"
        )
    quotes = edited

ois_curve = ZeroCouponCurve.bootstrap_ois_curve(quotes, curve_name="EUR-OIS-BOOTSTRAP")
st.success("Courbe OIS construite.")

# Paramètres du swap 
st.header("Paramètres du swap")

col1, col2, col3 = st.columns(3)

with col1:
    notional_initial = st.number_input("Notionnel initial", value=1_000.0, step=100.0, format="%.2f")
with col2:
    fixed_rate = st.number_input("Taux fixe (K)", value=0.04, step=0.0005, format="%.4f")
with col3:
    maturity_years = st.number_input("Maturité (années)", value=5, step=1)

freq = st.selectbox("Fréquence de paiement", ["1Y", "6M", "3M"], index=1)

# Construction du calendrier de paiement
freq_map = {"1Y": 1.0, "6M": 0.5, "3M": 0.25}
dt = freq_map[freq]

payment_times = [0.0]
t = 0.0
while t < maturity_years - 1e-12:
    t = round(t + dt, 10)
    payment_times.append(min(t, float(maturity_years)))

# Calendrier d'amortissement 
st.subheader("Calendrier d'amortissement du notionnel")

amort_type = st.radio(
    "Type d'amortissement",
    ["Linéaire", "Dégression", "Personnalisé"],
    horizontal=True
)

notional_schedule = []

if amort_type == "Linéaire":
    # Remboursement linéaire: notionnel décroît linéairement à chaque période
    n_periods = len(payment_times) - 1
    # Le notionnel de la période i (au DÉBUT de la période) décroît linéairement
    notional_schedule = [notional_initial * (n_periods - i) / n_periods for i in range(n_periods)]

elif amort_type == "Dégression":
    # Remboursement plus rapide au début (ex: pour refinance)
    # Le notionnel décroît de manière exponentielle
    n_periods = len(payment_times) - 1
    # Appliquer une courbe dégressive: le notionnel décroît plus vite au début
    # Exposant > 1 = dégression plus rapide, exposant < 1 = dégression plus lente
    notional_schedule = [
        notional_initial * ((n_periods - i) / n_periods) ** 1.5 
        for i in range(n_periods)
    ]

else:  # Personnalisé
    st.write("Entrez le notionnel pour chaque période:")
    notional_schedule = []
    cols = st.columns(min(4, len(payment_times) - 1))
    
    for i in range(len(payment_times) - 1):
        with cols[i % 4]:
            n = st.number_input(
                f"Période {i+1}",
                value=float(notional_initial / (len(payment_times) - 1)),
                step=10.0,
                format="%.2f",
                key=f"notional_{i}"
            )
            notional_schedule.append(n)

# Afficher le calendrier
schedule_df = pd.DataFrame({
    "Période": range(1, len(payment_times)),
    "Début (Y)": payment_times[:-1],
    "Fin (Y)": payment_times[1:],
    "Notionnel": notional_schedule
})

st.dataframe(schedule_df, use_container_width=True)

# Pricing 
st.header("Pricing")

if st.button("Pricer l'Amortizing Swap", type="primary"):
    try:
        pricer = AmortizingSwapPricer(
            notional_schedule=notional_schedule,
            fixed_rate=fixed_rate,
            payment_times=payment_times,
            discount_curve=ois_curve
        )
        
        price = pricer.price()
        fair_rate = pricer.calculate_fair_swap_rate()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Prix (PV)", f"{price:,.2f}")
        
        with col2:
            st.metric("Taux fixe saisi", f"{fixed_rate*100:.3f}%")
        
        with col3:
            st.metric("Fair Swap Rate", f"{fair_rate*100:.3f}%")
            st.caption("Taux d'équilibre (PV=0)")
        
        # Afficher si le swap est avantageux
        if abs(price) < 1:
            st.success("Swap quasi-équilibré")
        elif price > 0:
            st.info(f"Swap avantageux pour le payeur fixe (+{price:,.2f})")
        
        # Détail des flux
        st.subheader("Détail des flux")
        summary = pricer.get_schedule_summary()
        summary_df = pd.DataFrame(summary)
        st.dataframe(summary_df, use_container_width=True)
        
        st.caption("V2 : pricer amortizing avec calcul du fair swap rate. Notionnel décroît linéairement ou en dégression.")
        
    except Exception as e:
        st.error(f"Erreur lors du pricing: {e}")
