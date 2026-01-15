import streamlit as st
import numpy as np
import pandas as pd
from pricers.accreting_swap import price_accreting_swap

st.set_page_config(page_title="Accreting Swap")
st.title("📈 Accreting Swap Pricing")

st.sidebar.header("Paramètres")
n0 = st.sidebar.number_input("Notionnel Initial", value=1000000)
growth = st.sidebar.slider("Croissance périodique (%)", 0.0, 10.0, 2.5)
fixed_r = st.sidebar.number_input("Taux Fixe", value=0.03)

steps = 10
notionals = np.array([n0 * (1 + growth/100)**i for i in range(steps)])

st.subheader("Évolution du Notionnel (Accretion)")
st.line_chart(pd.DataFrame(notionals, columns=["Notionnel"]))

if st.button("Calculer la NPV"):
    st.success("NPV calculée avec succès")