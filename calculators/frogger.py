"""Frogger Gem Rate Calculator - calculation logic.

Command line usage (from the project root):
    python -m calculators.frogger test_data.json   # prints the gem rate table
"""
from __future__ import annotations

from core.game_json import flatten_stats

GRADES = range(0, 46)

INPUTS = [
    dict(name="fuel_duration_multi", label="Fuel Duration Multiplier",
         key="coal_fuel_duration_multi", scale=1, default=1.0),
    dict(name="fuel_save_chance", label="Fuel Save Chance",
         key="coal_fuel_save_chance", scale=0.01, default=0.01),
    dict(name="free_bomb_chance", label="Free Bomb Chance",
         key="bomb_free_chance", scale=0.01, default=0.01),
    dict(name="d20_charges", label="D20 Charges Refilled",
         key=None, scale=1, default=1),
    dict(name="cherry_triple_chance", label="Cherry Bomb Triple Chance",
         key="bomb_cherry3x_chance", scale=0.01, default=0.01),
    # 3% + 0.10% per level of the 7th entry of pet_quest_array
    dict(name="gem_bomb_chance", label="Gem Bomb Gem Chance",
         key="pet_quest_array[6]", scale=0.001, offset=0.03, default=0.01),
    dict(name="cherry_battery", label="Cherry Battery?",
         key=None, scale=1, default=True),
    dict(name="frogger_level", label="Frogger Level",
         key="drones_suit_level_array[{suit_index}]", scale=1, default=1),
    dict(name="game_speed", label="Game Speed",
         key="game_speed_multi", scale=1, default=1.0),
]
DEFAULT_SUIT_INDEX = 5
GRADE_KEY = "frogger_fuel_grade"


def inputs_from_json(flat: dict, suit_index: int = DEFAULT_SUIT_INDEX) -> dict:
    """Returns {name: (value, source key)} for the calculator inputs."""
    out = {}
    for inp in INPUTS:
        key = inp["key"].format(suit_index=suit_index) if inp["key"] else None
        if key and flat.get(key) is not None:
            out[inp["name"]] = (float(flat[key]) * inp["scale"] + inp.get("offset", 0), key)
        else:
            out[inp["name"]] = (inp["default"], None)
    return out


# -------------------------------------------------------------------- calculation
FUEL_COST = 5
BOMB_KINDS = 13


def _geometric(p: float) -> float:
    return 1 / (1 - p)


def _gems_per_trigger(p: dict) -> float:
    repeat = _geometric(p["free_bomb_chance"])
    battery = 2 / BOMB_KINDS * repeat
    d20 = p["d20_charges"] / (20 * BOMB_KINDS) * repeat
    cherry = (1 + 2 * p["cherry_triple_chance"]) * repeat
    gem = p["gem_bomb_chance"] * repeat

    amplification = (1 + battery) * (1 + d20)
    # Strategy A
    if p["cherry_battery"]:
        loop_gain = battery * ((1 + d20) * (1 + cherry) - 1)
        return gem * amplification / (1 - loop_gain)
    # Strategy B
    return gem * amplification * (1 + cherry) / (1 - battery * d20)


def _bombs_per_fire(grade: int) -> float:
    """Mean bomb count: grade + 5, growing at half rate once it passes 10."""
    return grade + 5 - max(0, grade - 5) / 2


def compute(p: dict) -> list[dict]:
    per_trigger = _gems_per_trigger(p)
    fire_interval = 30 - 1.5 * p["frogger_level"]
    fires_per_hour = 3600 * p["game_speed"] / fire_interval
    fuel_bonus = p["fuel_duration_multi"] * _geometric(p["fuel_save_chance"])

    rows = []
    for g in GRADES:
        gems = per_trigger * _bombs_per_fire(g) / BOMB_KINDS
        fuel_time = 9 * (20 + g) * fuel_bonus
        fuel_per_hour = 3600 * p["game_speed"] / fuel_time
        rows.append({
            "Frogger Grade": g,
            "Avg Gems per Fire": gems,
            "Required Fires per Fuel": FUEL_COST / gems,
            "Fuel Duration": fuel_time,
            "Time Between Fires for Gem Positive": fuel_time * gems / FUEL_COST,
            "Gem Net Production Rate (/h)": gems * fires_per_hour - FUEL_COST * fuel_per_hour,
        })
    return rows


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    if len(sys.argv) >= 2:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        params = {k: v for k, (v, _) in inputs_from_json(flatten_stats(data)).items()}
        for row in compute(params):
            print(f"grade {row['Frogger Grade']:>2}: "
                  f"{row['Gem Net Production Rate (/h)']:10.2f} gems/h")
    else:
        print(__doc__)
