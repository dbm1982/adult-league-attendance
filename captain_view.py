import streamlit as st
import pandas as pd

def captain_view(players_df, games_df, attendance_df, team_id, save_attendance):

    st.subheader("Team Attendance Overview")

    # Clean whitespace
    players_df["team_id"] = players_df["team_id"].astype(str).str.strip()
    games_df["team_id"] = games_df["team_id"].astype(str).str.strip()

    # Filter players for this team
    team_players = players_df[players_df["team_id"] == team_id].copy()

    # Filter games for this team
    team_games = games_df[games_df["team_id"] == team_id].copy()

    if team_players.empty:
        st.error("No players found for this team.")
        return

    if team_games.empty:
        st.error("No games found for this team.")
        return

    # Display table of attendance
    merged = attendance_df.merge(
        team_players,
        left_on="player_id",
        right_on="token",
        how="right"
    )

    merged = merged.merge(
        team_games,
        on="game_id",
        how="right"
    )

    st.dataframe(merged[[
        "player_name",
        "game_id",
        "date",
        "time",
        "opponent",
        "status"
    ]])

    st.subheader("Update Attendance")

    valid_statuses = ["Yes", "No", "Maybe", "No Response"]

    for _, game in team_games.iterrows():
        st.write(f"**{game['game_id']} — {game['date']} — {game['time']} — vs {game['opponent']}**")

        for _, player in team_players.iterrows():

            # Get current status
            current_status = attendance_df.loc[
                (attendance_df["player_id"] == player["token"]) &
                (attendance_df["game_id"] == game["game_id"]),
                "status"
            ].values

            current_status = current_status[0] if len(current_status) > 0 else "No Response"

            # Normalize status
            raw_status = str(current_status).strip().capitalize()
            current_status = raw_status if raw_status in valid_statuses else "No Response"

            # Selectbox
            new_status = st.selectbox(
                player["player_name"],
                valid_statuses,
                index=valid_statuses.index(current_status)
            )

            # Save button
            if st.button(f"Save {player['player_name']} for {game['game_id']}"):
                save_attendance([(player["token"], game["game_id"], new_status)])
                st.success(f"Saved {player['player_name']} for {game['game_id']}")
