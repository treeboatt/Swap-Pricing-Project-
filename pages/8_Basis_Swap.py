import streamlit as st
import pandas as pd

from pricers.basis_swap import BasisSwapPricer
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes

st.set_page_config(page_title="Basis Swap", layout="wide")
st.title("Basis Swap")

st.markdown("""
Un **Basis Swap** échange deux taux flottants de tenors différents avec un **spread (basis)**.

Exemple: Payer EURIBOR 3M et recevoir EURIBOR 6M + spread.

Le basis spread compense la différence de terme et la courbe de taux.
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

#Paramètres du swap 
st.header("Paramètres du swap")

col1, col2, col3 = st.columns(3)

with col1:
    notional = st.number_input("Notionnel", value=1_000.0, step=100.0, format="%.2f")
with col2:
    basis_spread = st.number_input("Basis Spread (%)", value=0.10, step=0.01, format="%.3f") / 100.0
with col3:
    maturity_years = st.number_input("Maturité (années)", value=5, step=1)

# Tenors des deux jambes
st.subheader("Tenors des jambes flottantes")

col1, col2 = st.columns(2)

with col1:
    tenor_1_str = st.selectbox("Jambe 1 (payée)", ["1M", "3M", "6M", "1Y"], index=1, key="tenor1")
with col2:
    tenor_2_str = st.selectbox("Jambe 2 (reçue)", ["1M", "3M", "6M", "1Y"], index=2, key="tenor2")

# Convertir les tenors en années
tenor_map = {"1M": 1/12, "3M": 0.25, "6M": 0.5, "1Y": 1.0}
tenor_1 = tenor_map[tenor_1_str]
tenor_2 = tenor_map[tenor_2_str]

# Déterminer la fréquence de paiement: s'aligner sur le teneur le plus court
min_tenor = min(tenor_1, tenor_2)
if min_tenor <= 1/12:  # 1M ou moins
    freq = "1M"
elif min_tenor <= 0.25:  # 3M ou moins
    freq = "3M"
elif min_tenor <= 0.5:  # 6M ou moins
    freq = "6M"
else:
    freq = "1Y"

st.info(f"**Note:** Fréquence de paiement alignée sur le teneur le plus court ({tenor_1_str.lower()} vs {tenor_2_str.lower()}) = **{freq}**")

freq_map = {"1Y": 1.0, "6M": 0.5, "3M": 0.25}
dt = freq_map[freq]

# Construction du calendrier de paiement
payment_times = [0.0]
t = 0.0
while t < maturity_years - 1e-12:
    t = round(t + dt, 10)
    payment_times.append(min(t, float(maturity_years)))

st.info(f"**Jambe 1:** Payer EURIBOR {tenor_1_str}")
st.info(f"**Jambe 2:** Recevoir EURIBOR {tenor_2_str} + {basis_spread*100:.3f}%")

# Pricing
st.header("Pricing")

if st.button("Pricer le Basis Swap", type="primary"):
    try:
        pricer = BasisSwapPricer(
            notional=notional,
            basis_spread=basis_spread,
            payment_times=payment_times,
            discount_curve=ois_curve,
            tenor_1=tenor_1,
            tenor_2=tenor_2
        )
        
        price = pricer.price()
        fair_spread = pricer.calculate_fair_basis_spread()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Prix (PV)", f"{price:,.2f}")
        
        with col2:
            st.metric("Spread saisi", f"{basis_spread*100:.3f}%")
        
        with col3:
            st.metric("Fair Basis Spread", f"{fair_spread*100:.3f}%")
            st.caption("Spread d'équilibre (PV=0)")
        
        # Détail des flux
        st.subheader("Détail des flux")
        summary = pricer.get_schedule_summary()
        summary_df = pd.DataFrame(summary)
        st.dataframe(summary_df, use_container_width=True)
        
        st.caption(f"V1 : Basis Swap simple. Tenors: {tenor_1_str} vs {tenor_2_str}. Spread d'équilibre calculé.")
        
    except Exception as e:
        st.error(f"Erreur lors du pricing: {e}")
