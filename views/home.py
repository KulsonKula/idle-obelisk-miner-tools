"""Home page - list of tools."""
import streamlit as st

st.title("Idle Obelisk Miner Tools")
st.write("Calculators for Idle Obelisk Miner. Paste your game stats export in the sidebar once - "
         "every tool reads its inputs from it.")

st.subheader("Tools")
with st.container(border=True):
    st.page_link("views/frogger.py", label="Frogger Gem Rate Calculator")
    st.caption("Net gem production per Frogger grade")
