import streamlit as st

# Opponent colors from your latest version
OPP_COLORS = {
    "Purple": "#800080",
    "Royal": "#4169E1",
    "Gray": "#808080",
    "Red": "#B22222",
    "Green": "#228B22",
    "Orange": "#FF8C00",
    "Blue": "#1E90FF",
    "Yellow": "#DAA520"
}

def game_card(game, attendance_lookup, player_id):
    opponent = game["opponent"]
    game_id = game["game_id"]
    status = attendance_lookup.get((player_id, game_id), "")

    opp_color = OPP_COLORS.get(opponent, "#333")

    st.markdown(
        f"""
        <div class="game-card">
            <span class="opp-badge" style="background-color:{opp_color};">
                {opponent}
            </span>

            <span class="time-badge">
                {game["date"]} — {game["time"]}
            </span>

            <span class="field-badge">
                Field {game["field"]}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    return {
        "player_id": player_id,
        "game_id": game_id,
        "status": st.radio(
            "Attendance",
            ["Yes", "No", "Maybe"],
            horizontal=True,
            index=["Yes", "No", "Maybe"].index(status) if status in ["Yes", "No", "Maybe"] else 0,
            key=f"att_{player_id}_{game_id}"
        )
    }
