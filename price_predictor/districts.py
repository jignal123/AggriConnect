# ml_engine/districts.py
# Lat/Lon lookup table for Indian districts
# No user input needed — resolved automatically from district name
import json
import os

with open(
    os.path.join(
        os.path.dirname(__file__), "..", "dataset", "districts_coordinates.json"
    )
) as dist:
    DISTRICT_COORDINATES = json.load(dist)


def get_coords(district_name):
    """
    Returns lat/lon/state for a district name.
    Case-insensitive lookup.
    """
    return DISTRICT_COORDINATES.get(district_name.strip())


def get_all_districts():
    return list(DISTRICT_COORDINATES.keys())


def get_districts_by_state(state_name):
    return {
        k: v
        for k, v in DISTRICT_COORDINATES.items()
        if v["state"].lower() == state_name.lower()
    }
