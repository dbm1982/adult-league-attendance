# captain_view.py

import streamlit as st
import pandas as pd
from ui_components import segmented_control

def captain_view(players_df, games_df, attendance_df, team_id, save_attendance):
    st.header(f"Captain View — {team_id}")

    upcoming_games = games_df[
        (games_df["team_id"] == team_id)
        & (pd.to_datetime(games_df["date"]) >= pd.Timestamp.now())
    ].sort_values("date")

    for _, game in upcoming_games.iterrows():
        st.subheader(
            f"{game['date']} — {game['time']} — vs {game['opponent']} — {game['field']}"
        )

        team_players = players_df[players_df["team_id"] == team_id]
        game_attendance = attendance_df[attendance_df["game_id"] == game["game_id"]]

        updates = []

        for _, player in team_players.iterrows():
            current_status = (
                game_attendance.loc[
                    game_attendance["player_id"] == player["token"], "status"
                ].values[0]
                if player["token"] in game_attendance["player_id"].values
                else "NR"
            )

            new_status = segmented_control(player["token"], current_status)
            updates.append((player["token"], game["game_id"], new_status))

        if st.button(f"Save Changes for {game['game_id']}"):
            save_attendance(updates)
            st.success(f"Saved changes for {game['game_id']}")
