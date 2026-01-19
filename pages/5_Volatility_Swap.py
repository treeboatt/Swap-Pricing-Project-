import streamlit as st
import numpy as np

st.title("Volatility Swap")
st.header("Paramètres")
col1, col2 = st.columns(2)

with col1:
    notionnel = st.number_input("Notionnel N", value = 1_000_000)
    vol_strike = st.number_input("Volatility Strike K_vol (%)", value = 20.0)
    nb_obs = st.number_input("Nombre d'observations", value = 200)

with col2 : 
    taux_actualisation = st.number_input("Taux d'actualisation (%)", value = 2.0)
    maturite = st.number_input("Maturité (années)", value = 1.0)
    freq = st.selectbox("Fréquence d'observation", ["Daily", "Weekly", "Monthly"])

st.header("Pricing")

if st.button("Pricer le Volatility Swap"):
    st.warning("Le modèle de pricing n'est pas encore implémenté")