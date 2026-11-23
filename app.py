"""Idle Obelisk Miner Tools - Streamlit multipage app.

Run:  streamlit run app.py

Adding a tool: put its logic in calculators/, its page in views/,
then register the page in the navigation below (and in views/home.py).
"""
import streamlit as st

from core.game_json import sidebar_loader
from core.layout import footer

st.set_page_config(page_title="Idle Obelisk Miner Tools", layout="wide")

pages = st.navigation({
    "": [st.Page("views/home.py", title="Home", default=True)],
    "Calculators": [
        st.Page("views/frogger.py", title="Frogger Gem Rate", url_path="frogger"),
    ],
})

st.session_state.game = sidebar_loader()

pages.run()
footer()
