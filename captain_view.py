import streamlit as st

def captain_view(data, captain_player_id):

    players = data["players"]
    games = data["games"]
    attendance = data["attendance"]

    # ---------------------------------------------------------
    # Identify captain's team
    # ---------------------------------------------------------
    captain = next(p for p in players if p["player_id"] == captain_player_id)
    team_id = captain["team_id"]

    # ---------------------------------------------------------
    # Filter players on captain's team
    # ---------------------------------------------------------
    team_players = [p for p in players if p["team_id"] == team_id]

    # ---------------------------------------------------------
    # Filter games for captain's team
    # ---------------------------------------------------------
    team_games = [g for g in games if g["team_id"] == team_id]
    team_game_ids = {g["game_id"] for g in team_games}

    # ---------------------------------------------------------
    # Filter attendance to only this team
    # ---------------------------------------------------------
    team_attendance = [
        a for a in attendance
        if a["game_id"] in team_game_ids
        and a["player_id"] in {p["player_id"] for p in team_players}
    ]

    # ---------------------------------------------------------
    # Captain Tools UI
    # ---------------------------------------------------------
    st.markdown("### Captain Tools")

    # ---------------------------------------------------------
    # Missing Responses
    # ---------------------------------------------------------
    st.markdown("#### Players Missing Responses")

    for p in team_players:
        missing = [
            a for a in team_attendance
            if a["player_id"] == p["player_id"] and a["status"] == ""
        ]

        if missing:
            st.markdown(f"**{p['player_name']}**")
            for m in missing:
                game = next(g for g in team_games if g["game_id"] == m["game_id"])
                st.write(f"{game['date']} {game['time']}")
