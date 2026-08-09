import streamlit as st

# ---------------------------------------------------------
# TEAM SELECTOR
# ---------------------------------------------------------

def team_selector(teams):
    active_teams = [t for t in teams if t["active"]]
    team_names = [t["team_id"] for t in active_teams]

    selected = st.selectbox("Select your team", team_names)
    return selected


# ---------------------------------------------------------
# PLAYER SELECTOR
# ---------------------------------------------------------

def player_selector(players, team_id):
    team_players = [p for p in players if p["team_id"] == team_id]
    names = [p["player_name"] for p in team_players]

    selected_name = st.selectbox("Select your name", names)
    selected_player = next(p for p in team_players if p["player_name"] == selected_name)

    return selected_player


# ---------------------------------------------------------
# GAME CARD
# ---------------------------------------------------------

def game_card(game, attendance_lookup, player_id):
    st.markdown(f"### {game['date']} — {game['time']} — {game['field']}")
    st.markdown(f"**Opponent:** {game['opponent']}")

    key = (player_id, game["game_id"])
    current_status = attendance_lookup.get(key, "Unknown")

    status = st.radio(
        "Attendance",
        ["Yes", "No", "Maybe"],
        index=["Yes", "No", "Maybe"].index(current_status) if current_status in ["Yes", "No", "Maybe"] else 2,
        horizontal=True,
        key=f"{player_id}_{game['game_id']}"
    )

    return {
        "player_id": player_id,
        "game_id": game["game_id"],
        "status": status
    }


# ---------------------------------------------------------
# SUMMARY BOX
# ---------------------------------------------------------

def attendance_summary(attendance, games, player_id):
    st.markdown("## Your Attendance Summary")

    yes = sum(1 for a in attendance if a["player_id"] == player_id and a["status"] == "Yes")
    no = sum(1 for a in attendance if a["player_id"] == player_id and a["status"] == "No")
    maybe = sum(1 for a in attendance if a["player_id"] == player_id and a["status"] == "Maybe")

    st.write(f"**Yes:** {yes}")
    st.write(f"**No:** {no}")
    st.write(f"**Maybe:** {maybe}")
