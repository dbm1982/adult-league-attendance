import streamlit as st
import pandas as pd

def captain_view(players_df, games_df, attendance_df, team_id, save_attendance):

    st.title("Captain View")
    st.write("Manage attendance for upcoming games.")

    players_df["team_id"] = players_df["team_id"].astype(str).str.strip()
    games_df["team_id"] = games_df["team_id"].astype(str).str.strip()

    team_players = players_df[players_df["team_id"] == team_id].copy()
    team_games = games_df[games_df["team_id"] == team_id].copy()

    today = pd.Timestamp.now()
    upcoming_games = team_games[team_games["date"] >= today].sort_values("date")

    if upcoming_games.empty:
        st.info("No upcoming games found for this team.")
        return

    valid_statuses = ["Yes", "No", "Maybe", "No Response"]

    attendance_lookup = {
        (row["player_id"], row["game_id"]): row["status"]
        for _, row in attendance_df.iterrows()
    }

    for _, game in upcoming_games.iterrows():

        game_id = game["game_id"]
        game_date = game["display_date"]
        game_time = game["display_time"]
        opponent = game["opponent"]

        grouped = {s: [] for s in valid_statuses}

        for _, player in team_players.iterrows():
            pid = player["token"]
            raw = attendance_lookup.get((pid, game_id), "No Response")
            status = str(raw).strip().capitalize()
            status = status if status in valid_statuses else "No Response"
            grouped[status].append(player["player_name"])

        yes_count = len(grouped["Yes"])
        unconfirmed_count = len(grouped["Maybe"]) + len(grouped["No Response"])

        title = (
            f"{game_date} — {game_time} — vs {opponent} "
            f"({yes_count} playing • {unconfirmed_count} unconfirmed)"
        )

        with st.expander(title, expanded=False):

            def chips(label, names, color):
                if not names:
                    st.markdown(f"**{label}:** _None_")
                    return
                html = " ".join(
                    f"<span style='background:{color};padding:4px 8px;"
                    f"border-radius:6px;color:white;margin-right:4px'>{n}</span>"
                    for n in names
                )
                st.markdown(f"**{label} ({len(names)}):**<br>{html}", unsafe_allow_html=True)

            chips("Yes", grouped["Yes"], "#2ecc71")
            chips("No", grouped["No"], "#e74c3c")
            chips("Maybe", grouped["Maybe"], "#f1c40f")
            chips("No Response", grouped["No Response"], "#7f8c8d")

            st.markdown("---")

            st.subheader("Update Attendance")

            updated = []

            for _, player in team_players.iterrows():
                pid = player["token"]
                pname = player["player_name"]

                raw = attendance_lookup.get((pid, game_id), "No Response")
                status = str(raw).strip().capitalize()
                status = status if status in valid_statuses else "No Response"

                new_status = st.radio(
                    pname,
                    valid_statuses,
                    index=valid_statuses.index(status),
                    horizontal=True,
                    key=f"radio_{pid}_{game_id}"
                )

                updated.append((pid, game_id, new_status))

            if st.button(f"Save All Changes for {game_date}", key=f"save_{game_id}"):
                save_attendance(updated)
                st.success(f"Saved all attendance updates for {game_date}")
