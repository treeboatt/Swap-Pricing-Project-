import streamlit as st

st.title("Quanto Swap")

st.header("Paramètres du swap")
col1, col2 = st.columns(2)

with col1:
    notionnel_dom = st.number_input("Paramètre 1", value=1_000)
    volatilite_actif = st.number_input("Paramètre 2", value=10.0)
    volatilite_fx = st.number_input("Paramètre 2", value=100.0)

with col2:
    correlation = st.slider("Paramètre 4", -1.0, 1.0, 0.0)
    maturite = st.number_input("Paramètre 5", value=5.0)
    freq = st.selectbox("Paramètre 6", ["1M", "3M", "6M", "1Y"])

st.header("Pricing")
if st.button("Pricer le Quanto Swap"):
    st.warning("Le modèle de pricing n'est pas encore implémenté.")
