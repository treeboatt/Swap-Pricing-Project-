import streamlit as st

from pricers.callable_swap import CallableSwapPricer
from core.hull_white import HullWhiteModel
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes

st.set_page_config(page_title="Callable Swap", layout="wide")
st.title("Callable Swap (V1)")

# courbe OIS
st.header("Données de marché (courbe d'actualisation OIS)")

with st.expander("Voir les quotes OIS (en dur)"):
    quotes = get_mock_ois_quotes()

    # petit éditeur simple
    edited = {}
    for T, r in quotes.items():
        edited[T] = st.number_input(f"Taux swap OIS {T}Y", value=float(r), step=0.0001, format="%.4f")
    quotes = edited

ois_curve = ZeroCouponCurve.bootstrap_ois_curve(quotes, curve_name="EUR-OIS-BOOTSTRAP")
st.success("Courbe OIS construite.")

# Paramètres Hull-White
st.header("Paramètres Hull-White")

col1, col2 = st.columns(2)
with col1:
    a = st.number_input("a (vitesse de retour à la moyenne)", value=0.05, step=0.01, format="%.4f")
with col2:
    sigma = st.number_input("sigma (volatilité du taux court)", value=0.02, step=0.001, format="%.4f")

hw = HullWhiteModel(a=a, sigma=sigma)

# Paramètres du swap
st.header("Paramètres du swap")

col1, col2, col3 = st.columns(3)

with col1:
    notional = st.number_input("Notionnel", value=1_000.0, step=100.0, format="%.2f")
with col2:
    fixed_rate = st.number_input("Taux fixe (K)", value=0.04, step=0.0005, format="%.4f")
with col3:
    maturity_years = st.number_input("Maturité (années)", value=5, step=1)

freq = st.selectbox("Fréquence de paiement", ["1Y", "6M", "3M"], index=0)

freq_map = {"1Y": 1.0, "6M": 0.5, "3M": 0.25}
dt = freq_map[freq]

# construction des dates de paiement
payment_times = [0.0]
t = 0.0
while t < maturity_years - 1e-12:
    t = round(t + dt, 10)
    payment_times.append(min(t, float(maturity_years)))

# call dates 
st.subheader("Call schedule")
call_from = st.number_input("Première date de call (années)", value=1.0, step=dt, format="%.4f")
call_times = [x for x in payment_times[1:-1] if x >= call_from]

st.write("Dates de paiement :", payment_times)
st.write("Dates de call :", call_times if call_times else "Aucune")

# Pricing
st.header("Pricing")

if st.button("Pricer le Callable Swap"):
    pricer = CallableSwapPricer(
        notional=notional,
        fixed_rate=fixed_rate,
        payment_times=payment_times,
        call_times=call_times,
        discount_curve=ois_curve,
        hw_model=hw
    )

    price = pricer.price()
    st.metric("Prix (PV) du Callable Swap", f"{price:,.2f}")
    st.caption("V1 : arbre HW simplifié, forward basé sur courbe OIS, call exercé si continuation > 0 (payeur fixe).")
