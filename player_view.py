import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

eastern = ZoneInfo("America/New_York")


def player_view(players_df, games_df, attendance_df, player_id, commit_changes):
    st.markdown("### Player View")

    player_row = players_df[players_df["player_id"] == player_id]
    if player_row.empty:
        st.error("Player not found.")
        return

    player_name = player_row.iloc[0]["player_name"]
    team_id = player_row.iloc[0]["team_id"]

    st.markdown(f"#### {player_name} — {team_id}")

    games_df["team_id_norm"] = games_df["team_id"].astype(str).str.strip().str.lower()
    team_id_norm = team_id.strip().lower()

    team_games = games_df[games_df["team_id_norm"] == team_id_norm].copy()

    if "date" in team_games.columns:
        team_games["date"] = team_games["date"].apply(
            lambda d: d.date() if hasattr(d, "date") else None
        )

    today_local = datetime.now(eastern).date()
    upcoming_games = team_games[team_games["date"] >= today_local].sort_values("date")

    attendance_lookup = {
        (row["player_id"], row["game_id"]): row["status"]
        for _, row in attendance_df.iterrows()
    }

    for _, g in upcoming_games.iterrows():
        game_id = g["game_id"]
        date = g["date"]
        time = g["time"]
        opponent = g["opponent"]

        st.markdown(f"**{date} — {time} vs {opponent}**")

        current_status = attendance_lookup.get((player_id, game_id), "No Response")
        options = ["Yes", "No", "Maybe", "No Response"]

        new_status = st.radio(
            f"Your status for {date} {time}",
            options,
            index=options.index(current_status) if current_status in options else options.index("No Response"),
            key=f"{player_id}_{game_id}",
        )

        mask = (attendance_df["player_id"] == player_id) & (attendance_df["game_id"] == game_id)
        if mask.any():
            attendance_df.loc[mask, "status"] = new_status
            attendance_df.loc[mask, "updated_at"] = datetime.now(eastern).isoformat()
        else:
            attendance_df.loc[len(attendance_df)] = {
                "player_id": player_id,
                "game_id": game_id,
                "status": new_status,
                "updated_at": datetime.now(eastern).isoformat(),
            }

    if st.button("Save My Responses"):
        commit_changes(attendance_df)
        st.success("Your attendance has been saved!")
