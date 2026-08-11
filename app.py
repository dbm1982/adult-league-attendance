import streamlit as st
import pandas as pd
import gspread

from captain_view import captain_view
from player_view import player_view
from ui_components import segmented_control

st.set_page_config(page_title="Adult Team Attendance", layout="wide")

# Authenticate using your existing secrets key
gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
sheet = gc.open_by_key("1afoSDWnUlB6ZN5Wlz4CDyX1whhzNNHxm6vCINs-2LDM")

# ---------------------------------------------------------
# SAFE SHEET → DATAFRAME LOADER
# ---------------------------------------------------------

def sheet_to_df(ws):
    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()
    header = values[0]
    rows = values[1:]
    return pd.DataFrame(rows, columns=header)

# Load worksheets
teams_ws = sheet.worksheet("Teams")
players_ws = sheet.worksheet("Players")
games_ws = sheet.worksheet("Games")
attendance_ws = sheet.worksheet("Attendance")

# Convert worksheets to DataFrames
teams_df = sheet_to_df(teams_ws)
players_df = sheet_to_df(players_ws)
games_df = sheet_to_df(games_ws)
attendance_df = sheet_to_df(attendance_ws)

# Normalize column names
teams_df.columns = teams_df.columns.str.strip().str.lower()
players_df.columns = players_df.columns.str.strip().str.lower()
games_df.columns = games_df.columns.str.strip().str.lower()
attendance_df.columns = attendance_df.columns.str.strip().str.lower()

# Cleanup whitespace
teams_df["team_id"] = teams_df["team_id"].astype(str).str.strip()
players_df["team_id"] = players_df["team_id"].astype(str).str.strip()
games_df["team_id"] = games_df["team_id"].astype(str).str.strip()
players_df["player_name"] = players_df["player_name"].astype(str).str.strip()

# Convert booleans
teams_df["active"] = teams_df["active"].astype(str).str.lower().isin(["true", "yes", "1"])
players_df["is_captain"] = players_df["is_captain"].astype(str).str.lower().isin(["true", "yes", "1"])

# Date formatting
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
# SAVE ATTENDANCE BACK TO SHEET
# ---------------------------------------------------------

def save_attendance(updates):
    global attendance_df

    for player_id, game_id, status in updates:
        existing = attendance_df[
            (attendance_df["player_id"] == player_id) &
            (attendance_df["game_id"] == game_id)
        ]

        if existing.empty:
            attendance_df.loc[len(attendance_df)] = [
                player_id,
                game_id,
                status,
                str(pd.Timestamp.now()),
            ]
        else:
            attendance_df.loc[
                existing.index, ["status", "updated_at"]
            ] = [status, str(pd.Timestamp.now())]

    attendance_ws.update(
        [attendance_df.columns.values.tolist()] +
        attendance_df.values.tolist()
    )

# ---------------------------------------------------------
# VIEW SWITCH
# ---------------------------------------------------------

if is_captain:
    mode = st.radio("Choose view:", ["Player View", "Captain View"])
else:
    mode = "Player View"

if mode == "Captain View":
    captain_view(players_df, games_df, attendance_df, team_id, save_attendance)
else:
    player_view(players_df, games_df, attendance_df, team_id, selected_player_name, save_attendance)
