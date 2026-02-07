import streamlit as st

from pricers.constant_notional_swap import ConstantNotionalSwapPricer
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes, get_mock_ibor_quotes

st.set_page_config(page_title="Constant Notional Swap", layout="wide")
st.title("Constant Notional Swap")

################################
# Courbe OIS (discounting)
################################
st.header("Données de marché – Courbe OIS (discounting)")

with st.expander("Quotes OIS"):
    ois_quotes = get_mock_ois_quotes()
    edited_ois = {}

    for T, r in ois_quotes.items():
        edited_ois[T] = st.number_input(
            f"OIS {T}Y",
            value=float(r),
            step=0.0001,
            format="%.4f"
        )

ois_curve = ZeroCouponCurve.bootstrap_ois_curve(
    edited_ois,
    curve_name="EUR-OIS"
)

st.success("Courbe OIS construite.")

################################
# Courbe IBOR (projection)
################################
st.header("Données de marché – Courbe IBOR (projection)")

with st.expander("Zéros IBOR (proxy)"):
    ibor_quotes = get_mock_ibor_quotes()
    ibor_times = []
    ibor_rates = []

    for T, r in ibor_quotes.items():
        ibor_times.append(T)
        ibor_rates.append(
            st.number_input(
                f"IBOR {T}Y",
                value=float(r),
                step=0.0001,
                format="%.4f"
            )
        )

projection_curve = ZeroCouponCurve(
    ibor_times,
    ibor_rates,
    curve_name="EUR-IBOR-3M"
)

st.success("Courbe IBOR construite.")

################################
# Paramètres du swap
################################
st.header("Paramètres du Constant Notional Swap")

col1, col2, col3 = st.columns(3)

with col1:
    notional = st.number_input(
        "Notionnel",
        value=1_000.0,
        step=10_000.0
    )

with col2:
    maturity = st.number_input(
        "Maturité (années)",
        value=5.0,
        step=1.0
    )

with col3:
    payment_freq = st.number_input(
        "Fréquence de paiement",
        value=4,
        step=1
    )

col1, col2, col3 = st.columns(3)

with col1:
    fixed_rate = st.number_input(
        "Taux fixe K",
        value=0.03,
        step=0.001,
        format="%.4f"
    )

################################
# Pricing
################################
st.header("Pricing")

if st.button("Pricer le Constant Notional Swap"):

    pricer = ConstantNotionalSwapPricer(
        notional=notional,
        maturity=maturity,
        payment_freq=payment_freq,
        fixed_rate=fixed_rate,
        discount_curve=ois_curve,
        projection_curve=projection_curve
    )

    pv = pricer.price_constant_notional()

    st.metric("Valeur actuelle (PV)", f"{pv:,.2f}")
    st.caption(
        "Pricing d’un swap fixe contre flottant à notionnel constant, "
        "projection via la courbe IBOR et actualisation via la courbe OIS."
    )
