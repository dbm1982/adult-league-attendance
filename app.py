import streamlit as st
import pandas as pd
import gspread

from captain_view import captain_view
from player_view import player_view

st.set_page_config(page_title="Adult Team Attendance", layout="wide")

# ---------------------------------------------------------
# LOAD SHEETS ONCE
# ---------------------------------------------------------

gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
sheet = gc.open_by_key("1afoSDWnUlB6ZN5Wlz4CDyX1whhzNNHxm6vCINs-2LDM")

def sheet_to_df(ws):
    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()
    header = values[0]
    rows = values[1:]
    return pd.DataFrame(rows, columns=header)

teams_df = sheet_to_df(sheet.worksheet("Teams"))
players_df = sheet_to_df(sheet.worksheet("Players"))
games_df = sheet_to_df(sheet.worksheet("Games"))
attendance_ws = sheet.worksheet("Attendance")

# ---------------------------------------------------------
# INITIALIZE SESSION STATE
# ---------------------------------------------------------

if "attendance_df" not in st.session_state:
    st.session_state.attendance_df = sheet_to_df(attendance_ws)

attendance_df = st.session_state.attendance_df

# ---------------------------------------------------------
# CLEANUP
# ---------------------------------------------------------

teams_df.columns = teams_df.columns.str.strip().str.lower()
players_df.columns = players_df.columns.str.strip().str.lower()
games_df.columns = games_df.columns.str.strip().str.lower()
attendance_df.columns = attendance_df.columns.str.strip().str.lower()

teams_df["team_id"] = teams_df["team_id"].astype(str).str.strip()
players_df["team_id"] = players_df["team_id"].astype(str).str.strip()
games_df["team_id"] = games_df["team_id"].astype(str).str.strip()

players_df["player_name"] = players_df["player_name"].astype(str).str.strip()

teams_df["active"] = teams_df["active"].astype(str).str.lower().isin(["true", "yes", "1"])
players_df["is_captain"] = players_df["is_captain"].astype(str).str.lower().isin(["true", "yes", "1"])

games_df["date"] = pd.to_datetime(games_df["date"], errors="coerce")
games_df["display_date"] = games_df["date"].dt.strftime("%A, %b %d")
games_df["display_time"] = pd.to_datetime(
    games_df["time"], format="%I:%M %p", errors="coerce"
).dt.strftime("%-I:%M %p")

# ---------------------------------------------------------
# LOGIN FLOW
# ---------------------------------------------------------

st.title("Adult Soccer Attendance Portal at Union Point")

active_teams = teams_df[teams_df["active"] == True]["team_id"].tolist()
team_options = ["-- Select Team --"] + active_teams

selected_team = st.selectbox("Select your team:", team_options)
if selected_team == "-- Select Team --":
    st.stop()

team_players = players_df[players_df["team_id"] == selected_team].copy()
player_options = ["-- Select Player --"] + team_players["player_name"].tolist()

selected_player_name = st.selectbox("Select your name:", player_options)
if selected_player_name == "-- Select Player --":
    st.stop()

player_row = team_players[team_players["player_name"] == selected_player_name].iloc[0]
player_token = player_row["token"]
team_id = player_row["team_id"]
is_captain = player_row["is_captain"]

st.success(f"Logged in as {selected_player_name} ({team_id})")

# ---------------------------------------------------------
# COMMIT FUNCTION (BUFFERED WRITE)
# ---------------------------------------------------------

def commit_attendance_changes():
    attendance_ws.update(
        [attendance_df.columns.values.tolist()] +
        attendance_df.values.tolist()
    )
    st.success("All attendance changes have been saved.")

# ---------------------------------------------------------
# VIEW SWITCH — True iOS-style segmented tabs (HTML + JS)
# ---------------------------------------------------------

if is_captain:

    # Initialize view mode if not set
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "Player View"

    # CSS for real folder-style segmented tabs
    st.markdown("""
        <style>
            .segmented-control {
                display: flex;
                justify-content: center;
                margin-top: 10px;
                margin-bottom: 0px;
            }

            .segmented-tab {
                padding: 10px 26px;
                font-size: 18px;
                font-weight: 500;
                border: 1px solid #ccc;
                border-radius: 14px 14px 0 0;
                background-color: #e6e6e6;
                color: #555;
                margin-right: 6px;
                cursor: pointer;
                transition: all 0.15s ease-in-out;
                user-select: none;
            }

            .segmented-tab-active {
                background-color: #ffffff;
                color: #000;
                border-bottom: 1px solid #ffffff;
                font-weight: 700;
                box-shadow: 0px -2px 6px rgba(0,0,0,0.08);
            }

            .segmented-tab:hover {
                background-color: #f2f2f2;
            }
        </style>
    """, unsafe_allow_html=True)

    # Render the tab bar using HTML
    st.markdown(
        f"""
        <div class="segmented-control">
            <div class="segmented-tab {'segmented-tab-active' if st.session_state.view_mode=='Player View' else ''}"
                 onclick="window.location.href='?view=player'">
                 Player View
            </div>

            <div class="segmented-tab {'segmented-tab-active' if st.session_state.view_mode=='Captain View' else ''}"
                 onclick="window.location.href='?view=captain'">
                 Captain View
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Handle tab clicks via query params
    params = st.query_params
    if "view" in params:
        if params["view"] == "player":
            st.session_state.view_mode = "Player View"
        elif params["view"] == "captain":
            st.session_state.view_mode = "Captain View"

    mode = st.session_state.view_mode

else:
    mode = "Player View"

# Render selected view
if mode == "Captain View":
    captain_view(players_df, games_df, attendance_df, team_id, commit_attendance_changes)
else:
    player_view(players_df, games_df, attendance_df, team_id, selected_player_name, commit_attendance_changes)
