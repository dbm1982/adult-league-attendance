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

# Cache sheets in session_state
if "players_df" not in st.session_state:
    st.session_state.players_df = load_players_df()

if "games_df" not in st.session_state:
    st.session_state.games_df = load_games_df()

if "attendance_df" not in st.session_state:
    st.session_state.attendance_df = load_attendance_df()

if "teams_df" not in st.session_state:
    st.session_state.teams_df = load_teams_df()

if "pending_updates" not in st.session_state:
    st.session_state.pending_updates = {}

# Persistent selection
if "selected_team" not in st.session_state:
    st.session_state.selected_team = None

if "selected_player" not in st.session_state:
    st.session_state.selected_player = None

players_df = st.session_state.players_df
games_df = st.session_state.games_df
attendance_df = st.session_state.attendance_df
teams_df = st.session_state.teams_df

st.title("Adult League Attendance")

active_team_ids = sorted(
    teams_df[teams_df["active"] == True]["team_id"].unique()
)

# Reset callback
def reset_selection():
    st.session_state.selected_team = None
    st.session_state.selected_player = None
    st.experimental_rerun()

# Show selectors only when nothing is selected
if st.session_state.selected_team is None and st.session_state.selected_player is None:

    selector_container = st.container()

    with selector_container:

        team_id = st.selectbox(
            "Team",
            active_team_ids,
            index=None,
            placeholder="Select a team"
        )

        if team_id:
            st.session_state.selected_team = team_id

            team_players = players_df[
                (players_df["team_id"] == team_id)
                & (players_df["team_id"].ne(""))
                & (~players_df["team_id"].str.contains("Inactive", case=False))
                & (~players_df["team_id"].str.contains("Floaters", case=False))
            ]

            player_names = team_players["player_name"].tolist()

            player_name = st.selectbox(
                "Player",
                player_names,
                index=None,
                placeholder="Select a player"
            )

            if player_name:
                st.session_state.selected_player = player_name
                selector_container.empty()
                st.experimental_rerun()

# Compact badge after selection
if st.session_state.selected_team and st.session_state.selected_player:

    badge_col1, badge_col2 = st.columns([0.85, 0.15])

    with badge_col1:
        st.markdown(
            f"""
            <div style="
                background-color:#eef2f7;
                padding:10px 14px;
                border-radius:8px;
                margin-bottom:15px;
                font-size:15px;
                font-weight:600;
            ">
                Selected:
                <span style="color:#2c3e50;">Team {st.session_state.selected_team}</span> •
                <span style="color:#2c3e50;">{st.session_state.selected_player}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with badge_col2:
        st.button("Change", on_click=reset_selection)

# Stop if still missing selection
if st.session_state.selected_team is None or st.session_state.selected_player is None:
    st.stop()

# Load player row
team_id = st.session_state.selected_team
player_name = st.session_state.selected_player

team_players = players_df[
    (players_df["team_id"] == team_id)
    & (players_df["team_id"].ne(""))
    & (~players_df["team_id"].str.contains("Inactive", case=False))
    & (~players_df["team_id"].str.contains("Floaters", case=False))
]

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

# Render views
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
