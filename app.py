# app.py
import streamlit as st
import pandas as pd
from captain_view import captain_view
from ui_components import segmented_control

st.set_page_config(page_title="Adult Team Attendance", layout="wide")

# Load data
teams_df = pd.read_csv("Teams.csv")
players_df = pd.read_csv("Players.csv")
games_df = pd.read_csv("Games.csv")
attendance_df = pd.read_csv("Attendance.csv")

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

if is_captain:
    captain_view(players_df, games_df, attendance_df, team_id)
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
            existing = attendance_df[
                (attendance_df["player_id"] == player["token"])
                & (attendance_df["game_id"] == game["game_id"])
            ]
            if existing.empty:
                attendance_df.loc[len(attendance_df)] = [
                    player["token"],
                    game["game_id"],
                    new_status,
                    pd.Timestamp.now(),
                ]
            else:
                attendance_df.loc[
                    existing.index, ["status", "updated_at"]
                ] = [new_status, pd.Timestamp.now()]
            st.success(f"Saved changes for {game['game_id']}")
