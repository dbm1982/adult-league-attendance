import streamlit as st
from attendance_logic import (
    load_players_df,
    load_games_df,
    load_attendance_df,
    load_teams_df,
    commit_attendance_changes,
)
from player_view import player_view
from captain_view import captain_view

st.set_page_config(page_title="Adult League Attendance", layout="wide")

players_df = load_players_df()
games_df = load_games_df()
attendance_df = load_attendance_df()
teams_df = load_teams_df()

if "attendance_df" not in st.session_state:
    st.session_state.attendance_df = attendance_df.copy()

st.title("Adult League Attendance")

# ACTIVE TEAMS ONLY
active_team_ids = sorted(
    teams_df[teams_df["active"] == True]["team_id"].unique()
)

team_id = st.selectbox("Team", active_team_ids)

team_players = players_df[players_df["team_id"] == team_id]
player_names = team_players["player_name"].tolist()
player_name = st.selectbox("Player", player_names)

player_row = team_players[team_players["player_name"] == player_name].iloc[0]
player_id = player_row["player_id"]
is_captain = bool(player_row["is_captain"])

# TABS
if is_captain:
    tab_player, tab_captain = st.tabs(["Player View", "Captain View"])
else:
    tab_player = st.tabs(["Player View"])[0]

with tab_player:
    player_view(
        players_df=players_df,
        games_df=games_df,
        attendance_df=st.session_state.attendance_df,
        player_id=player_id,
        commit_changes=commit_attendance_changes,
    )

if is_captain:
    with tab_captain:
        captain_view(
            data={
                "players": players_df.to_dict("records"),
                "games": games_df,
                "attendance": st.session_state.attendance_df.to_dict("records"),
            },
            current_player_id=player_id,
            team_id=team_id,
        )

st.markdown("---")
if st.button("Save All Changes"):
    updated = commit_attendance_changes(st.session_state.attendance_df)
    st.session_state.attendance_df = updated
    st.success("Attendance saved successfully!")
