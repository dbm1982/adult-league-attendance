import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

eastern = ZoneInfo("America/New_York")


def captain_view(data, current_player_id, team_id):
    st.markdown("### Captain View")

    players = data["players"]
    games = data["games"]
    attendance = data["attendance"]

    # Normalize team_id
    team_id_normalized = team_id.strip().lower()
    games["team_id_normalized"] = (
        games["team_id"].astype(str).str.strip().str.lower()
    )

    team_games = games[
        games["team_id_normalized"] == team_id_normalized
    ].copy()

    today_local = datetime.now(eastern).date()

    if "date" in team_games.columns:
        team_games["date"] = team_games["date"].apply(
            lambda d: d.date() if hasattr(d, "date") else None
        )

    upcoming_games = team_games[
        team_games["date"] >= today_local
    ].sort_values("date")

    st.markdown("#### Players Missing Responses")

    attendance_lookup = {
        (a["player_id"], a["game_id"]): a["status"]
        for a in attendance
    }

    missing = []

    for p in players:
        pid = p["player_id"]

        if pid == current_player_id:
            continue

        for _, g in upcoming_games.iterrows():
            key = (pid, g["game_id"])
            if key not in attendance_lookup:
                missing.append((p["player_name"], g["date"], g["time"]))

    unique_missing = sorted(set(missing))

    if unique_missing:
        for name, date, time in unique_missing:
            st.markdown(
                f"<span style='color:#d9534f; font-weight:bold;'>⚠ {name}</span> "
                f"<span style='color:#555;'>— {date} {time}</span>",
                unsafe_allow_html=True,
            )
    else:
        st.success("All players have responded!")

    st.markdown("---")
    st.markdown("#### Team Attendance Summary")

    if upcoming_games.empty:
        st.info("No upcoming games found for this team.")
        return

    for _, g in upcoming_games.iterrows():
        game_id = g["game_id"]

        yes = sum(
            1 for a in attendance
            if a["game_id"] == game_id and a["status"] == "Yes"
        )
        no = sum(
            1 for a in attendance
            if a["game_id"] == game_id and a["status"] == "No"
        )
        maybe = sum(
            1 for a in attendance
            if a["game_id"] == game_id and a["status"] == "Maybe"
        )

        st.markdown(
            f"""
            <div style='padding:6px 10px; border-radius:6px; background:#f7f7f7; margin-bottom:4px;'>
              <strong>{g['date']} — {g['time']}</strong><br>
              <span style='color:#5cb85c;'>Yes: {yes}</span> &nbsp;|&nbsp;
              <span style='color:#d9534f;'>No: {no}</span> &nbsp;|&nbsp;
              <span style='color:#f0ad4e;'>Maybe: {maybe}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
