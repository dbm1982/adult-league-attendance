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
# TOP-OF-PAGE TEAM + PLAYER SELECTORS (NO SIDEBAR)
# ---------------------------------------------------------
st.title("Adult League Attendance")

# Team dropdown
team_list = sorted(players_df["team_id"].unique())
team_id = st.selectbox("Team", team_list)

# Player dropdown filtered by team
team_players = players_df[players_df["team_id"] == team_id]
player_names = team_players["player_name"].tolist()
player_name = st.selectbox("Player", player_names)

# Identify player
player_row = team_players[team_players["player_name"] == player_name].iloc[0]
player_id = player_row["player_id"]
is_captain = bool(player_row["is_captain"])

# ---------------------------------------------------------
# TABS — ORIGINAL LAYOUT RESTORED
# ---------------------------------------------------------
if is_captain:
    tab_player, tab_captain = st.tabs(["Player View", "Captain View"])
else:
    tab_player = st.tabs(["Player View"])[0]

# Player View tab
with tab_player:
    player_view(
        players_df=players_df,
        games_df=games_df,
        attendance_df=st.session_state.attendance_df,
        player_id=player_id,
        commit_changes=commit_attendance_changes,
    )

# Captain View tab (only for captains)
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

# ---------------------------------------------------------
# SAVE BUTTON
# ---------------------------------------------------------
st.markdown("---")
if st.button("Save All Changes"):
    updated = commit_attendance_changes(st.session_state.attendance_df)
    st.session_state.attendance_df = updated
    st.success("Attendance saved successfully!")
