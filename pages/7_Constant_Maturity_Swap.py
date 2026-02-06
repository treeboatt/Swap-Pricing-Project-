import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pricers.constant_maturity_swap import CMSPricer 

st.set_page_config(page_title="CMS Pricing", layout="wide")

st.title("Constant Maturity Swap (CMS) Pricer")

#INPUTS
col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("Paramètres")
    nominal = st.number_input("Nominal (€)", value=1_000_000, step=100_000)
    maturity = st.number_input("Maturité (Années)", value=5)
    fix_rate = st.number_input("Taux Fixe (K) %", value=3.0) / 100
    cms_tenor = st.selectbox("Maturité Constante", ["CMS 10Y", "CMS 2Y"])

#CALCUL
if st.button("Calculer"):
    # On appelle ton pricer
    pricer = CMSPricer(discount_curve=None, swap_surface=None)
    res = pricer.calculate_price(nominal, fix_rate, maturity, cms_tenor)
    
    #RESULTAT
    with col2:
        st.metric("Prix Total (NPV)", f"{res['price']:,.2f} €")
        st.write(f"Jambe CMS : {res['leg_cms']:,.2f} € | Jambe Fixe : {res['leg_fix']:,.2f} €")
