"""Frogger Gem Rate Calculator page."""
import altair as alt
import pandas as pd
import streamlit as st

from calculators.frogger import (DEFAULT_SUIT_INDEX, GRADE_KEY, INPUTS,
                                 compute, inputs_from_json)

game = st.session_state.game
flat, data_id = game["flat"], game["data_id"]

st.title("Frogger Gem Rate Calculator")
st.caption("Paste your game stats export (JSON) in the sidebar - the calculator inputs fill in automatically. "
           "Then enter D20 Charges Refilled manually (Bombs menu → click the D20 bomb).")

STRATEGIES = {
    True: ("Strategy A - on battery bombs",
           "Cherry charges go into battery bombs, which refill further bombs."),
    False: ("Strategy B - on gem bombs",
            "Cherry charges are spent directly on gem bombs."),
}

tab_calc, tab_details = st.tabs(["Calculator", "Details"])

# Layout of the Calculator tab: settings, inputs from JSON, then results
with tab_calc:
    settings_box = st.container()
    json_box = st.container()

with json_box:
    st.subheader("Inputs from JSON")
    st.caption("Filled in from the JSON file. Change a value to override it.")
suit_index = DEFAULT_SUIT_INDEX
auto = inputs_from_json(flat, suit_index)

params = {}

D20_HINT = "You can find this value in the Bombs menu after clicking the D20 bomb."

DISPLAY = {
    "d20_charges": "int",
    "frogger_level": "int",
    "fuel_duration_multi": "2dp",
    "fuel_save_chance": "pct",
    "free_bomb_chance": "pct",
    "cherry_triple_chance": "pct",
    "gem_bomb_chance": "pct",
}


def input_widget(inp):
    value, key = auto[inp["name"]]
    if isinstance(inp["default"], bool):
        v = st.radio(
            "How do you use cherry charges?",
            options=[True, False], index=0 if value else 1,
            format_func=lambda x: STRATEGIES[x][0],
            captions=[STRATEGIES[True][1], STRATEGIES[False][1]],
            help="Not in the JSON - pick the method you use in the game.",
            key=f"frogger_{inp['name']}_{data_id}")
    else:
        kind = DISPLAY.get(inp["name"])
        kwargs = dict(help=f"JSON: {key}" if key else "Not in the JSON - set it manually.",
                      key=f"frogger_{inp['name']}_{data_id}_{suit_index}")
        if inp["name"] == "d20_charges":
            kwargs["help"] = D20_HINT
        if kind == "int":
            v = st.number_input(inp["label"], value=int(round(value)), step=1, format="%d", **kwargs)
            if inp["name"] == "d20_charges":
                st.caption(D20_HINT)
        elif kind == "pct":
            # full-precision value; "format" only affects how it is displayed
            v = st.number_input(f"{inp['label']} (%)", value=float(value) * 100, step=0.1,
                                format="%.2f", **kwargs) / 100
        elif kind == "2dp":
            v = st.number_input(inp["label"], value=float(value), step=0.01,
                                format="%.2f", **kwargs)
        else:
            v = st.number_input(inp["label"], value=float(value), format="%.4f", **kwargs)
    params[inp["name"]] = v


json_inputs = [i for i in INPUTS if i["key"]]
manual_inputs = [i for i in INPUTS if not i["key"]]

with json_box:
    cols = st.columns(3)
    for n, inp in enumerate(json_inputs):
        with cols[n % 3]:
            input_widget(inp)

with settings_box:
    st.subheader("Your settings")
    cols = st.columns(len(manual_inputs))
    for col, inp in zip(cols, manual_inputs):
        with col:
            input_widget(inp)

# ------------------------------------------------------------------ results
RATE = "Gem Net Production Rate (/h)"


def rate_chart(df, my_grade, positive):
    """Rate per grade, with the first gem-positive grade and your grade marked."""
    base = alt.Chart(df).encode(
        x=alt.X("Frogger Grade:Q", scale=alt.Scale(domain=[df["Frogger Grade"].min(), df["Frogger Grade"].max()])),
        y=alt.Y(f"{RATE}:Q", title="Gem net rate (/h)"))
    layers = [
        alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(strokeDash=[4, 4], opacity=0.5).encode(y="y:Q"),
        base.mark_line(),
    ]
    points = []
    if len(positive):
        r = positive.iloc[0]
        points.append({"Frogger Grade": r["Frogger Grade"], RATE: r[RATE], "point": "Min. gem-positive grade"})
    if my_grade is not None and my_grade in df["Frogger Grade"].values:
        r = df[df["Frogger Grade"] == my_grade].iloc[0]
        points.append({"Frogger Grade": my_grade, RATE: r[RATE], "point": "Your grade"})
    if points:
        pts = pd.DataFrame(points)
        pts["label"] = pts.apply(lambda r: f"{r['point']}: {int(r['Frogger Grade'])} ({r[RATE]:.2f}/h)", axis=1)
        enc = alt.Chart(pts).encode(
            x="Frogger Grade:Q", y=f"{RATE}:Q",
            color=alt.Color("point:N", title=None, legend=alt.Legend(orient="top"),
                            scale=alt.Scale(domain=["Min. gem-positive grade", "Your grade"],
                                            range=["#F5A623", "#2ECC71"])),
            tooltip=["label:N"])
        layers.append(enc.mark_point(size=160, filled=True))
    return alt.layer(*layers).properties(height=380)


df = pd.DataFrame(compute(params))
my_grade = flat.get(GRADE_KEY)
my_grade = int(my_grade) if my_grade is not None else None
positive = df[df[RATE] > 0]

with tab_calc:
    st.subheader("Result")
    c1, c2, c3, c4 = st.columns(4)
    if my_grade is not None and my_grade in df["Frogger Grade"].values:
        row = df[df["Frogger Grade"] == my_grade].iloc[0]
        c1.metric("Your Frogger Grade", my_grade)
        c2.metric("Gem Net Production Rate", f"{row[RATE]:.2f} /h")
        c3.metric("Time Between Fires (gem positive)", f"{row['Time Between Fires for Gem Positive']:.2f} s")
    else:
        c1.metric("Your Frogger Grade", "not in JSON")
    c4.metric("First gem-positive grade", int(positive["Frogger Grade"].min()) if len(positive) else "-")

    st.altair_chart(rate_chart(df, my_grade, positive), width="stretch")


def highlight(r):
    return ["background-color: #92D05055; font-weight: bold" if r["Frogger Grade"] == my_grade else ""] * len(r)


with tab_details:
    st.subheader("All grades")
    st.dataframe(
        df.style.apply(highlight, axis=1).format(precision=3),
        hide_index=True, width="stretch", height=420)

    st.subheader("Values read from the file")
    st.dataframe(pd.DataFrame(
        [{"input": i["label"], "value": auto[i["name"]][0], "JSON key": auto[i["name"]][1] or "- (manual)"}
         for i in INPUTS]), hide_index=True)

    with st.expander("All JSON stats"):
        q = st.text_input("Search key")
        stats = pd.DataFrame({"key": list(flat), "value": [str(v) for v in flat.values()]})
        if q:
            stats = stats[stats["key"].str.contains(q, case=False)]
        st.dataframe(stats, hide_index=True, width="stretch")
