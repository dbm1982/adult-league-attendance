import streamlit as st

# Opponent colors
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

def team_selector(teams):
    team_names = {t["team_id"]: t["team_name"] for t in teams}
    selected = st.selectbox("Select your team", list(team_names.keys()), format_func=lambda x: team_names[x])
    return selected

def player_selector(players, team_id):
    team_players = [p for p in players if p["team_id"] == team_id]
    player_names = {p["player_id"]: p["player_name"] for p in team_players}
    selected = st.selectbox("Select your name", list(player_names.keys()), format_func=lambda x: player_names[x])
    return next(p for p in team_players if p["player_id"] == selected)

def game_card(game, attendance_lookup, player_id):
    opponent = game["opponent"]
    game_id = game["game_id"]
    status = attendance_lookup.get((player_id, game_id), "")

    opp_color = OPP_COLORS.get(opponent, "#333")

    # IMPORTANT: HTML must be left-aligned with NO indentation
    html = f"""
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
"""

    st.markdown(html, unsafe_allow_html=True)

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

def attendance_summary(attendance, games, player_id):
    st.markdown("### Attendance Summary")

    for g in games:
        status = next(
            (a["status"] for a in attendance
             if a["player_id"] == player_id and a["game_id"] == g["game_id"]),
            "No response"
        )
        st.write(f"{g['date']} — {status}")
