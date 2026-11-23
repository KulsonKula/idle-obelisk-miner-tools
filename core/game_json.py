"""Game stats export (JSON) - parsing and the shared sidebar loader."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta


def flatten_stats(data: dict) -> dict:
    """Flattens the game JSON to {key: value}; arrays -> key[i]."""
    stats = data.get("stats", data)
    flat = {"version": data.get("version"), "time": data.get("time")}
    for k, v in stats.items():
        if isinstance(v, list):
            for i, x in enumerate(v):
                flat[f"{k}[{i}]"] = x
        else:
            flat[k] = v
    return flat


def export_time(flat: dict) -> str:
    """Export timestamp (stored as days since 1899-12-30) as text, or ''."""
    t = flat.get("time")
    if not isinstance(t, (int, float)):
        return ""
    return (datetime(1899, 12, 30) + timedelta(days=t)).strftime("%Y-%m-%d %H:%M")


def sidebar_loader() -> dict:
    """Renders the JSON paste box in the sidebar and returns the loaded game data.

    Returned dict:
        data    - parsed JSON ({} when nothing / invalid is pasted)
        flat    - flatten_stats(data)
        data_id - changes when the JSON changes or "Restore" is clicked; pages use it
                  in widget keys so their inputs refill from the new data
    """
    import streamlit as st

    pasted = st.sidebar.text_area("Paste your game stats JSON here", height=250, key="game_json",
                                  placeholder='{"version": "...", "stats": {...}}')
    raw = pasted.strip().encode("utf-8")
    data = {}
    if raw:
        try:
            data = json.loads(raw.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            st.sidebar.error(f"Could not read the pasted JSON: {e}")

    st.session_state.setdefault("reset_n", 0)
    if st.sidebar.button("↺ Restore values from JSON"):
        st.session_state.reset_n += 1

    flat = flatten_stats(data)
    if data:
        st.sidebar.success("JSON loaded")
        st.sidebar.write(f"Game version: **{flat.get('version') or '-'}**  \n"
                         f"Exported: **{export_time(flat) or '-'}**")

    return {
        "data": data,
        "flat": flat,
        "data_id": f"{hashlib.md5(raw).hexdigest()[:10]}_{st.session_state.reset_n}",
    }
