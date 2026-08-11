import streamlit as st

def segmented_control(player_token, current_status, game_id):
    options = ["Yes", "No", "Maybe", "None"]

    if current_status in ["", "NR", None]:
        current_status = "None"

    selected = st.radio(
        f"Attendance for {player_token} — {game_id}",
        options,
        index=options.index(current_status),
        horizontal=True,
        key=f"{player_token}_{game_id}_radio"
    )

    return selected
