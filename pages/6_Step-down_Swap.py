import streamlit as st

from pricers.step_down_swap import StepDownPricer
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes
from core.utils import year_fraction

st.set_page_config(page_title = "Step-down swap", layout = "wide")
st.title("Step-down swap")

st.header("Données du marché (courbe d'actualisation)")

with st.expander("Voir les quotes OIS"):
    quotes = get_mock_ois_quotes()
    edited = {}
    for T, r in quotes.items():
        edited[T] = st.number_input(
            f"Taux swap OIS {T}Y",
            value = float(r),
            step = 0.0001,
            format = "%.4f"
        )
    quotes = edited

ois_curve = ZeroCouponCurve.bootstrap_ois_curve(
    quotes,
    curve_name="EUR-OIS-BOOTSTRAP"
)

st.success("Courbe OIS construite.")

st.header("Paramètres")
col1, col2, col3 = st.columns(3)

with col1:
    notionnel = st.number_input("Notionnel N", value = 1_000_000.0, step = 10_000.0)
    
with col2 : 
    freq = st.selectbox("Fréquence de paiement", ["1Y", "6M", "3M"], index =0)

freq_map = {"1Y": 1.0, "6M" : 0.5, "3M" : 0.25}
dt = freq_map[freq]

with col3 : 
    maturity = st.number_input("Maturité (années)", value = 5, step = 1)

payment_times = [0.0]
t = 0.0

while t<maturity - 1e-12:
    t = round(t+dt, 10)
    payment_times.append(min(t, float(maturity)))

st.subheader("Calendrier des taux fixes (Step-down)")

fixed_rates = []
for i in range(1, len(payment_times)):
    rate = st.number_input(
        f"Taux fixe période {i} (t = {payment_times[i-1]} -> {payment_times[i]})",
        value=max(0.04-0.005*(i-1), 0.0),
        step = 0.0005,
        format="%.4f"
    )
        
    

    fixed_rates.append(rate)

st.write("Dates de paiement :", payment_times)
st.write("Taux fixes par période :", fixed_rates)



if st.button("Pricer le Step down Swap"):
    pricer = StepDownPricer(
        notional = notionnel,
        payment_times = payment_times,
        fixed_rates = fixed_rates,
        discount_curve=ois_curve   
    )

    price = pricer.price()

    st.metric("Prix (PV) du Step-down swap", f"{price:,.2f}")