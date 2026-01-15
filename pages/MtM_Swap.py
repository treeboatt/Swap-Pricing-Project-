import streamlit as st
import numpy as np
from pricers.mtm_swap import price_mtm_swap

st.set_page_config(page_title="MtM Swap")
st.title("🔄 Mark-to-Market Swap Pricing")

st.info("Ce modèle réajuste le notionnel selon les fluctuations de marché.")

base_n = st.number_input("Notionnel de base", value=1000000)
fx_vol = st.slider("Volatilité FX simulée", 0.0, 0.5, 0.1)
