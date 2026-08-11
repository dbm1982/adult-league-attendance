# ui_components.py

import streamlit as st

def segmented_control(player_token, current_status):
    """
    Render a segmented control for attendance selection.
    Returns the selected status.
    """

    options = ["Yes", "No", "Maybe", "None"]

    # Map None/NR to "None"
    if current_status in ["", "NR", None]:
        current_status = "None"

    selected = st.radio(
        f"Attendance for {player_token}",
        options,
        index=options.index(current_status),
        horizontal=True
    )

    return selected
