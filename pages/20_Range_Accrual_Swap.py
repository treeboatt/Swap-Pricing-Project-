import streamlit as st

from core.hull_white import HullWhiteModel
from pricers.range_accrual_swap import RangeAccrualSwapPricer
from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes, get_mock_ibor_quotes

st.set_page_config(page_title="Range Accrual Swap", layout="wide")
st.title("Range Accrual Swap")

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
st.header("Paramètres du Range Accrual Swap")

col1, col2, col3 = st.columns(3)

with col1:
    notional = st.number_input("Notionnel", value=1_000.0, step=10.0)

with col2:
    maturity = st.number_input("Maturité (années)", value=5.0, step=1.0)

with col3:
    payment_freq = st.selectbox("Fréquence de paiement", [1, 2, 4], index=2)

col1, col2, col3 = st.columns(3)

with col1:
    coupon = st.number_input("Coupon annualisé", value=0.05, step=0.001, format="%.4f")

with col2:
    lower_bound = st.number_input("Borne basse", value=0.02, step=0.001, format="%.4f")

with col3:
    upper_bound = st.number_input("Borne haute", value=0.04, step=0.001, format="%.4f")

################################
# Paramètres Hull–White
################################
st.header("Modèle de taux – Hull–White (1 facteur)")

col1, col2, col3 = st.columns(3)

with col1:
    a = st.number_input(
        "Vitesse de retour a",
        value=0.03,
        step=0.005,
        format="%.4f"
    )

with col2:
    sigma = st.number_input(
        "Volatilité sigma",
        value=0.01,
        step=0.001,
        format="%.4f"
    )

with col3:
    n_paths = st.number_input(
        "Nombre de scénarios Monte Carlo",
        value=10_000,
        step=1_000
    )


################################
# Pricing
################################
st.header("Pricing")

if st.button("Pricer le Range Accrual Swap"):
    hw_model = HullWhiteModel(
        a=a,
        sigma=sigma
    )

    pricer = RangeAccrualSwapPricer(
    notional=notional,
    maturity=maturity,
    payment_freq=payment_freq,
    coupon=coupon,
    lower_bound=lower_bound,
    upper_bound=upper_bound,
    discount_curve=ois_curve,
    projection_curve=projection_curve,
    hw_model=hw_model,
    n_paths=int(n_paths),
    seed=42
    )


    pv = pricer.price_range_accrual()

    st.metric("Valeur actuelle (PV)", f"{pv:,.2f}")
    st.caption(
        "Pricing basé sur une jambe range accrual, "
        "taux forward IBOR projetés, actualisation OIS."
    )
