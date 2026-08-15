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

if "pending_updates" not in st.session_state:
    st.session_state.pending_updates = {}

st.title("Adult League Attendance")

active_team_ids = sorted(
    teams_df[teams_df["active"] == True]["team_id"].unique()
)

if not active_team_ids:
    st.warning("No active teams found in Teams sheet.")
    st.stop()

team_id = st.selectbox("Team", active_team_ids)

team_players = players_df[
    (players_df["team_id"] == team_id)
    & (players_df["team_id"].ne(""))
    & (~players_df["team_id"].str.contains("Inactive", case=False))
    & (~players_df["team_id"].str.contains("Floaters", case=False))
]

player_names = team_players["player_name"].tolist()
player_name = st.selectbox("Player", player_names)

if team_players.empty or not player_names:
    st.warning(f"No players found for team '{team_id}'.")
    st.stop()

player_row = team_players[
    team_players["player_name"].astype(str).str.strip().str.lower()
    == str(player_name).strip().lower()
]

if player_row.empty:
    st.error("Selected player not found in Players sheet.")
    st.stop()

player_row = player_row.iloc[0]
player_id = player_row["player_id"]
is_captain = bool(player_row["is_captain"])

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
            players_df=players_df,
            games_df=games_df,
            attendance_df=st.session_state.attendance_df,
            team_id=team_id,
            commit_changes=commit_attendance_changes,
        )
