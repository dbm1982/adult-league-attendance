# app.py

import streamlit as st
import pandas as pd
import gspread
from captain_view import captain_view
from ui_components import segmented_control

st.set_page_config(page_title="Adult Team Attendance", layout="wide")

# Authenticate using Streamlit Secrets
gc = gspread.service_account_from_dict(st.secrets["google_service_account"])
sheet = gc.open("Adult Team Attendance Dev")

# Load tabs
teams_ws = sheet.worksheet("Teams")
players_ws = sheet.worksheet("Players")
games_ws = sheet.worksheet("Games")
attendance_ws = sheet.worksheet("Attendance")

teams_df = pd.DataFrame(teams_ws.get_all_records())
players_df = pd.DataFrame(players_ws.get_all_records())
games_df = pd.DataFrame(games_ws.get_all_records())
attendance_df = pd.DataFrame(attendance_ws.get_all_records())

# Save attendance back to Google Sheets
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

# Identify user
user_token = st.text_input("Enter your token:")
player_row = players_df[players_df["token"] == user_token]

if player_row.empty:
    st.warning("Invalid token.")
    st.stop()

player = player_row.iloc[0]
team_id = player["team_id"]
is_captain = player["is_captain"]

st.title(f"Hello {player['player_name']} 👋")

# Captain View
if is_captain:
    captain_view(players_df, games_df, attendance_df, team_id, save_attendance)

# Player View
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

        current_status = attendance_df.loc[
            (attendance_df["player_id"] == player["token"])
            & (attendance_df["game_id"] == game["game_id"]),
            "status",
        ].values

        current_status = current_status[0] if len(current_status) > 0 else "NR"

        new_status = segmented_control(player["token"], current_status)

        if st.button(f"Save Changes for {game['game_id']}"):
            save_attendance([(player["token"], game["game_id"], new_status)])
            st.success(f"Saved changes for {game['game_id']}")
