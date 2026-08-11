# app.py

import streamlit as st
import pandas as pd
import gspread
from captain_view import captain_view
from ui_components import segmented_control

st.set_page_config(page_title="Adult Team Attendance", layout="wide")

# Authenticate using your existing secrets key
gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
sheet = gc.open("Adult Team Attendance Dev")

# Load worksheets
teams_ws = sheet.worksheet("Teams")
players_ws = sheet.worksheet("Players")
games_ws = sheet.worksheet("Games")
attendance_ws = sheet.worksheet("Attendance")

# Convert worksheets to DataFrames
teams_df = pd.DataFrame(teams_ws.get_all_records())
players_df = pd.DataFrame(players_ws.get_all_records())
games_df = pd.DataFrame(games_ws.get_all_records())
attendance_df = pd.DataFrame(attendance_ws.get_all_records())


st.write("Teams loaded:", len(teams_df))
st.write("Players loaded:", len(players_df))
st.write("Games loaded:", len(games_df))
st.write("Attendance loaded:", len(attendance_df))

# Convert active column to real boolean
teams_df["active"] = teams_df["active"].astype(str).str.strip().str.upper() == "TRUE"


# ---------------------------------------------------------
# CLEANUP: strip whitespace + remove blank team_id rows
# ---------------------------------------------------------

# Strip whitespace from team_id and player_name
teams_df["team_id"] = teams_df["team_id"].astype(str).str.strip()
players_df["team_id"] = players_df["team_id"].astype(str).str.strip()
games_df["team_id"] = games_df["team_id"].astype(str).str.strip()
players_df["player_name"] = players_df["player_name"].astype(str).str.strip()

# Remove rows with blank team_id
teams_df = teams_df[teams_df["team_id"] != ""]
players_df = players_df[players_df["team_id"] != ""]
games_df = games_df[games_df["team_id"] != ""]


# Convert active column to real boolean
teams_df["active"] = teams_df["active"].astype(str).str.strip().str.upper() == "TRUE"

# Convert captain column to real boolean
players_df["is_captain"] = (
    players_df["is_captain"].astype(str).str.strip().str.upper() == "TRUE"
)



# ---------------------------------------------------------
# LOGIN FLOW: TEAM → PLAYER
# ---------------------------------------------------------

st.title("Adult League Attendance")

# Team dropdown (only active teams)
active_teams = teams_df[teams_df["active"] == True]["team_id"].tolist()
selected_team = st.selectbox("Select your team:", active_teams)

# Player dropdown (filtered by team)
team_players = players_df[players_df["team_id"] == selected_team].copy()

player_names = team_players["player_name"].tolist()
selected_player_name = st.selectbox("Select your name:", player_names)

# Identify player row safely
player_row = team_players[team_players["player_name"] == selected_player_name]

if player_row.empty:
    st.error("Player not found. Check your Players sheet for exact spelling or trailing spaces.")
    st.stop()

player = player_row.iloc[0]
player_token = player["token"]
team_id = player["team_id"]
is_captain = player["is_captain"]

st.success(f"Logged in as {player['player_name']} ({team_id})")

# ---------------------------------------------------------
# SAVE ATTENDANCE BACK TO SHEET
# ---------------------------------------------------------

def save_attendance(updates):
    global attendance_df

    for player_id, game_id, status in updates:
        existing = attendance_df[
            (attendance_df["player_id"] == player_id)
            & (attendance_df["game_id"] == game_id)
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

    # Write back to Google Sheets
    attendance_ws.update(
        [attendance_df.columns.values.tolist()] +
        attendance_df.values.tolist()
    )

# ---------------------------------------------------------
# CAPTAIN VIEW
# ---------------------------------------------------------

if is_captain:
    st.header("Captain View")
    captain_view(players_df, games_df, attendance_df, team_id, save_attendance)

# ---------------------------------------------------------
# PLAYER VIEW
# ---------------------------------------------------------

else:
    st.header("Player View")

    upcoming_games = games_df[
        (games_df["team_id"] == team_id)
        & (pd.to_datetime(games_df["date"]) >= pd.Timestamp.now())
    ].sort_values("date")

    for _, game in upcoming_games.iterrows():
        st.subheader(
            f"{game['date']} — {game['time']} — vs {game['opponent']} — {game['field']}"
        )

        # Get current status
        current_status = attendance_df.loc[
            (attendance_df["player_id"] == player_token)
            & (attendance_df["game_id"] == game["game_id"]),
            "status",
        ].values

        current_status = current_status[0] if len(current_status) > 0 else "NR"

        # Segmented control UI
        new_status = segmented_control(player_token, current_status)

        # Save button
        if st.button(f"Save Changes for {game['game_id']}"):
            save_attendance([(player_token, game["game_id"], new_status)])
            st.success(f"Saved changes for {game['game_id']}")
