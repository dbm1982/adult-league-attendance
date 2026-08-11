import streamlit as st

def segmented_control(player_name, current_status, game_id):
    # Updated valid statuses
    options = ["Yes", "No", "Maybe", "No Response"]

    # Normalize incoming status
    raw = str(current_status).strip().capitalize()
    current_status = raw if raw in options else "No Response"

    # Render segmented control
    selected = st.radio(
        f"{player_name} — {game_id}",
        options,
        index=options.index(current_status),
        horizontal=True
    )

    return selected
