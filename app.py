import streamlit as st
from zoneinfo import ZoneInfo
import datetime

# ---------------------------------------------------------
# SAFE RERUN HANDLER
# ---------------------------------------------------------
if st.session_state.get("force_rerun", False):
    st.session_state["force_rerun"] = False
    st.experimental_rerun()

# ---------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------
from attendance_logic import (
    load_players_df,
    load_games_df,
    load_attendance_df,
    commit_attendance_changes,
)

from captain_view import captain_view
from player_view import player_view

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
players_df = load_players_df()
games_df = load_games_df()
attendance_df = load_attendance_df()

st.set_page_config(page_title="Adult League Attendance", layout="wide")

st.title("Adult League Attendance")

# Sidebar role/team selection
role = st.sidebar.selectbox("Role", ["Captain", "Player"])
team_id = st.sidebar.text_input("Team ID", "GRAY")

# ---------------------------------------------------------
# ROUTING
# ---------------------------------------------------------
if role == "Captain":
    captain_view(
        players_df=players_df,
        games_df=games_df,
        attendance_df=attendance_df,
        team_id=team_id,
        commit_changes=commit_attendance_changes,
    )
else:
    player_view(
        players_df=players_df,
        games_df=games_df,
        attendance_df=attendance_df,
        team_id=team_id,
        commit_changes=commit_attendance_changes,
    )
