import streamlit as st
import sys
import os

from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes

from pricers.asset_swap import AssetSwapPricer

st.set_page_config(page_title="Asset Swap", layout="wide")
st.title("Asset Swap Pricer")

st.markdown("""
**Définition :** L'Asset Swap permet de transformer le risque de taux d'une obligation (Fixe) en risque variable (Euribor + Spread).
L'objectif est de calculer l'**Asset Swap Spread (ASW)** qui reflète le risque crédit de l'émetteur.
""")

st.header("1. Environnement de Marché")
with st.expander("Courbe des taux (OIS / Sans Risque)"):
    quotes = get_mock_ois_quotes()
    ois_curve = ZeroCouponCurve.bootstrap_ois_curve(quotes, curve_name="EUR-OIS")
    st.write("Quotes utilisées :", quotes)

st.header("2. Caractéristiques de l'Obligation")

col1, col2, col3 = st.columns(3)

with col1:
    nominal = st.number_input("Nominal (€)", value=1_000_000.0, step=100_000.0)
    maturity = st.number_input("Maturité (Années)", value=5, step=1)

with col2:
    bond_price_pct = st.number_input("Prix de marché (% du pair)", value=98.50, step=0.1, format="%.2f")
    coupon_rate = st.number_input("Taux Coupon Obligation (%)", value=3.00, step=0.1) / 100.0

with col3:
    freq = st.selectbox("Fréquence des coupons", ["1Y", "6M"], index=0)

if st.button("Calculer l'Asset Swap Spread"):
    
    pricer = AssetSwapPricer(
        nominal=nominal,
        maturity_years=maturity,
        bond_coupon_rate=coupon_rate,
        bond_market_price_pct=bond_price_pct,
        discount_curve=ois_curve,
        payment_frequency=freq
    )
    
    res = pricer.calculate_spread()
    spread_bps = res['spread'] * 10000 

    st.divider()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Prix Obligation", f"{bond_price_pct:.2f} %")
    c2.metric("Upfront (Cash reçu)", f"{res['upfront_payment']:,.2f} €", help="100% - Prix Obligation")
    c3.metric("Asset Swap Spread", f"{spread_bps:.2f} bps", delta_color="normal")
    
    st.success(f"L'investisseur échange son taux fixe de {coupon_rate*100}% contre Euribor + **{spread_bps:.0f} bps**.")
    
    with st.expander("Détails du calcul d'équilibre"):
        st.write("L'équation résolue est :")
        st.latex(r"PV_{Swap} = 100\% - P_{Market}")
        st.write(f"**PV Jambe Fixe (payée par le swap) :** {res['pv_fix_leg']:,.2f} €")
        st.write(f"**PV Jambe Variable (hors spread) :** {res['pv_float_clean']:,.2f} €")
        st.write(f"**Valeur actuelle du Spread :** {(res['spread'] * (res['pv_fix_leg']/coupon_rate/nominal if coupon_rate>0 else 0) * nominal):,.2f} € (approx)")