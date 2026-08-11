import streamlit as st
import pandas as pd

def captain_view(players_df, games_df, attendance_df, team_id, save_attendance):

    st.title("Captain View")
    st.write("Manage attendance for upcoming games.")

    # Normalize whitespace
    players_df["team_id"] = players_df["team_id"].astype(str).str.strip()
    games_df["team_id"] = games_df["team_id"].astype(str).str.strip()

    # Filter players + games for this team
    team_players = players_df[players_df["team_id"] == team_id].copy()
    team_games = games_df[games_df["team_id"] == team_id].copy()

    # Only show upcoming games
    today = pd.Timestamp.now()
    upcoming_games = team_games[team_games["date"] >= today].sort_values("date")

    if upcoming_games.empty:
        st.info("No upcoming games found for this team.")
        return

    # Valid attendance statuses
    valid_statuses = ["Yes", "No", "Maybe", "No Response"]

    # Build attendance lookup
    attendance_lookup = {}
    for _, row in attendance_df.iterrows():
        attendance_lookup[(row["player_id"], row["game_id"])] = row["status"]

    # ---------------------------------------------------------
    # REDESIGNED CAPTAIN VIEW — COLLAPSIBLE GAME SECTIONS
    # ---------------------------------------------------------

    for _, game in upcoming_games.iterrows():

        game_id = game["game_id"]
        game_date = game["display_date"] if "display_date" in game else game["date"]
        game_time = game["display_time"] if "display_time" in game else game["time"]
        opponent = game["opponent"]

        # Collapsible section per game
        with st.expander(f"{game_id} — {game_date} — {game_time} — vs {opponent}", expanded=False):

            # Group players by attendance status
            grouped = {
                "Yes": [],
                "No": [],
                "Maybe": [],
                "No Response": []
            }

            for _, player in team_players.iterrows():
                pid = player["token"]
                raw_status = attendance_lookup.get((pid, game_id), "No Response")
                normalized = str(raw_status).strip().capitalize()
                status = normalized if normalized in valid_statuses else "No Response"
                grouped[status].append(player["player_name"])

            # Display grouped attendance with color-coded chips
            def chip_list(label, names, color):
                if len(names) == 0:
                    st.markdown(f"**{label}:** _None_")
                else:
                    chips = " ".join([f"<span style='background:{color};padding:4px 8px;border-radius:6px;color:white;margin-right:4px'>{n}</span>" for n in names])
                    st.markdown(f"**{label} ({len(names)}):**<br>{chips}", unsafe_allow_html=True)

            chip_list("Yes", grouped["Yes"], "#2ecc71")
            chip_list("No", grouped["No"], "#e74c3c")
            chip_list("Maybe", grouped["Maybe"], "#f1c40f")
            chip_list("No Response", grouped["No Response"], "#7f8c8d")

            st.markdown("---")

            # Quick-edit controls
            st.subheader("Update Attendance")

            updated_statuses = []

            for _, player in team_players.iterrows():
                pid = player["token"]
                pname = player["player_name"]

                raw_status = attendance_lookup.get((pid, game_id), "No Response")
                normalized = str(raw_status).strip().capitalize()
                current_status = normalized if normalized in valid_statuses else "No Response"

                new_status = st.radio(
                    pname,
                    valid_statuses,
                    index=valid_statuses.index(current_status),
                    horizontal=True,
                    key=f"radio_{pid}_{game_id}"
                )

                updated_statuses.append((pid, game_id, new_status))

            # Save button for entire game
            if st.button(f"Save All Changes for {game_id}", key=f"saveall_{game_id}"):
                save_attendance(updated_statuses)
                st.success(f"Saved all attendance updates for {game_id}")
