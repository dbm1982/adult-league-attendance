import streamlit as st
from attendance_logic import (
    load_players_df,
    load_games_df,
    load_attendance_df,
    commit_attendance_changes,
)
from player_view import player_view
from captain_view import captain_view

st.set_page_config(page_title="Adult League Attendance", layout="wide")

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
players_df = load_players_df()
games_df = load_games_df()
attendance_df = load_attendance_df()

# Store attendance in session state for editing
if "attendance_df" not in st.session_state:
    st.session_state.attendance_df = attendance_df.copy()

# ---------------------------------------------------------
# SIDEBAR — ORIGINAL LOGIN FLOW RESTORED
# ---------------------------------------------------------
st.sidebar.header("Access")

# Only show ACTIVE teams
active_teams = sorted(
    players_df[players_df["active_team"] == True]["team_id"].unique()
)

team_id = st.sidebar.selectbox("Team", active_teams)

# Filter players by team
team_players = players_df[players_df["team_id"] == team_id]
player_names = team_players["player_name"].tolist()

player_name = st.sidebar.selectbox("Player", player_names)

# Get player_id and captain flag
player_row = team_players[team_players["player_name"] == player_name].iloc[0]
player_id = player_row["player_id"]
is_captain = bool(player_row["is_captain"])

# ---------------------------------------------------------
# PAGE TITLE
# ---------------------------------------------------------
st.title("Adult League Attendance")

# ---------------------------------------------------------
# ROUTING BASED ON CAPTAIN FLAG
# ---------------------------------------------------------
if is_captain:
    captain_view(
        data={
            "players": players_df.to_dict("records"),
            "games": games_df,
            "attendance": st.session_state.attendance_df.to_dict("records"),
        },
        current_player_id=player_id,
        team_id=team_id,
    )
else:
    player_view(
        players_df=players_df,
        games_df=games_df,
        attendance_df=st.session_state.attendance_df,
        player_id=player_id,
        commit_changes=commit_attendance_changes,
    )

# ---------------------------------------------------------
# SAVE BUTTON
# ---------------------------------------------------------
st.markdown("---")
if st.button("Save All Changes"):
    updated = commit_attendance_changes(st.session_state.attendance_df)
    st.session_state.attendance_df = updated
    st.success("Attendance saved successfully!")
