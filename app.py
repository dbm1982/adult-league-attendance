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
# SIDEBAR — RESTORED TO DROPDOWNS
# ---------------------------------------------------------
st.sidebar.header("Access")

# Role dropdown
role = st.sidebar.selectbox("Role", ["Player", "Captain"])

# Team dropdown (from Players sheet)
team_list = sorted(players_df["team_id"].unique())
team_id = st.sidebar.selectbox("Team", team_list)

# Player dropdown (filtered by team)
team_players = players_df[players_df["team_id"] == team_id]
player_names = team_players["player_name"].tolist()

# Player selection only when role = Player
if role == "Player":
    player_name = st.sidebar.selectbox("Player", player_names)
    player_token = team_players.loc[
        team_players["player_name"] == player_name, "player_id"
    ].iloc[0]
else:
    player_token = None

# ---------------------------------------------------------
# PAGE TITLE
# ---------------------------------------------------------
st.title("Adult League Attendance")

# ---------------------------------------------------------
# PLAYER VIEW
# ---------------------------------------------------------
if role == "Player":
    player_view(
        players_df=players_df,
        games_df=games_df,
        attendance_df=st.session_state.attendance_df,
        player_id=player_token,
        commit_changes=commit_attendance_changes,
    )

# ---------------------------------------------------------
# CAPTAIN VIEW
# ---------------------------------------------------------
else:
    captain_view(
        data={
            "players": players_df.to_dict("records"),
            "games": games_df,
            "attendance": st.session_state.attendance_df.to_dict("records"),
        },
        current_player_id=player_token,
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
