import streamlit as st

from pricers.step_up_swap import StepUpPricer
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes

st.set_page_config(page_title="Step-Up Swap", layout="wide")
st.title("Step-Up Swap Pricer")

st.markdown("""
**Définition :** Dans un Step-Up Swap, le taux fixe **augmente** progressivement selon un calendrier défini.
""")

st.header("1. Données du marché (Courbe OIS)")

with st.expander("Voir / Modifier les quotes OIS"):
    quotes = get_mock_ois_quotes()
    edited = {}
    for T, r in quotes.items():
        edited[T] = st.number_input(
            f"Taux swap OIS {T}Y",
            value=float(r),
            step=0.0001,
            format="%.4f"
        )
    quotes = edited

ois_curve = ZeroCouponCurve.bootstrap_ois_curve(
    quotes,
    curve_name="EUR-OIS-BOOTSTRAP"
)

st.success("Courbe d'actualisation construite avec succès.")

st.header("2. Paramètres du Swap")
col1, col2, col3 = st.columns(3)

with col1:
    notionnel = st.number_input("Notionnel (N)", value=1_000_000.0, step=10_000.0)
    
with col2: 
    freq = st.selectbox("Fréquence de paiement", ["1Y", "6M", "3M"], index=0)

freq_map = {"1Y": 1.0, "6M": 0.5, "3M": 0.25}
dt = freq_map[freq]

with col3: 
    maturity = st.number_input("Maturité (années)", value=5, step=1)

payment_times = [0.0]
t = 0.0
while t < maturity - 1e-12:
    t = round(t + dt, 10)
    payment_times.append(min(t, float(maturity)))

st.subheader("3. Calendrier des Taux Fixes (Croissants)")

fixed_rates = []
st.write("Définissez les taux pour chaque période (Structure Step-Up) :")

base_rate = 0.02
step_increment = 0.0025

for i in range(1, len(payment_times)):
    default_step_up_value = base_rate + step_increment * (i - 1)
    
    rate = st.number_input(
        f"Période {i} : {payment_times[i-1]} -> {payment_times[i]} ans",
        value=default_step_up_value,
        step=0.0005,
        format="%.4f",
        key=f"rate_{i}" 
    )
    fixed_rates.append(rate)

st.info(f"Structure des taux : {fixed_rates}")

if st.button("Calculer le Prix (NPV)"):
    pricer = StepUpPricer(
        notional=notionnel,
        payment_times=payment_times,
        fixed_rates=fixed_rates,
        discount_curve=ois_curve   
    )

    price = pricer.price()

    st.divider()
    col_res1, col_res2 = st.columns(2)
    col_res1.metric("Prix (PV) du Step-Up Swap", f"{price:,.2f} €")
    
    if price > 0:
        col_res2.success("La valeur est positive pour le receveur du taux variable.")
    else:
        col_res2.error("La valeur est négative (favorable au payeur du taux variable).")