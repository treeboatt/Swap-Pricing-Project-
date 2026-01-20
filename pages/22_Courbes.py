import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from core.curves import ZeroCouponCurve
from core.market_data import get_mock_ois_quotes

st.set_page_config(page_title="Courbe sans risque (OIS)", layout="wide")
st.title("Courbe sans risque – OIS")

st.markdown(
"""
Cette page illustre la **construction de la courbe sans risque**  
à partir des **taux fixes des swaps OIS**.
"""
)

# ==============================
# Quotes OIS
# ==============================
st.header("Quotes de marché – Swaps OIS")

ois_quotes = get_mock_ois_quotes()
edited_ois = {}

cols = st.columns(len(ois_quotes))
for col, (T, r) in zip(cols, ois_quotes.items()):
    with col:
        edited_ois[T] = st.number_input(
            f"OIS {T}Y",
            value=float(r),
            step=0.0001,
            format="%.4f"
        )

# ==============================
# Bootstrap OIS curve
# ==============================
ois_curve = ZeroCouponCurve.bootstrap_ois_curve(
    edited_ois,
    curve_name="EUR-OIS"
)

st.success("Courbe OIS bootstrapée avec succès.")

# ==============================
# Construction des points de courbe
# ==============================
st.header("Courbe sans risque obtenue")

times = np.linspace(0.01, max(edited_ois.keys()), 100)
discount_factors = [ois_curve.get_discount_factor(t) for t in times]
zero_rates = [-np.log(df) / t for df, t in zip(discount_factors, times)]

df_curve = pd.DataFrame({
    "Maturité (années)": times,
    "Facteur d'actualisation P(0,T)": discount_factors,
    "Taux zéro sans risque": zero_rates
})

# ==============================
# Graphiques
# ==============================
col1, col2 = st.columns(2)

with col1:
    st.subheader("Facteurs d'actualisation OIS")
    fig, ax = plt.subplots()
    ax.plot(times, discount_factors)
    ax.set_xlabel("Maturité (années)")
    ax.set_ylabel("P(0,T)")
    ax.grid(True)
    st.pyplot(fig)

with col2:
    st.subheader("Taux zéro sans risque (OIS)")
    fig, ax = plt.subplots()
    ax.plot(times, zero_rates)
    ax.set_xlabel("Maturité (années)")
    ax.set_ylabel("Taux zéro")
    ax.grid(True)
    st.pyplot(fig)

# ==============================
# Table
# ==============================
st.subheader("Valeurs numériques")
st.dataframe(df_curve.style.format({
    "Facteur d'actualisation P(0,T)": "{:.6f}",
    "Taux zéro sans risque": "{:.4%}"
}))
