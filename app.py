# app.py

import streamlit as st
import pandas as pd
import gspread
from captain_view import captain_view
from ui_components import segmented_control

st.set_page_config(page_title="Adult Team Attendance", layout="wide")

# Authenticate using your existing secrets key
gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
sheet = gc.open("Adult Team Attendance")

# Load worksheets
teams_ws = sheet.worksheet("Teams")
players_ws = sheet.worksheet("Players")
games_ws = sheet.worksheet("Games")
attendance_ws = sheet.worksheet("Attendance")

# Convert worksheets to DataFrames
def sheet_to_df(ws):
    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()
    header = values[0]
    rows = values[1:]
    return pd.DataFrame(rows, columns=header)

teams_df = sheet_to_df(teams_ws)
players_df = sheet_to_df(players_ws)
games_df = sheet_to_df(games_ws)
attendance_df = sheet_to_df(attendance_ws)

# Normalize column names to avoid KeyErrors
teams_df.columns = teams_df.columns.str.strip().str.lower()
players_df.columns = players_df.columns.str.strip().str.lower()
games_df.columns = games_df.columns.str.strip().str.lower()
attendance_df.columns = attendance_df.columns.str.strip().str.lower()


# ---------------------------------------------------------
# CLEANUP: strip whitespace + remove blank team_id rows
# ---------------------------------------------------------

teams_df["team_id"] = teams_df["team_id"].astype(str).str.strip()
players_df["team_id"] = players_df["team_id"].astype(str).str.strip()
games_df["team_id"] = games_df["team_id"].astype(str).str.strip()
players_df["player_name"] = players_df["player_name"].astype(str).str.strip()

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
# DATE + TIME FORMATTING
# ---------------------------------------------------------

# Convert date column to datetime
games_df["date"] = pd.to_datetime(games_df["date"], errors="coerce")

# Format date for display
games_df["display_date"] = games_df["date"].dt.strftime("%A, %b %d")

# Format time for display
games_df["display_time"] = pd.to_datetime(
    games_df["time"], format="%I:%M %p", errors="coerce"
).dt.strftime("%-I:%M %p")

# ---------------------------------------------------------
# LOGIN FLOW: TEAM → PLAYER
# ---------------------------------------------------------

st.title("Attendances")

active_teams = teams_df[teams_df["active"] == True]["team_id"].tolist()
selected_team = st.selectbox("Select your team:", active_teams)

team_players = players_df[players_df["team_id"] == selected_team].copy()
player_names = team_players["player_name"].tolist()
selected_player_name = st.selectbox("Select your name:", player_names)

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

    # Season summary
    st.subheader("Season Summary")

    player_att = attendance_df[attendance_df["player_id"] == player_token]
    summary = player_att["status"].value_counts().to_dict()

    for status in ["Yes", "No", "Maybe", "None"]:
        st.write(f"{status}: {summary.get(status, 0)} games")

    # Upcoming games
    upcoming_games = games_df[
        (games_df["team_id"] == team_id) &
        (games_df["date"] >= pd.Timestamp.now())
    ].sort_values("date")

    for _, game in upcoming_games.iterrows():

        st.markdown(f"""
        ### {game['display_date']} — {game['display_time']}
        **vs {game['opponent']}**  
        *{game['field']}*
        """)

        current_status = attendance_df.loc[
            (attendance_df["player_id"] == player_token) &
            (attendance_df["game_id"] == game["game_id"]),
            "status"
        ].values

        current_status = current_status[0] if len(current_status) > 0 else "None"

        new_status = segmented_control(player_token, current_status, game["game_id"])

        if st.button(f"Save Changes for {game['game_id']}", key=f"save_{player_token}_{game['game_id']}"):
            save_attendance([(player_token, game["game_id"], new_status)])
            st.success(f"Saved changes for {game['game_id']}")
