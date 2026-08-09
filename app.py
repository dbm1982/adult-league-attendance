import streamlit as st

from data_loader import load_all_data
from attendance_logic import save_attendance
from ui_components import (
    team_selector,
    player_selector,
    game_card,
    attendance_summary
)

from styles import inject_css
inject_css()

from captain_view import captain_view


# ---------------------------------------------------------
# LOAD DATA ONLY AFTER STREAMLIT INITIALIZES
# ---------------------------------------------------------

def get_league_data():
    if "league_data" not in st.session_state:
        st.session_state.league_data = load_all_data()
    return st.session_state.league_data


# Load data
data = get_league_data()

teams = data["teams"]
players = data["players"]
games = data["games"]
attendance = data["attendance"]
sheet = data["sheet"]


# ---------------------------------------------------------
# ACTIVE TEAM FILTER (supports TRUE, "TRUE", 1, yes)
# ---------------------------------------------------------

def is_active(value):
    return str(value).strip().lower() in ("true", "1", "yes")

active_teams = [
    t for t in teams
    if is_active(t.get("active"))
]


# ---------------------------------------------------------
# ATTENDANCE LOOKUP
# ---------------------------------------------------------

attendance_lookup = {
    (row["player_id"], row["game_id"]): row["status"]
    for row in attendance
}


# ---------------------------------------------------------
# UI — TEAM + PLAYER SELECTION
# ---------------------------------------------------------

st.title("Adult Team Attendance")

# TEAM SELECTOR
if not active_teams:
    st.error("No active teams found.")
    st.stop()

team_id = team_selector(active_teams)

# PLAYER SAFETY CHECK
team_players = [p for p in players if p["team_id"] == team_id]
if not team_players:
    st.error("No players found for this team.")
    st.stop()

# PLAYER SELECTOR
player = player_selector(players, team_id)
player_id = player["player_id"]

st.markdown(f"### Welcome, **{player['player_name']}**")


# ---------------------------------------------------------
# CAPTAIN MODE TOGGLE (RESTORED)
# ---------------------------------------------------------

if player["is_captain"] is True:

    if "captain_mode" not in st.session_state:
        st.session_state.captain_mode = False

    toggle_label = (
        "Switch to Captain View"
        if not st.session_state.captain_mode
        else "Return to Player View"
    )

    if st.button(toggle_label):
        st.session_state.captain_mode = not st.session_state.captain_mode

    if st.session_state.captain_mode:
        st.markdown("## Captain View")
        captain_view(data, player_id)
        st.markdown("---")


# ---------------------------------------------------------
# SHOW GAMES FOR THIS TEAM (PLAYER VIEW)
# ---------------------------------------------------------

team_games = [g for g in games if g["team_id"] == team_id]

updates = []

for game in team_games:
    update = game_card(game, attendance_lookup, player_id)
    updates.append(update)
    st.markdown("---")


# ---------------------------------------------------------
# SAVE BUTTON
# ---------------------------------------------------------

if st.button("Save Attendance"):
    save_attendance(sheet, updates)
    st.success("Attendance saved!")
    st.session_state.league_data = load_all_data()


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

attendance_summary(attendance, games, player_id)
